import logging
from flask import Flask
from flask_ask import Ask, request, session, question, statement


app = Flask(__name__)
ask = Ask(app, "/")
#logging.getLogger('flask_ask').setLevel(logging.DEBUG)


@ask.launch
def launch():
    speech_text = 'Welcome to the BBC food skills. Here, I can help you get your favourite recipes.'
    return question(speech_text).reprompt(speech_text).simple_card('Introduction', speech_text)


@ask.intent('GetRecipes')
def recipe_handler(Ingredients):
    print(request.user.userId)
    speech_text = 'Hi %s' % Ingredients
    return statement(speech_text).simple_card('Recipes', speech_text)

@ask.intent('MeetNGreet')
def configuration_handler():
    return statement('Function not complete')

@ask.intent('AddPreference')
def add_preference(Preference):
    userId = session.user.userId
    #add user pref against userID
    return statement('Function not complete')


@ask.intent('AMAZON.HelpIntent')
def help():
    speech_text = 'Tell me your favourite ingredients and I will get you recipes you love!'
    return question(speech_text).reprompt(speech_text).simple_card('Help', speech_text)


@ask.session_ended
def session_ended():
    return "{}", 200


if __name__ == '__main__':
    app.config['ASK_VERIFY_REQUESTS'] = False
    app.run(debug=True)