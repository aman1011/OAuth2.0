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


@app.route('/')
def homePage():
	print CLIENT_ID_GOOGLE
	session.add(User(username = 'Agaur'))
	session.commit()
	user = session.query(User).all()
	print user[0].username
	session.delete(user[0])
	session.commit()
	return render_template('main.html')





if __name__ == '__main__':
	app.debug = True
	app.run(host='0.0.0.0', port=5000)
