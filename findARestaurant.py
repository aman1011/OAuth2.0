# -*- coding: utf-8 -*-
from geo_code import getGeoCodeLocation
import json
import httplib2

import sys
import codecs
sys.stdout = codecs.getwriter('utf8')(sys.stdout)
sys.stderr = codecs.getwriter('utf8')(sys.stderr)

foursquare_client_id = "PASTE_YOUR_ID_HERE"
foursquare_client_secret = "YOUR_SECRET_HERE"


def findARestaurant(mealType,location):
	#1. Use getGeocodeLocation to get the latitude and longitude coordinates of the location string.
	latitude, longitude = getGeoCodeLocation(location)

	CLIENT_ID = 'KXTPUTXWJXUUUE22RHHQ3YNYEGZHBG31AXS0CFOHWL3AHANU'
	CLIENT_SECRET = '3IF050LBAUYMCD1UV55HV2IAA1WOLR3NFMWYOAVYUVCNU5U2'
	#2.  Use foursquare API to find a nearby restaurant with the latitude, longitude, and mealType strings.
	#HINT: format for url will be something like https://api.foursquare.com/v2/venues/search?client_id=CLIENT_ID&client_secret=CLIENT_SECRET&v=20130815&ll=40.7,-74&query=sushi
	url = ('https://api.foursquare.com/v2/venues/search?ll=%s,%s&client_id=%s&client_secret=%s&v=20171127&intent=browser&radius=20000&query=%s'% (latitude, longitude, CLIENT_ID, CLIENT_SECRET, mealType))
	h = httplib2.Http()
	response, content = h.request(url, 'GET')

	result = json.loads(content)

	#3. Grab the first restaurant
	venue = result['response']['venues'][0]

	#4. Get a  300x300 picture of the restaurant using the venue_id (you can change this by altering the 300x300 value in the URL or replacing it with 'orginal' to get the original picture
	url = ('https://api.foursquare.com/v2/venues/%s/photos?client_id=%s&client_secret=%s&v=20171127'% (venue['id'], CLIENT_ID, CLIENT_SECRET))
	response, content = h.request(url, 'GET')
	result = json.loads(content)

	#5. Grab the first image
	if result['response']['photos']['items']:
		photo = result['response']['photos']['items'][0]
		photourl = photo['prefix'] + '300x300' + photo['suffix']
	#6. If no image is available, insert default a image url
	else:
		photourl = 'http://www.ramw.org/sites/default/files/styles/news_item/public/default_images/default_0.jpg?itok=t5AdiGCF'

	#7. Return a dictionary containing the restaurant name, address, and image url	
	

	address = ''
	print venue['location']['formattedAddress']
	fullAddress = venue['location']['formattedAddress']
	print fullAddress[0]
	for i in fullAddress:
		print i
		address += i + ' '
	print address

	dictionary = {'Restaurant Name': venue['name'], 'Restaurant Address': address,'Image': photourl}

	print "Restaurant Name: %s" % dictionary['Restaurant Name']
	print "Restaurant Address: %s" % dictionary['Restaurant Address']
	print "Image: %s" % dictionary['Image']
	print "\n"

	return dictionary

if __name__ == '__main__':
	findARestaurant("Pizza", "Tokyo, Japan")
	findARestaurant("Tacos", "Jakarta, Indonesia")
	findARestaurant("Tapas", "Maputo, Mozambique")
	findARestaurant("Falafel", "Cairo, Egypt")
	findARestaurant("Spaghetti", "New Delhi, India")
	findARestaurant("Cappuccino", "Geneva, Switzerland")
	findARestaurant("Sushi", "Los Angeles, California")
	findARestaurant("Steak", "La Paz, Bolivia")
	findARestaurant("Gyros", "Sydney Australia")
