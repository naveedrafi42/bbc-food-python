from flask import Flask, request
import json
from datetime import datetime
import requests

mmonth_number_to_name = {
    1 : 'january',
    2:'febuary',
    3:'march',
    4:'april',
    5:'may',
    6:'june',
    7:'july',
    8:'august',
    9:'september',
    10:'october',
    11:'november',
    12:'december'
}

path_to_pem_file = ''

app=Flask(__name__)

# FoodIDController
# def getFoodId(ingredient_name):
#     r = requests.get()

# GetRecipe Controller
def getRecipes(ingredient_name):
    url = 'https://api.live.bbc.co.uk/food/recipes/by/ingredient/%s/season/%s' % (ingredient_name, mmonth_number_to_name[datetime.now().month])
    r = requests.get( url, verify=path_to_pem_file )
    print(r.text)

@app.route("/process",methods=['POST'])
def func():

    #extract intent message and relevant detail
    #call relevant controller and querry bbc
    #receive and store response for user consumption
    #return data wrapped in natural language

    output_json = {
  "version": "1.0",
  "sessionAttributes": {
    "supportedHoriscopePeriods": {
      "daily": True,
      "weekly": False,
      "monthly": False
    }
  },
  "response": {
    "outputSpeech": {
      "type": "PlainText",
      "text": "This is a test. git update"
    },
    "card": {
      "type": "Simple",
      "title": "Horoscope",
      "content": "Today will provide you a new learning opportunity.  Stick with it and the possibilities will be endless."
    },
    "reprompt": {
      "outputSpeech": {
        "type": "PlainText",
        "text": "Can I help you with anything else?"
      }
    },
    "shouldEndSession": False
  }
}
    input_json = request.get_json()
    intent_name = input_json['request']['intent']['name']
    ingredient_name = input_json['request']['intent']['slots']["Ingredients"]['value']

    if intent_name == 'GetRecipes':
        something = getRecipes(ingredient_name)

    return json.dumps(output_json)


if __name__=="__main__":
    app.run(host="127.0.0.1", port=8880, debug=True)