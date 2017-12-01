from flask import Flask, render_template
from models import Base, Music_Band, Album, User

app = Flask(__name__)

# login session.
from flask import 


@app.route('/')
def homePage():
	return render_template('main.html')





if __name__ == '__main__':
	app.debug = True
	app.run(host='0.0.0.0', port=5000)
