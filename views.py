
from findARestaurant import findARestaurant
from models import Base, Restaurant
from flask import Flask, jsonify, request
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

import sys
import codecs
sys.stdout = codecs.getwriter('utf8')(sys.stdout)
sys.stderr = codecs.getwriter('utf8')(sys.stderr)




foursquare_client_id = 'KXTPUTXWJXUUUE22RHHQ3YNYEGZHBG31AXS0CFOHWL3AHANU'

foursquare_client_secret = '3IF050LBAUYMCD1UV55HV2IAA1WOLR3NFMWYOAVYUVCNU5U2'

google_api_key = 'AIzaSyBrLuHzG2mpXOAFwVefaA0797WMEgJYVHo'

engine = create_engine('sqlite:///restaruants.db')

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
app = Flask(__name__)

@app.route('/restaurants', methods = ['GET', 'POST'])
def all_restaurants_handler():
    #YOUR CODE HERE
    if request.method == 'POST':
        print "reached in post"
        location = request.args.get('location', '')
        mealType = request.args.get('mealType', '')

        restaurant = findARestaurant(mealType, location)
        print restaurant
        if restaurant:
            addedRestaurant = Restaurant(restaurant_name=restaurant['Restaurant Name'], restaurant_address=restaurant['Restaurant Address'], restaurant_image=restaurant['Image'])
            session.add(addedRestaurant)
            session.commit()

            print "reached before returning"
            return jsonify(restaurants = addedRestaurant.serialize)
        else:
            return "no restaurant found"

    else:
        allRestaurants = session.query(Restaurant).all()
        return jsonify(restaurants = [restaurant.serialize for restaurant in allRestaurants])
    
@app.route('/restaurants/<int:id>', methods = ['GET','PUT', 'DELETE'])
def restaurant_handler(id):
    #YOUR CODE HERE
    restaurant = session.query(Restaurant).filter_by(id=id).one()

    if request.method == 'PUT':
        if request.args.get('name'):
            restaurant.restaurant_name = request.args.get('name')
        if request.args.get('address'):
            restaurant.restaurant_address = request.args.get('address')
        if request.args.get('image'):
            restaurant.restaurant_image = rrequest.args.get('image')

        session.add()
        session.commit()
        return jsonify(restaurants = restaurant.serialize)

    elif request.method == 'DELETE':
        
        session.delete(restaurant)
        session.commit()
        return "Restaurant deleted successfully"
    else:
        
        return jsonify(restaurant = restaurant.serialize)





if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)