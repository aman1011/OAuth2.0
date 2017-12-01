url = address + '/restaurants?location=Buenos+Aires+Argentina&mealType=Sushi'. ===> JSON output through jsonify
request(url,'POST', body = data, headers = {"Content-Type": "application/json"}) 