from flask import Flask
from threading import Thread
import random

app = Flask('')

@app.route('/')
def home():
    choice = random.choice((
      "Hi high.", "I'm here.", "No worries.", "Miss me?", "Hello there", "200", 
      "¯\\_(ツ)_/¯", "I feel your heart.", "👋", "I'm fine, you good?", 
      "Never going down!"
      ))
    return '⭐' + str(choice)

def run():
  app.run(host='0.0.0.0',port=8080)

def keep_alive():  
    t = Thread(target=run)
    t.start()