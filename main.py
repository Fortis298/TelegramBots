from flask import Flask, request
import telebot
import os

from bot_currency import bot_cur
from bot_notes import bot_notes

app = Flask(__name__)

@app.route(f'/webhook/bot_cur', methods=['POST'])
def webhook_cur():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot_cur.process_new_updates([update])
    return '', 200


@app.route(f'/webhook/bot_notes', methods=['POST'])
def webhook_notes():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot_notes.process_new_updates([update])
    return '', 200


@app.route("/")
def health():
    return "ok", 200

if __name__ == "__main__":
   port = int(os.getenv("PORT", 10000))
   app.run(host="0.0.0.0", port=port)
