import asyncio
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.exceptions import TelegramBadRequest
import asyncpg
import os

BOT_TOKEN_NOTES = os.getenv('BOT_TOKEN_NOTES')
BD_NOTES = os.getenv('BD_NOTES')

bot_notes = Bot(token=BOT_TOKEN_NOTES)
dp_notes = Dispatcher()

router = Router()
dp_notes.include_router(router)

pool = None

user_status = {}
user_data = {}
bot_message_id = {}
note_id_Edit = {}

### ОБРАБОТЧИК /START ###
@dp_notes.message(CommandStart())
async def start(message: Message):
  await main_menu(message)



### КНОПКА СОЗДАНИЯ ЗАМЕТОК###
@router.callback_query(F.data == 'add_note')
async def click_buttom_add_note(callback: CallbackQuery):
  user_status[callback.from_user.id] = 'waiting_title'	
  bot_message_id[callback.from_user.id] = callback.message.message_id
  
  button_exit = InlineKeyboardButton(text='⬅️ Отмена', callback_data='exit')
  markup = InlineKeyboardMarkup(inline_keyboard=[[button_exit]])
  
  bot_message_id[callback.from_user.id] = await send_safe(
    callback,
    callback.message.chat.id,
    callback.message.message_id,
    '✏️ Введите название заметки', 				
		markup
  )



### КНОПКА УДАЛЕНИЕ ЗАМЕТОК ###
@router.callback_query(F.data == 'del_note')
async def click_buttom_del_note(callback: CallbackQuery):
  await print_list_note(callback, 'del', '🚮 *Выберите заметку для удаления:*')

### ВОЗВРАЩЕНИЕ К ВЫБОРУ ЗАМЕТКИ ДЛЯ УДАЛЕНИЯ ###
@router.callback_query(F.data == 'return_list_delNote')
async def click_buttom_return_list_delNote(callback: CallbackQuery):
  await print_list_note(callback, 'del', '🚮 *Выберите заметку для удаления:*')

### УДАЛЕНИЕ ЗАМЕТОК SQL ###
@router.callback_query(F.data.startswith('delNote_'))
async def click_list_buttom_del(callback: CallbackQuery):
  note_id = int(callback.data.split('_')[1])
  
  async with pool.acquire() as conn:
    await conn.execute("DELETE FROM notes WHERE id = $1 AND user_id = $2", note_id, callback.from_user.id)
  
  button_main_menu = InlineKeyboardButton(text='⬅️ Назад', callback_data='return_list_delNote')
  markup = InlineKeyboardMarkup(inline_keyboard=[[button_main_menu]])
  
  bot_message_id[callback.from_user.id] = await send_safe(
    callback,
    callback.message.chat.id,
    callback.message.message_id,
    '✅ Заметка удалена',
		markup
  )



### КНОПКА ПОКАЗА ЗАМЕТОК ###
@router.callback_query(F.data == 'all_note')
async def click_buttom_all_note(callback: CallbackQuery):
  await print_list_note(callback, 'all', '🗒 *Ваши заметки:*')

### ВОЗВРАЩЕНИЕ К ВЫБОРУ ЗАМЕТКИ ДЛЯ ПРОСМОТРА ###
@router.callback_query(F.data == 'return_list_allNote')
async def click_buttom_return_list_allNote(callback: CallbackQuery):
  await print_list_note(callback, 'all', '🗒 *Ваши заметки:*')

### ПОКАЗ ЗАМЕТОК SQL ###
@router.callback_query(F.data.startswith('allNote_'))
async def click_list_buttom_all(callback: CallbackQuery):
  note_id = int(callback.data.split('_')[1])
  
  async with pool.acquire() as conn:
    note_info = await conn.fetchrow("SELECT title, text, created_at FROM notes WHERE id = $1 AND user_id = $2", note_id, callback.from_user.id)
  
  title, text, created_at = note_info
  text_note_info = '*' + title + '*' + '\n\n' + text + '\n\n' + 'Создано: ' + str(created_at)[0:10]
			
  button_main_menu = InlineKeyboardButton(text='⬅️ Назад', callback_data='return_list_allNote')
  markup = InlineKeyboardMarkup(inline_keyboard=[[button_main_menu]])
  
  bot_message_id[callback.from_user.id] = await send_safe(
    callback,
    callback.message.chat.id,
    callback.message.message_id,
    text_note_info,
		markup
  )
  
  
  
### КНОПКА РЕДАКТИРОВАНИЯ ЗАМЕТОК ###
@router.callback_query(F.data == 'edit_note')
async def click_buttom_edit_note(callback: CallbackQuery):
  await print_list_note(callback, 'edit', '📝 *Выберите заметку для редактирования:*')
  
### ПОКАЗ ЗАМЕТОК SQL ###
@router.callback_query(F.data.startswith('editNote_'))
async def click_list_buttom_edit(callback: CallbackQuery):
  note_id_Edit[callback.from_user.id] = int(callback.data.split('_')[1])
  user_status[callback.from_user.id] = 'edit_note_text'	
  
  button_exit = InlineKeyboardButton(text='⬅️ Назад', callback_data='exit')
  markup = InlineKeyboardMarkup(inline_keyboard=[[button_exit]])
  
  bot_message_id[callback.from_user.id] = await send_safe(
    callback,
    callback.message.chat.id,
    callback.message.message_id,
    '✏️ Введите новый текст:',
		markup
  )


  
### ОБРАБОТКА НАЖАТИЯ КНОПКИ exit ###
@router.callback_query(F.data == 'exit')
async def click_buttom_exit(callback: CallbackQuery):
  user_status.pop(callback.from_user.id, None)			
  bot_message_id.pop(callback.from_user.id, None)
  note_id_Edit.pop(callback.from_user.id, None)
  
  await main_menu(callback, callback.message.message_id, callback.message.chat.id)
  
### ОБРАБОТКА НАЖАТИЯ КНОПКМ main_menu ###
@router.callback_query(F.data == 'main_menu')
async def click_buttom_main_menu(callback: CallbackQuery):
  await main_menu(callback, callback.message.message_id, callback.message.chat.id)
  

### ВВОД ТЕКСТА ###
@dp_notes.message(F.text)
async def input_processing(message: Message):
  user_id = message.from_user.id
  
  ### ОЖИДАНИЕ ВВОДА НАЗВАНИЯ ###
  if user_status.get(user_id) == 'waiting_title':
    user_status.pop(message.from_user.id)
    user_status[message.from_user.id] = 'waiting_text'
    user_data[message.from_user.id] = {'title': message.text}
    
    await bot_notes.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    
    button_exit = InlineKeyboardButton(text='⬅️ Отмена', callback_data='exit')
    markup = InlineKeyboardMarkup(inline_keyboard=[[button_exit]])
    
    bot_message_id[message.from_user.id] = await send_safe(
      message,
      message.chat.id,
      bot_message_id.get(user_id),
      '✅ *Отлично*\n\nTеперь ввените текст', 	
      markup
    )
  
  ### ОЖИДАНИЕ ВВОДА ТЕКСТА ###
  elif user_status.get(user_id) == 'waiting_text':
    user_data[message.from_user.id]['text'] = message.text
    await bot_notes.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    
    # SQL
    async with pool.acquire() as conn:
      await conn.execute("INSERT INTO notes (user_id, title, text) VALUES ($1, $2, $3)", user_id, user_data[user_id]['title'],	user_data[user_id]['text'])
    
    button_main_menu = InlineKeyboardButton(text='🏠 На главную', callback_data='main_menu')
    markup = InlineKeyboardMarkup(inline_keyboard=[[button_main_menu]])
    
    bot_message_id[message.from_user.id] = await send_safe(
      message,
      message.chat.id,
      bot_message_id.get(user_id),
      '✅ Заметка добавлена!', 
      markup
    )
    
    user_status.pop(message.from_user.id)
    bot_message_id.pop(message.from_user.id)
    
  ### ОЖИДАНИЕ ВВОДА НОВОГО ТЕКСТА ###
  elif user_status.get(user_id) == 'edit_note_text':
    async with pool.acquire() as conn:
      await conn.execute("UPDATE notes SET text = $1 WHERE id = $2 AND user_id = $3", message.text, note_id_Edit[user_id], user_id)
    
    await bot_notes.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    
    button_main_menu = InlineKeyboardButton(text='🏠 На главную', callback_data='main_menu')
    markup = InlineKeyboardMarkup(inline_keyboard=[[button_main_menu]])
    
    bot_message_id[message.from_user.id] = await send_safe(
      message,
      message.chat.id,
      bot_message_id.get(user_id),
      '✅ Заметка обновлена!', 
      markup
    )
    
    note_id_Edit.pop(user_id)
    

### БЕЗОПАСТНАЯ ОТПРАВКА СООБЩЕНИЙ ###
async def send_safe(message, chat_id, message_id, text, markup):
  try:
    await message.bot.edit_message_text(
      chat_id=chat_id, 
      message_id=message_id,
      text=text, 
      reply_markup=markup, 
      parse_mode='Markdown'
    )
    return message_id
  except TelegramBadRequest:
    msg = await message.answer(
      text=text,									
			reply_markup=markup,
			parse_mode='Markdown'
    )
    return msg.message_id


### ПОКАЗ ГЛАВНОГО МЕНЮ ###
async def main_menu(message, message_id=None, chat_id=None):
  button_add_note = InlineKeyboardButton(text='🆕 Новая заметка', callback_data='add_note')
  button_del_note = InlineKeyboardButton(text='🗑 Удалить заметку', callback_data='del_note')
  button_edit_note = InlineKeyboardButton(text='📝 Ред. заметку', callback_data='edit_note')
  button_all_note = InlineKeyboardButton(text='🗒 Все заметки', callback_data='all_note')
  
  markup = InlineKeyboardMarkup(inline_keyboard=[
    [button_add_note, button_del_note],
    [button_edit_note, button_all_note]
  ])
  
  text = (
		'🎉 *Добро пожаловать в MyNotes!*\n\n'
		'Здесь вы можете:\n'
		'*•* Создавать новые заметки\n'
		'*•* Просматривать все записи\n'
		'*•* Редактировать и удалять\n\n'
		'Выберите действие ниже:'
	)
	
  if message_id and chat_id:
    await send_safe(message, chat_id, message_id, text, markup)
  else:
    await message.answer(text, reply_markup=markup, parse_mode='Markdown')


### ПОКАЗ КНОПОК ДЛЯ ВЫБОРА ЗАМЕТОК ###
async def print_list_note(callback, symbol, text):
  async with pool.acquire() as conn:
      notes = await conn.fetch("SELECT id, title FROM notes WHERE user_id = $1", callback.from_user.id)
      
  if not notes:
    button_main_menu = InlineKeyboardButton(text='🏠 На главную', callback_data='main_menu')
    markup = InlineKeyboardMarkup(inline_keyboard=[[button_main_menu]])
    
    bot_message_id[callback.from_user.id] = await send_safe(
      callback,
      callback.message.chat.id,
      callback.message.message_id,
      'У вас пока нет заметок 🥲', 				
      markup
    )
    return
  
  buttons = []
  button_main_menu = InlineKeyboardButton(text='🏠 На главную', callback_data='main_menu')
  
  for note_id, title in notes:
    button = InlineKeyboardButton(text=title, callback_data=f'{symbol}Note_{note_id}')
    buttons.append([button])
  
  buttons.append([button_main_menu])
  markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    
  bot_message_id[callback.from_user.id] = await send_safe(
      callback,
      callback.message.chat.id,
      callback.message.message_id,
      text,
      markup
    )
    
