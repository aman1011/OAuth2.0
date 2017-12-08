from flask import Flask, render_template, request, redirect
from flask import jsonify, url_for, flash, make_response, g
from models import Base, Music_Band, Album, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from httplib2 import Http
from redis import Redis
import time
from functools import update_wrapper
from flask_httpauth import HTTPBasicAuth

# login session.
from flask import session as login_session
import random
import string

# imports for the google auth
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)
auth = HTTPBasicAuth()

CLIENT_ID_GOOGLE = json.loads(open(
	'client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Music Album Catalog App"

# connect to database
engine = create_engine('sqlite:///musicbandswithalbums.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Redis code for limiting API call.
redis = Redis()


# create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(
        string.ascii_uppercase + string.digits) for x in xrange(32))
    print state
    login_session['state'] = state

    return render_template('login.html', STATE=state)


# gconnect module
@app.route('/gconnect', methods=['POST'])
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
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps(
            'Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'

        return response

    # check that the access token is valid.
    access_token = credentials.access_token
    url = 'https://www.googleapis.com/oauth2/v1/tokeninfo?'
    url += 'access_token=%s' % access_token
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
        response = make_response(json.dumps(
            "Token"'s used id does not match the given user ID'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that its for the appropriate application.
    if result['issued_to'] != CLIENT_ID_GOOGLE:
        response = make_response(json.dumps(
            'The clinet ID does not match with the token'), 401)
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
        response = make_response(json.dumps(
            'User currently logged in'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # get user info from google api.
    userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    result = requests.get(userinfo_url,
                          params=params)
    data = result.json()

    login_session['provider'] = 'google'
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # Check whether the user is in the database.
    # If not then add the users.
    try:
        user = session.query(User).filter_by(
            email=login_session['email']).one()
        login_session['user_id'] = user.id
    except:
        user = None

    if user is None:
        session.add(User(
            username=login_session['username'],
            picture=login_session['picture'],
            email=login_session['email']))
        session.commit()
        newUser = session.query(User).filter_by(
            email=login_session['email']).one()
        login_session['user_id'] = newUser.id

    flash("You have successfully logged in")
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;'
    output += '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    return output


# google disconnect
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.

    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps(
            'Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'

        return response
    else:
        response = make_response(json.dumps(
            'Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# FB Connect and Disconnect
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?'
    url += 'grant_type=fb_exchange_token&'
    url += 'client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.11/me"
    '''
        Due to the formatting for the result from the server
        token exchange we have to split the token first on
        commas and select the first index which gives us the
        key : value for the server access token then we split
        it on colons to pull out the actual token value
        and replace the remaining quotes with nothing
        so that it can be used directly in the graph api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v2.11/me?'
    url += 'access_token=%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture?'
    url += 'access_token=%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user = session.query(User).filter_by(
        email=login_session['email']).one()
    if not user:
        session.add(User(
            username=login_session['username'],
            picture=login_session['picture'],
            email=login_session['email']))
        session.commit()
        newUser = session.query(User).filter_by(
            email=login_session['email']).one()
        login_session['user_id'] = newUser.id

    login_session['user_id'] = user.id
    flash("You have successfully logged in")
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;'
    output += 'border-radius: 150px;'
    output += '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']

    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (
        facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']

        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['access_token']
            del login_session['facebook_id']

        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('homePage'))
    else:
        flash('You were not logged in')
        return redirect(url_for('homePage'))


@app.route('/')
@app.route('/catalog/')
def homePage():
    bands = session.query(Music_Band).all()
    albums = session.query(Album).all()
    return render_template('album.html',
                           music_bands=bands,
                           albums=albums)


# Route for showing all the albums by a band.
@app.route('/catalog/<string:music_band_name>/albums/')
def showBandAlbums(music_band_name):

    music_bands = session.query(Music_Band).all()
    try:
        current_music_band = session.query(Music_Band).filter_by(
            name=music_band_name).one()
    except:
        return "Could not get the band"

    # get the albums for the band.
    try:
        albums = session.query(Album).filter_by(
            music_band_id=current_music_band.id).all()
        number_of_albums = session.query(Album).filter_by(
            music_band_id=current_music_band.id).count()
    except:
        return "could not get the albums"

    return render_template('showAlbum.html',
                           currentBand=current_music_band,
                           albums=albums,
                           music_bands=music_bands,
                           number_of_albums=number_of_albums)


# Route for adding a band
@app.route('/catalog/add_music_band/', methods=['GET', 'POST'])
def addMusicBand():
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))

    if request.method == 'POST':
        if not request.form['music_band_name']:
            return "mising name"
        if not request.form['user_id']:
            return "Missing user_id"

        try:
            session.add(Music_Band(
                name=request.form['music_band_name'],
                user_id=request.form['user_id']))
            session.commit()
            new_music_band = session.query(Music_Band).filter_by(
                name=request.form['music_band_name']).one()
            flash("New Music Band was created")
            return redirect(url_for('homePage'))
        except:
            return "some error while adding the music band"

    else:
        return render_template('addMusicBand.html')


# Route for adding an album.
@app.route('/catalog/add_album/', methods=['GET', 'POST'])
def addAlbum():
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))

    bands = session.query(Music_Band).all()
    if request.method == 'POST':
        if not request.form['album_name']:
            return "mising name"
        if not request.form['description']:
            return "missing description"
        if not request.form['band']:
            return "missing band"
        if not request.form['user_id']:
            return "Missing user_id"

        try:
            band = session.query(Music_Band).filter_by(
                name=request.form['band']).one()
            session.add(Album(name=request.form['album_name'],
                              description=request.form['description'],
                              music_band_id=band.id,
                              user_id=request.form['user_id']))
            session.commit()
            newAlbum = session.query(Album).filter_by(
                name=request.form['album_name']).one()
            flash("New Album was created")
            return redirect(url_for('homePage'))
        except:
            return "some error while adding the album"

    else:
        return render_template('addAlbum.html', bands=bands)


# Route for showing a particular album.
@app.route('/catalog/<string:music_band_name>/<string:album_name>/')
def showAlbumInfo(music_band_name, album_name):
    try:
        album = session.query(Album).filter_by(name=album_name).one()
    except:
        return "could not get the specific album"

    return render_template('showAlbumInfo.html',
                           album=album,
                           music_band_name=music_band_name)


@app.route('/catalog/<string:music_band_name>/<string:album_name>/edit/',
           methods=['POST', 'GET'])
def editAlbum(music_band_name, album_name):

    # check if the user is logged in.
    # if not then redirect to the login page
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))

    toEditAlbum = session.query(Album).filter_by(
        name=album_name).one()

    user = session.query(User).filter_by(
        email=login_session['email']).one()

    if user.id != toEditAlbum.user_id:
        flash('Not authorized to edit the album')
        return redirect(url_for('homePage'))

    try:
        bands = session.query(Music_Band).all()
    except:
        return "Could not get the album to edit"
    if request.method == 'POST':
        if request.form['albumName']:
            toEditAlbum.name = request.form['albumName']
        if request.form['description']:
            toEditAlbum.description = request.form['description']
        if request.form['band']:
            music_band = session.query(Music_Band).filter_by(
                name=request.form['band']).one()
            toEditAlbum.music_band_id = music_band.id
        session.add(toEditAlbum)
        session.commit()
        flash('The album ' + toEditAlbum.name + 'was successfully edited')

        return redirect(url_for('homePage'))
    else:
        return render_template('editAlbum.html',
                               album=toEditAlbum, bands=bands,
                               music_band_name=music_band_name)


# Adding the deleting functionality.
@app.route('/catalog/<string:music_band_name>/<string:album_name>/delete/',
           methods=['POST', 'GET'])
def deleteAlbum(music_band_name, album_name):

    # check if the user is logged in.
    # if not then redirect to the login page
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))

    try:
        toDeleteAlbum = session.query(Album).filter_by(name=album_name).one()
        bands = session.query(Music_Band).all()
    except:
        return "Could not get the album to delete"

    # check for the authorization of the code.Check if he's
    # the owner of the album. If not, flash him the message
    # over his un-authorization.
    user = session.query(User).filter_by(email=login_session['email']).one()
    if user.id != toDeleteAlbum.user_id:
        flash('Not authorized to delete the album')
        return redirect(url_for('deleteAlbum',
                                music_band_name=music_band_name,
                                album_name=album_name))

    if request.method == 'POST':
        session.delete(toDeleteAlbum)
        session.commit()
        flash('The album ' + toDeleteAlbum.name + 'was successfully deleted')

        return redirect(url_for('homePage'))
    else:
        return render_template('homePage')


@auth.verify_password
def verify_password(username, password):
    user = session.query(User).filter_by(username=username).first()
    if not user or not user.verify_password(password):
        return False
    g.user = user
    return True


@app.route('/users', methods=['POST'])
def new_user():
    username = request.json.get('username')
    password = request.json.get('password')
    if username is None or password is None:
        abort(400)

    if session.query(User).filter_by(username=username).first() is not None:
        user = session.query(User).filter_by(username=username).first()
        return jsonify({'message': 'user already exists'}), 200, {
            'Location': url_for('get_user', id=user.id, _external=True)
        }

    user = User(username=username)
    user.hash_password(password)
    session.add(user)
    session.commit()
    return jsonify({'username': user.username}), 201, {
        'Location': url_for('get_user', id=user.id, _external=True)
    }


@app.route('/api/users/<int:id>')
def get_user(id):
    user = session.query(User).filter_by(id=id).one()
    if not user:
        abort(400)
    return jsonify({'username': user.username})


# Adding the JSON routes for API output.
@app.route('/api/catalog/<string:music_band_name>/json/')
@auth.login_required
def musicBandJSON(music_band_name):
    try:
        music_band = session.query(Music_Band).filter_by(
            name=music_band_name).one()
    except:
        return "could not get the band"

    # Get the albums for the above music_band.
    try:
        albums = session.query(Album).filter_by(
            music_band_id=music_band.id).all()
    except:
        return "could not get the albums for the music band"

    return jsonify(Albums=[i.serialize for i in albums])

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
