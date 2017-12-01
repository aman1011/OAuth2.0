from flask import Flask, render_template, request, redirect, jsonify, url_for, flash, make_response
from models import Base, Music_Band, Album, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from httplib2 import Http
app = Flask(__name__)

# login session.
from flask import session as login_session
import random, string

# imports for the google auth
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID_GOOGLE = json.loads(open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Music Album Catalog App"

# connect to database
engine = create_engine('sqlite:///musicbandswithalbums.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    print state
    login_session['state'] = state

    return render_template('login.html', STATE=state)
# gconnect module
@app.route('/gconnect', methods = ['POST'])
def gconnect():
    print "reached here"
    # validating the state token.
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    
    # obtain the authorization code.
    code = request.data

    try:

        # upgrading the code to a credential object
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri='postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'

        return response

    # check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # abort, if error in this step.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response
    
    # Verify that the token is for the same user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("Token"'s used id does not match the given user ID'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that its for the appropriate application.
    if result['issued_to'] != CLIENT_ID_GOOGLE:
        response = make_repsonse(json.dumps('The clinet ID does not match with the token'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')

    # Now if there is no user present, the above values will be 
    # empty meaning no user is logged in. In case, these values
    # are present beforehand, means there is a user logged in.
    # If the values are not none and the trying user's gplus_id
    # matches the login_session's g plus id, then it means the 
    # same user is currently logged in.
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('User currently logged in'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # get user info from google api.
    userinfo_url = 'https://www/googleapis.com/oauth2/v1/userinfo',
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    result = requests.get(userinfo_url, params=params)
    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    return render_template('homePage')


@app.route('/')
def homePage():
    print CLIENT_ID_GOOGLE
    bands = session.query(Music_Band).all()
    return render_template('main.html', music_bands = bands)


if __name__ == '__main__':
    app.secret_key  = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
