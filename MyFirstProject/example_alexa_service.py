from flask import Flask
from flask_ask import Ask, statement, question, session
import json
import requests
import time
import unidecode
from bs4 import BeautifulSoup
import utils
from topics import *
from my_topics import TOPIC_DIC
#!/usr/bin/env python
# -*- encoding: utf8 -*-

CERT="/Users/mikroe01/certificates/certificate.pem"

app = Flask(__name__)
ask = Ask(app, "/bbc_sports_reader")

def get_sports_headlines_by_topic(topic):
    guid = TOPIC_DIC[topic]
    query = "https://morph.api.bbci.co.uk/data/bbc-morph-cs-sport-headlines-by-guid/cworkFormat/TextualFormat/cworkType/cwork:NewsItem,cwork:LiveEventPage/guid/%s/limit/3" % guid
    print query
    headers = {"Content-Type": "application/json"}
    response = utils.http_get(endpoint=query, params=None, headers=headers, ssl_cert=CERT)
    data = json.loads(response)
    briefs = ""
    for headline in data['headlines']:
        brief = (headline['title'], '... ', headline['summary'])
        briefs += '... '.join(brief)
    print briefs
    return briefs


def get_sports_headlines():
    url = "http://feeds.bbci.co.uk/sport/rss.xml"
    params={"edition" : "uk"}
    headers = {"Content-Type": "application/xml"}
    result_set = utils.http_get(endpoint=url, params=params, headers=headers)
    # print result_set['title']
    parser = BeautifulSoup(result_set, "html.parser")
    briefs = ""
    for item in parser.find_all('item'):
        title = item.find_all('title')[0].text
        description = item.find_all('description')[0].text
        brief = (title, '... ', description)
        briefs += '... '.join(brief)
    return briefs

@app.route('/')
def homepage():
    return "hi there, how ya doin?"

@ask.launch
def start_skill():
    welcome_message = 'Hello there, would you like the BBC Sport headlines or headlines by Topic?'
    return question(welcome_message)

@ask.intent("HeadlinesIntent")
def share_headlines():
    headlines = get_sports_headlines()
    headline_msg = 'The current BBC Sport headlines are {}'.format(headlines)
    return statement(headline_msg)

@ask.intent("HeadlinesByTopicIntent")
def share_headlines():
    msg = 'Ok what is your topic?'
    return question(msg)

@ask.intent("MyTopicIsIntent")
def share_headlines_by_topic(topic):
    session.attributes['topic'] = topic
    headlines = get_sports_headlines_by_topic(topic.lower())
    headline_msg = 'The current BBC Sport headlines for {} are {}'.format(topic, headlines)
    return statement(headline_msg)

@ask.intent("WhatsMyTopicIntent")
def share_headlines_by_topic():
    session.attributes['topics'] = TOPICS
    msg = 'Your BBC Sport topics are {}. What is your topic?'.format(TOPICS)
    return question(msg)


@ask.intent("NoIntent")
def no_intent():
    bye_text = 'Sorry I cannot understand what you mean'
    return statement(bye_text)
    
if __name__ == '__main__':
    app.run(debug=True)