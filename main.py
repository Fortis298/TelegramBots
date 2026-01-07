from flask import Flask, request
import telebot
import os

from bot_currency import bot_cur
from bot_notes import bot_notes

WEBHOOK_BOT_CUR = os.getenv('WEBHOOK_BOT_CUR')
WEBHOOK_BOT_NOTES = os.getenv('WEBHOOK_BOT_NOTES')

webhoo_url_bot_cur = f"{WEBHOOK_BOT_CUR}{bot_cur}"
webhoo_url_bot_notes = f"{WEBHOOK_BOT_NOTES}{bot_notes}"

app = Flask(__name__)

@app.route(f'/webhook/bot_cur', methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot_cur.process_new_updates([update])
    return '', 200


@app.route(f'/webhook/bot_notes', methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot_notes.process_new_updates([update])
    return '', 200


if __name__ == "__main__":
    bot_cur.remove_webhook()
    bot_cur.set_webhook(url=webhoo_url_bot_cur)
    
    
    bot_notes.remove_webhook()
    bot_notes.set_webhook(url=webhoo_url_bot_notes)
