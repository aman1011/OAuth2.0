import httplib2
import json


def getGeoCodeLocation(addressString):
	google_api_key = 'AIzaSyBrLuHzG2mpXOAFwVefaA0797WMEgJYVHo'

	# replacing input string.
	locationString = addressString.replace(' ', '+')
	url = ('https://maps.googleapis.com/maps/api/geocode/json?address=%s&key=%s'% (locationString, google_api_key))
	h = httplib2.Http()
	response, content = h.request(url, 'GET')
	result = json.loads(content)
	return result['results'][0]['geometry']['location']['lat'], result['results'][0]['geometry']['location']['lng']
