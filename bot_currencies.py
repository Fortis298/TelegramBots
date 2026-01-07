import telebot
import requests
import os

BOT_TOKEN_CUR = os.getenv('BOT_TOKEN_CUR')

bot_cur = telebot.TeleBot(BOT_TOKEN_CUR, threaded=False)


@bot_cur.message_handler(commands=['start'])
def main(message):
        bot_cur.send_message(message.chat.id, '💰 Привет! Я бот для конвертации валют.\nИспользуй команду /help чт\
обы увидеть инструкции.')

@bot_cur.message_handler(commands=['help'])
def help(message):
        help_text = """📖 *Как использовать бота:*

*Формат запроса:* `XXXYYY сумма`

*Доступные валюты:* USD, EUR, RUB, и другие валюты ЦБ РФ.

*Команды:*
/start - Начать работу с ботом
/help - Показать эту справку
/currencies - Все валюты

*Примечание:* Первые три буквы - исходная валюта, последние три - целевая валюта. RUB всегда должен быть ук\
азан."""
        bot_cur.send_message(message.chat.id, help_text, parse_mode='Markdown')


@bot_cur.message_handler(commands=['currencies'])
def currencies(message):
        try:
                response = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()['Valute']
                response['WEB'] = {'ID': 'Веременно', 'NumCode': 298 ,'CharCode': 'WEB', 'Nominal': 1, 'Name': 'Веб-коин', 'Value': 0.06, 'Previous': 0.06}
        except Exception:
                bot_cur.send_message(message.chat.id, 'Ошибка: не удалось получить данные о курсах валют')
                return
                
        list_currencies = "Все доспупные валюты:\n" + "\n".join([f"{key} – {value['Name']}" for key, value in response.items()])
        bot_cur.send_message(message.chat.id, list_currencies)


@bot_cur.message_handler()
def calc(message):
        try:
                response = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()['Valute']
                response['WEB'] = {'ID': 'Веременно', 'NumCode': 298 ,'CharCode': 'WEB', 'Nominal': 1, 'Name': 'Веб-коин', 'Value': 0.06, 'Previous': 0.06}
        except Exception:
                bot_cur.send_message(message.chat.id, 'Ошибка: не удалось получить данные о курсах валют')
                return

        print(f'@{message.from_user.username} сделал запрос')

        symbol = message.text.upper().split(maxsplit=1)

        if len(symbol) == 2 and len(symbol[0]) == 6 and symbol[1].isdigit():
                if symbol[0][0:3] in response and symbol[0][3:6] == 'RUB':
                        bot_cur.send_message(message.chat.id, f"{symbol[1]}({symbol[0][0:3]}) > {round(float(symbol[1]) * (response[symbol[0][0:3]]['Value'] / response[symbol[0][0:3]]['Nominal']), 2)}({symbol[0][3:6]})")
                elif symbol[0][3:6] in response and symbol[0][0:3] == 'RUB':
                        bot_cur.send_message(message.chat.id, f"{symbol[1]}({symbol[0][0:3]}) > {round(float(symbol[1]) / (response[symbol[0][3:6]]['Value'] / response[symbol[0][3:6]]['Nominal']), 2)}({symbol[0][3:6]})")
                else:
                        bot_cur.send_message(message.chat.id, f"Ошибка: такой валютной пары нет или она не поддерживается.")

        else:
                bot_cur.send_message(message.chat.id, f"Ошибка: формат должен быть XXXYYY сумма")
    