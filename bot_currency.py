import asyncio
import aiohttp
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

BOT_TOKEN_CUR = os.getenv('BOT_TOKEN_CUR')

bot_cur = Bot(token=BOT_TOKEN_CUR)
dp_cur = Dispatcher()

@dp_cur.message(CommandStart())
async def start(message: Message):
    await message.answer('💰 Привет! Я бот для конвертации валют.\nИспользуй команду /help чтобы увидеть инструкции.')


@dp_cur.message(Command('help'))
async def help(message: Message):
    help_text = """📖 *Как использовать бота:*

*Формат запроса:* `XXXYYY сумма`

*Доступные валюты:* USD, EUR, RUB, и другие валюты ЦБ РФ.

*Команды:*
/start - Начать работу с ботом
/help - Показать эту справку
/currencies - Все валюты

*Примечание:* Первые три буквы - исходная валюта, последние три - целевая валюта. RUB всегда должен быть ук\
азан."""
    await message.answer(help_text, parse_mode="Markdown")


@dp_cur.message(Command('currencies'))
async def currencies(message: Message):
    try:
        data = await get_data()
        response = data['Valute']
    except Exception:
        await message.answer('Ошибка: не удалось получить данные о курсах валют')
        return
        
    list_currencies = "Все доспупные валюты:\n" + "\n".join([f"{key} – {value['Name']}" for key, value in response.items()])
    await message.answer(list_currencies)



session_global = None

async def get_data():
    async with session_global.get('https://www.cbr-xml-daily.ru/daily_json.js') as response:
        return await response.json(content_type=None)


@dp_cur.message(F.text)
async def calc(message: Message):
    try:
        data = await get_data()
        response = data['Valute']
    except Exception:
        await message.answer('Ошибка: не удалось получить данные о курсах валют')
        return
        
    symbol = message.text.upper().split(maxsplit=1)
    
    if len(symbol) == 2 and len(symbol[0]) == 6 and symbol[1].isdigit():
        if symbol[0][0:3] in response and symbol[0][3:6] == 'RUB':
            await message.answer(f"{symbol[1]}({symbol[0][0:3]}) > {round(float(symbol[1]) * (response[symbol[0][0:3]]['Value'] / response[symbol[0][0:3]]['Nominal']), 2)}({symbol[0][3:6]})")
        elif symbol[0][3:6] in response and symbol[0][0:3] == 'RUB':
            await message.answer(f"{symbol[1]}({symbol[0][0:3]}) > {round(float(symbol[1]) / (response[symbol[0][3:6]]['Value'] / response[symbol[0][3:6]]['Nominal']), 2)}({symbol[0][3:6]})")
        else:
            await message.answer(f"Ошибка: такой валютной пары нет или она не поддерживается.")
    
    else:
        await message.answer(f"Ошибка: формат должен быть XXXYYY сумма")
    
