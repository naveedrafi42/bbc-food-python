import logging
import json
from flask import Flask
from flask_ask import Ask, request, session, question, statement
import pymysql
import requests
import inflection
from datetime import datetime

path_to_pem_file = 'C:/Users/Naveed/Desktop/CA/nav_bbc_cert.pem'

month_number_to_name = {
    1: 'january',
    2: 'febuary',
    3: 'march',
    4: 'april',
    5: 'may',
    6: 'june',
    7: 'july',
    8: 'august',
    9: 'september',
    10: 'october',
    11: 'november',
    12: 'december'
}

app = Flask(__name__)
ask = Ask(app, "/")
logging.getLogger('flask_ask').setLevel(logging.DEBUG)

conn = pymysql.connect(host='localhost', port=3306, user='root', passwd='Rockdhaba', db='bbc_food_alexa_db')

def session_exists():
    uId = session.user.userId
    queryStatement = "SELECT * FROM bbc_food_alexa_db.user_session WHERE UserAlexaId = '%s'" % uId
    try:
        cur = conn.cursor()
        cur.execute(queryStatement)
        res = cur.fetchall()
        if len(res) > 0:
            # session exists
            return True
        #session does not exist
    except:
        return statement('Sorry the skill had an internal error')
    return False

def get_session():
    uId = session.user.userId
    queryStatement = "SELECT SessionAttributes FROM bbc_food_alexa_db.user_session WHERE UserAlexaId = '%s'" % uId
    prev_session = ''
    try:
        cur = conn.cursor()
        cur.execute(queryStatement)
        res = cur.fetchall()
        for row in res:
            prev_session = row[0]
            # how to add "and" for last ingredient"
    except:
        return statement('There was an error fetching your list')
    return prev_session

def save_session(complete):
    cur = conn.cursor()
    # if user session exists
    if session_exists():
        if complete == True:
            insertStatement = "DELETE FROM `bbc_food_alexa_db`.`user_session` WHERE `UserAlexaId`='%s'" % session.user.userId
        else:
            insertStatement = "UPDATE `bbc_food_alexa_db`.`user_session` SET `SessionAttributes`= '%s' WHERE `UserAlexaId`=" \
                                "'%s'" % (json.dumps(session.attributes).replace('\'', ' a'), session.user.userId)
    else:
        insertStatement = "INSERT INTO `bbc_food_alexa_db`.`user_session` (`UserAlexaId`, `SessionAttributes`, " \
                          "`SessionComplete`) VALUES ('%s', '%s',0)" % (session.user.userId,
                                                                        json.dumps(session.attributes).replace('\'', ' a'))
    try:
        cur.execute(insertStatement)
        conn.commit()
    except:
        conn.rollback()
        return False
    return True

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

def ingredient_text_executor():
    session.attributes['list_pointer'] = 0
    session.attributes['state'] = 'recipe_ingredient_quantities'
    save_session(False)
    return ('Okay, lets do this. I will go over the ingredient quantities one by one. %s. Say next to proceed' %
            (session.attributes['ingredient_quantities'][0]))

def recipe_steps_executor():
    session.attributes['list_pointer'] = 0
    session.attributes['state'] = 'recipe_steps'
    save_session(False)
    return ('Awesome. Those were all the ingredients. Lets start cooking step by step. First %s. Say next for following steps' %
            session.attributes['recipe_steps'][0])


@ask.launch
def launch():
    # check if user was in the middle of something
    previous_session = get_session()
    if len(previous_session)>1:
        session.attributes = json.loads(previous_session)
        return question('Welcome back, you were cooking %s. Simply say next to continue.' % session.attributes['selected_recipe'])

    speech_text = 'Hey there, looks like we have a hunger emergency. Would you like some recommendations or add your favourite ingredients to my list?'
    return question(speech_text).reprompt(speech_text).simple_card('Introduction', speech_text)


@ask.intent('GetRecipes')
def recipe_handler(Ingredients):
    if str(Ingredients) == 'None':
        return question("Please tell me a base ingredient for your recommendation")
    # ingredient = inflection.singularize(Ingredients)
    url = 'https://api.live.bbc.co.uk/food/search?q="%s"' % Ingredients
    r = requests.get(url, cert=path_to_pem_file, verify=False)
    bbc_json_data = r.json()

    #bbcData = str(json.loads(r))
    recipes_returned = bbc_json_data['recipes']
    if len(recipes_returned) == 0:
        # handle case of no recipes returned
        return statement("Sorry, I couldn't find any %s recipes. Please try searching with a different ingredient" % Ingredients)
    else:
        all_recipes = [a['title'] for a in recipes_returned]
        all_recipe_ids = [a['id'] for a in recipes_returned]
        #a = list_iterator(all_recipes, Ingredients)
        session.attributes['search_term'] = Ingredients
        session.attributes['recipes'] = all_recipes
        session.attributes['recipe_ids'] = all_recipe_ids
        session.attributes['state'] = 'recipe_navigation'
        session.attributes['list_pointer'] = 0
        return question("I've found many recipes. Would you like %s. Say next for another recipe or 'go' for steps and ingredients" % all_recipes[0])


def get_all_substeps(chunky_steps):
    to_return = []
    for ls in chunky_steps:
        to_return.extend(ls)
    return to_return

@ask.intent('ExecuteRecipe')
def recipe_executor():
    session.attributes['state'] = 'recipe_ingredients'
    recipe_id = session.attributes['recipe_ids'][session.attributes['list_pointer']]
    # print(recipe_id) get recipe from recipe controller
    url = 'https://api.live.bbc.co.uk/food/recipes/%s' % recipe_id
    r = requests.get(url, cert=path_to_pem_file, verify=False)
    recipe_json = r.json()
    # session.attributes['entire_recipe'] = recipe_json
    all_stages = [a['title'] for a in recipe_json['stages']]
    ingredients = [ingredient for sublist in [stage['ingredients'] for stage in recipe_json['stages']] for ingredient in sublist]
    ingredients_texts = [ingredient['text'] for ingredient in ingredients]
    ingredients_titles = list(
        set(
            [food['title'] for sublist in [ingredient['foods'] for ingredient in ingredients]
             for food in sublist]
        )
    )
    all_steps = [a['text'] for a in recipe_json['methods']]
    temp_steps = [a.split('. ')for a in all_steps if len(a) > 1]
    session.attributes['ingredients'] = ingredients_titles
    session.attributes['recipe_stages'] = all_stages
    session.attributes['ingredient_quantities'] = ingredients_texts
    session.attributes['recipe_steps'] = [x for x in get_all_substeps(temp_steps) if len(x) > 1]
    session.attributes['selected_recipe'] = session.attributes['recipes'][session.attributes['list_pointer']]
    session.attributes['list_pointer'] = 0
    # save selected recipe session for user
    save_session(False)
    # start with ingredients (all in one)
    return question('Great, here are the ingredients you need. %s. To proceed to their quantities please say next' % ingredients_titles)

@ask.intent('AMAZON.NextIntent')
def next():
    # create a switch-case statement
    if session.attributes['state'] == 'recipe_navigation':
        if len(session.attributes['recipes']) == session.attributes['list_pointer']+1:
            return question('These were all the %s recipes I could find. Please search with a different base ingredient'
                            ' for more options. Or say previous to go back' % session.attributes['search_term'])
        session.attributes['list_pointer'] = session.attributes['list_pointer']+1
        save_session(False)
        return question("Okay, Do you want %s instead? Say next if you want something else or go to get started" %
                        session.attributes['recipes'][session.attributes['list_pointer']])\
            .simple_card(session.attributes['recipes'][session.attributes['list_pointer']])
    if session.attributes['state'] == 'recipe_steps':
        if len(session.attributes['recipe_steps']) == session.attributes['list_pointer']+1:
            save_session(True)  # HANDLE THIS
            return statement('That was the last step. I hope I was useful and that you will use me not only for %s, but'
                             'also other different recipes. Over time my features and capabilities will improve further'
                             '. Until then, bon apetite!' % session.attributes['search_term'])
        session.attributes['list_pointer'] = session.attributes['list_pointer'] + 1
        save_session(False)
        return question("%s. Please say next when you are done." %
                        session.attributes['recipe_steps'][session.attributes['list_pointer']])\
            .simple_card(session.attributes['recipe_steps'][session.attributes['list_pointer']])
    if session.attributes['state'] == 'recipe_ingredients':
        return question(ingredient_text_executor()).simple_card(session.attributes['ingredient_quantities'][0])
    if session.attributes['state'] == 'recipe_ingredient_quantities':
        if len(session.attributes['ingredient_quantities']) == session.attributes['list_pointer']+1:
            session.attributes['list_pointer'] = 0
            return question(recipe_steps_executor()).simple_card(session.attributes['recipe_steps'][0])
        session.attributes['list_pointer'] = session.attributes['list_pointer'] + 1
        save_session(False)
        return question('%s. Say next for subsequent ingredients' %
                        (session.attributes['ingredient_quantities'][session.attributes['list_pointer']])).simple_card(
                        session.attributes['ingredient_quantities'][session.attributes['list_pointer']])

@ask.intent('AMAZON.RepeatIntent')
def repeat():
    if (session.attributes['state'] == 'recipe_navigation'):
        return question("%s. Say next if you want something else or go to get started" %
                        session.attributes['recipes'][session.attributes['list_pointer']])\
            .simple_card(session.attributes['recipes'][session.attributes['list_pointer']])
    if (session.attributes['state'] == 'recipe_steps'):
        return question("%s. Please say next when you are done." %
                        session.attributes['recipe_steps'][session.attributes['list_pointer']])\
            .simple_card(session.attributes['recipe_steps'][session.attributes['list_pointer']])

@ask.intent('AMAZON.PreviousIntent')
def previous():
    if (session.attributes['state'] == 'recipe_navigation'):
        session.attributes['list_pointer'] = session.attributes['list_pointer'] - 1
        return question("%s. Say next if you want something else or go to get started" %
                        session.attributes['recipes'][session.attributes['list_pointer']])\
            .simple_card(session.attributes['recipes'][session.attributes['list_pointer']])
    if (session.attributes['state'] == 'recipe_steps'):
        session.attributes['list_pointer'] = session.attributes['list_pointer'] - 1
        return question("%s. Please say next when you are done." %
                        session.attributes['recipe_steps'][session.attributes['list_pointer']])\
            .simple_card(session.attributes['recipe_steps'][session.attributes['list_pointer']])

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
    speech_text = 'Tell me your favourite ingredients and I will get you recipes you love! You can also ask for a recipe by ingredient.'
    return question(speech_text).reprompt(speech_text).simple_card('Help', speech_text)


@ask.session_ended
def session_ended():
    return "{}", 200


if __name__ == '__main__':
    app.config['ASK_VERIFY_REQUESTS'] = False
    app.run(debug=True)