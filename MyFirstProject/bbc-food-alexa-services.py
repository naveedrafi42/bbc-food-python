import logging
import boto3
from flask import Flask
from flask_ask import Ask, request, session, question, statement
import pymysql



app = Flask(__name__)
ask = Ask(app, "/")
logging.getLogger('flask_ask').setLevel(logging.DEBUG)

conn = pymysql.connect(host='localhost', port=3306, user='root', passwd='Rockdhaba', db='bbc_food_alexa_db')

def insertPreference(userId, Preference):
    # add user pref against userID: Use MySql for preferences and dynamo for recipes
    cur = conn.cursor()
    insertStatement = "INSERT INTO `bbc_food_alexa_db`.`user_preferences` (`UserAlexaId`, `UserPreference`) VALUES ('%s', '%s')" % (userId, Preference)
    try:
        cur.execute(insertStatement)
        conn.commit()
    except:
        conn.rollback()
        return False
    return True

@ask.launch
def launch():
    speech_text = 'Hey there, looks like we have a hunger emergency. Would you like some recommendations or add your favourite ingredients to my list?'
    return question(speech_text).reprompt(speech_text).simple_card('Introduction', speech_text)


@ask.intent('GetRecipes')
def recipe_handler(Ingredients):
    speech_text = 'UserID: {}'.format(session.user.userId)
    return statement(speech_text).simple_card('Recipes', speech_text)

@ask.intent('MeetNGreet')
def configuration_handler():
    return statement('Function not complete')

@ask.intent('GetPreferences')
def get_preferences():
    uId = session.user.userId
    queryStatement = "SELECT UserPreference FROM bbc_food_alexa_db.user_preferences WHERE UserAlexaId = '%s'" % uId
    try:
        cur = conn.cursor()
        cur.execute(queryStatement)
        res = cur.fetchall()
        responseString = 'Your list includes: '
        for row in res:
            responseString += (row[0] + ", ")
            # how to add "and" for last ingredient"
    except:
        return statement('There was an error fetching your list')
    return statement(responseString)

@ask.intent('AddPreference')
def add_preference(Preference):
    if session.application.applicationId != "amzn1.ask.skill.d637afaa-2848-4a19-8654-08459fe0d61d":
        raise ValueError("Invalid Application ID")
    print(Preference)
    if str(Preference) == 'None':
        return question('What would you like to add?')
    if insertPreference(session.user.userId,Preference)==False:
        return statement("Sorry, there was a problem adding your preference. %s is most likely already added to your list" %Preference)

    return question('Okay, %s added. Would you like to add another preference?' % (Preference) )


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