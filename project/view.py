from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from models import Base, Music_Band, Album, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
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


@app.route('/')
def homePage():
	print CLIENT_ID_GOOGLE
	bands = session.query(Music_Band).all()
	return render_template('main.html', music_bands = bands)


if __name__ == '__main__':
	app.secret_key  = 'super_secret_key'
	app.debug = True
	app.run(host='0.0.0.0', port=5000)
