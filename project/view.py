from flask import Flask, render_template, request, redirect, jsonify, url_for, flash, make_response
from models import Base, Music_Band, Album, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from httplib2 import Http
from redis import Redis
import time
from functools import update_wrapper

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

# Redis code for limiting API call.
redis = Redis()

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

# Route for showing all the albums by a band.
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

# Route for adding a band
@app.route('/catalog/add_music_band/', methods=['GET', 'POST'])
def addMusicBand():
	if 'username' not in login_session:
		return redirect(url_for('showLogin'))

	if request.method == 'POST':
		print "reached in adding music bands"
		print request.form['music_band_name']
		print request.form['user_id']

		if not request.form['music_band_name']:
			return "mising name"
		if not request.form['user_id']:
			return "Missing user_id"

		try:
			session.add(Music_Band(name=request.form['music_band_name'], user_id=request.form['user_id']))
			session.commit()
			new_music_band = session.query(Music_Band).filter_by(name=request.form['music_band_name']).one()
			print "new album:"
			print new_music_band.name
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
		print "reached in adding albums"
		print request.form['album_name']
		print request.form['description']
		print request.form['user_id']
		print request.form['band']

		if not request.form['album_name']:
			return "mising name"
		if not request.form['description']:
			return "missing description" 
		if not request.form['band']:
			return "missing band"
		if not request.form['user_id']:
			return "Missing user_id"

		print "reached here yay"
		try:
			band = session.query(Music_Band).filter_by(name=request.form['band']).one()
			print band.name
			session.add(Album(name=request.form['album_name'], description=request.form['description'], music_band_id=band.id, user_id=request.form['user_id']))
			session.commit()
			print "comitted"
			newAlbum = session.query(Album).filter_by(name=request.form['album_name']).one()
			print "new album:"
			print newAlbum.name
			flash("New Album was created")
			return redirect(url_for('homePage'))
		except:
			return "some error while adding the album"

	else:
		return render_template('addAlbum.html', bands=bands)

# Route for showing a particular album.
@app.route('/catalog/<string:music_band_name>/<string:album_name>/')
def showAlbumInfo(music_band_name, album_name):
	print album_name
	try:
		album = session.query(Album).filter_by(name=album_name).one()
	except:
		return "could not get the specific album"

	return render_template('showAlbumInfo.html', album=album, music_band_name=music_band_name)

@app.route('/catalog/<string:music_band_name>/<string:album_name>/edit/', methods=['POST', 'GET'])
def editAlbum(music_band_name, album_name):

	# check if the user is logged in.
	# if not then redirect to the login page
	if 'username' not in login_session:
		return redirect(url_for('showLogin'))

	try:
		toEditAlbum = session.query(Album).filter_by(name=album_name).one()
		bands = session.query(Music_Band).all()
	except:
		return "Could not get the album to edit"
	print request
	if request.method == 'POST':
		print "reached in POST"
		if request.form['albumName']:
			print request.form['albumName']
			toEditAlbum.name = request.form['albumName']
		if request.form['description']:
			print request.form['description']
			toEditAlbum.description = request.form['description']
		if request.form['band']:
			print request.form['band']
			music_band = session.query(Music_Band).filter_by(name=request.form['band']).one()
			toEditAlbum.music_band_id = music_band.id
		print toEditAlbum.name
		print toEditAlbum.description
		print toEditAlbum.music_band_id
		session.add(toEditAlbum)
		session.commit()
		flash('The album' + toEditAlbum.name + 'was successfully edited')

		return redirect(url_for('homePage'))
	else:
		print "edit album:"
		print toEditAlbum.name
		print "band:"
		print bands
		return render_template('editAlbum.html', album=toEditAlbum, bands=bands, music_band_name=music_band_name)

# Adding the deleting functionality.
@app.route('/catalog/<string:music_band_name>/<string:album_name>/delete/', methods=['POST', 'GET'])
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
	print request
	if request.method == 'POST':
		print "reached in POST"
		print toDeleteAlbum.name
		print toDeleteAlbum.description
		print toDeleteAlbum.music_band_id
		session.delete(toDeleteAlbum)
		session.commit()
		flash('The album' + toDeleteAlbum.name + 'was successfully deleted')

		return redirect(url_for('homePage'))
	else:
		print "delete album:"
		print toDeleteAlbum.name
		print "bands:"
		print bands
		return render_template('deleteAlbum.html', album=toDeleteAlbum, bands=bands, music_band_name=music_band_name)

# Adding the JSON routes for API output.
@app.route('/catalog/<string:music_band_name>/json/', methods=['GET'])
def musicBandJSON(music_band_name):
	try:
		music_band = session.query(Music_Band).filter_by(name=music_band_name).one()
	except:
		return "could not get the band"

	# Get the albums for the above music_band.
	try:
		albums = session.query(Album).filter_by(music_band_id=music_band.id).all()
	except:
		return "could not get the albums for the music band"

	return jsonify(Albums=[i.serialize for i in albums])



if __name__ == '__main__':
    app.secret_key  = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
