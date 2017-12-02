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
    print login_session
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
    print "stored access code: %s" % stored_access_token

    stored_gplus_id = login_session.get('gplus_id')
    print "stored gplus: %s" % stored_gplus_id

    print "credentials access code %s" % credentials.access_token

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
    print login_session['gplus_id']
    # get user info from google api.
    userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    result = requests.get(userinfo_url, params=params)
    data = result.json()
    print data

    login_session['provider'] = 'google'
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # Check whether the user is in the database.
    # If not then add the users.
    try:
    	user = session.query(User).filter_by(email=login_session['email']).one()
    	login_session['user_id'] = user.id
    except:
    	user = None

    if user is None:
    	print "reached in None"
    	session.add(User(username=login_session['username'], picture=login_session['picture'], email=login_session['email']))
    	session.commit()
    	newUser = session.query(User).filter_by(email=login_session['email']).one()
    	print newUser.username
    	print newUser.id
    	login_session['user_id'] = newUser.id

    print login_session['provider']
    print login_session['username']
    print login_session['picture']
    print login_session['email']
    print login_session['user_id']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])

    return output

# google disconnect
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    print "reached in gdis"

    access_token = login_session.get('access_token')
    print access_token
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        print "reaching before response"
        print response
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        print response
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

@app.route('/disconnect')
def disconnect():
	print 'reached in disconnect'
	if 'provider' in login_session:
		if login_session['provider'] == 'google':
			gdisconnect()
			print login_session['gplus_id']
			del login_session['gplus_id']
			print login_session['access_token']
			del login_session['access_token']
			print "deleted"
		del login_session['username']
		del login_session['email']
		del login_session['picture']
		#del login_session['user_id']
		del login_session['provider']
		flash("You have successfully been logged out.")
		return redirect(url_for('homePage'))
	else:
		flash('You were not logged in')
		print 'you are not logged in'
		return redirect(url_for('homePage'))

@app.route('/')
@app.route('/catalog/')
def homePage():
    bands = session.query(Music_Band).all()
    albums = session.query(Album).all()
    return render_template('album.html', music_bands = bands, albums = albums)

@app.route('/catalog/<string:music_band_name>/albums/')
def showBandAlbums(music_band_name):

	music_bands = session.query(Music_Band).all()
	print music_band_name
	print music_bands[1].name
	try:
		current_music_band = session.query(Music_Band).filter_by(name=music_band_name).one()
		print current_music_band.id
		print current_music_band.name
	except:
		return "Could not get the band"

	# get the albums for the band.
	try:
		albums = session.query(Album).filter_by(music_band_id=current_music_band.id).all()
		number_of_albums = session.query(Album).filter_by(music_band_id=current_music_band.id).count()
		print albums[0].name
	except:
		return "could not get the albums"

	return render_template('showAlbum.html', currentBand=current_music_band, albums=albums, music_bands=music_bands, number_of_albums=number_of_albums)

@app.route('/catalog/<int:albumId>editAlbum/')
def editAlbum(albumId):

	# check if the user is logged in.
	# if not then redirect to the login page
	if 'username' not in login_session:
		return redirect(url_for('showLogin'))

	try:
		toEditAlbum = session.query(Album).filter_by(id=albumId).one()
		bands = session.query(Music_Band).all()
	except:
		return "Could not get the album to edit"

	if request.method == 'POST':
		if request.args.get('name'):
			toEditAlbum.name = request.args.get('name')
		if request.args.get('description'):
			toEditAlbum.name = request.args.get('description')
		if request.args.get('music_band_id'):
			toEditAlbum.name = request.args.get('music_band_id')
		session.add(toEditAlbum)
		session.commit()
		flash('The album' + toEditAlbum.name + 'was successfully edited')

		return url_for('homePage')
	else:
		return render_template('editAlbum.html', album=toEditAlbum, bands=bands)

if __name__ == '__main__':
    app.secret_key  = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
