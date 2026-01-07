import telebot
from telebot import types
from telebot.apihelper import ApiTelegramException
import psycopg
import os

BOT_TOKEN_NOTES = os.getenv('BOT_TOKEN_NOTES')
BD = os.getenv('BD_NOTES')

bot_notes = telebot.TeleBot(BOT_TOKEN_NOTES, threaded=False)

conn = psycopg.connect(BD)
conn.autocommit = True

user_status = {}
user_data = {}
bot_message_id = {}
note_id_Edit = {}

@bot_notes.message_handler(commands=['start'])
def start(message):	
	main_menu(message.chat.id)
	

@bot_notes.callback_query_handler(func=lambda call:True)
def callback(call):	
	if call.message:
				
		### СОЗДАНИЕ ЗАМЕТОК BUTTON. ДОБАВЛЕНИЕ SQL НАХОДИТСЯ В ОЖИДАНИИ ВВОДА ###
		if call.data == 'add_note':	
			user_status[call.from_user.id] = 'waiting_title'			
			bot_message_id[call.from_user.id] = call.message.message_id
			
			markup = types.InlineKeyboardMarkup(row_width=1)			
			button_exit = types.InlineKeyboardButton('⬅️ Отмена', callback_data='exit')			
			markup.add(button_exit)	
			
			bot_message_id[call.from_user.id] = send_safe(
				call.message.chat.id, 				
				call.message.message_id, 				
				'✏️ Введите название заметки', 				
				markup			
			)
			
			
		### ПОКАЗ ЗАМЕТОК BUTTON ###
		elif call.data == 'all_note':
			print_button_notes(call, 'p', '🗒 *Ваши заметки:*')
			
			
		### КНОПКА К ВОЗВРАЩЕНИЮ ПОКАЗА ЗАМЕТОК ###
		elif call.data == 'exit_list_pNote':
			print_button_notes(call, 'p', '🗒 *Ваши заметки:*')
			
			
		### ПОКАЗ ЗАМЕТОК SQL ###
		elif call.data.startswith('pNote_'):
			note_id = int(call.data.split('_')[1])
			
			with conn.cursor() as cur:	
				cur.execute('SELECT title, text, created_at FROM notes WHERE id = %s AND user_id = %s;', (note_id, call.from_user.id,))				
				note = cur.fetchone()
			
			title, text, created_at = note
			text_note = '*' + title + '*' + '\n\n' + text + '\n\n' + '*'+ 'Создано: ' + str(created_at)[0:10] + '*'
			
			markup = types.InlineKeyboardMarkup(row_width=1)
			markup.add(types.InlineKeyboardButton('⬅️ Назад', callback_data='exit_list_pNote'))
			
			bot_message_id[call.from_user.id] = send_safe(
				call.message.chat.id,
				call.message.message_id,
				text_note,
				markup
			)
			
			
		### УДАЛЕНИЕ ЗАМЕТОК BUTTON ###
		elif call.data == 'del_note':
			print_button_notes(call, 'd', '🚮 *Выберите заметку для удаления:*')
			
			
		### КНОПКА ВОЗВРАЩЕНИЯ К УДАЛЕНИЮ ЗАМЕТОК ###
		elif call.data == 'exit_list_dNote':
			print_button_notes(call, 'd', '🚮 *Выберите заметку для удаления:*')
			
			
		### УДАЛЕНИЕ ЗАМЕТОК SQL ###
		elif call.data.startswith('dNote_'):
			note_id = int(call.data.split('_')[1])
			
			with conn.cursor() as cur:
				cur.execute('DELETE FROM notes WHERE id = %s AND user_id = %s;', (note_id, call.from_user.id,))
				
				markup = types.InlineKeyboardMarkup(row_width=1)
				markup.add(types.InlineKeyboardButton('⬅️ Назад', callback_data='exit_list_dNote'))
				
				bot_message_id[call.from_user.id] = send_safe(
					call.message.chat.id,				
					call.message.message_id,
					'✅ Заметка удалена',
					markup
				)
				
				
		### РЕДАКТИРОВАНИЕ ЗАМЕТОК BUTTON ###
		elif call.data == 'edit_note':
			print_button_notes(call, 'e', '📝 *Выберите заметку для редактирования:*')
				
				
		### КНОПКА ОТМЕНЫ/НАЗАД ###
		elif call.data == 'exit':	
			user_status.pop(call.from_user.id, None)			
			bot_message_id.pop(call.from_user.id, None)
			note_id_Edit.pop(call.from_user.id, None)
			main_menu(call.message.chat.id, call.message.message_id)
			
			
		### КНОПКА ПОКАЗА ГЛАВНОГО МЕНЮ ###
		elif call.data == 'main_menu':		
			main_menu(call.message.chat.id, call.message.message_id)
			
			
		### РЕДАКТИРОВАНИЕ ТЕКСТА SQL ###
		elif call.data.startswith('eNote_'):
			
			note_id_Edit[call.from_user.id] = int(call.data.split('_')[1])
			
			user_status[call.from_user.id] = 'edit_note_text'						
			bot_message_id[call.from_user.id] = call.message.message_id						
			
			markup = types.InlineKeyboardMarkup(row_width=1)						
			button_exit = types.InlineKeyboardButton('⬅️ Отмена', callback_data='exit')	
			markup.add(button_exit)							
			
			bot_message_id[call.from_user.id] = send_safe(				
				call.message.chat.id, 								
				call.message.message_id, 								
				'✏️ Введите новый текст:', 								
				markup						
			)
			
			
			
@bot_notes.message_handler(content_types='text')
def input_processing(message):	
	user_id = message.from_user.id		
	
	### ОЖИДАНИЕ ВВОДЕ НАЗВАНИЯ ###
	if user_status.get(user_id) == 'waiting_title':		
		user_status.pop(message.from_user.id)		
		user_status[message.from_user.id] = 'waiting_text'
		user_data[message.from_user.id] = {'title': message.text}		
		
		bot_notes.delete_message(message.chat.id, message.message_id)				
		
		markup = types.InlineKeyboardMarkup(row_width=1)		
		button_exit = types.InlineKeyboardButton('⬅️ Отмена', callback_data='exit')		
		markup.add(button_exit)		
												
		bot_message_id[user_id] = send_safe(				
			message.chat.id, 				
			bot_message_id.get(user_id), 				
			'✅ *Отлично*\n\nTеперь ввените текст', 				
			markup			
		)
			
	### ОЖИДАНИЕ ВВОДА ТЕКСТА ###
	elif user_status.get(user_id) == 'waiting_text': 		
		user_data[message.from_user.id]['text'] = message.text	
		bot_notes.delete_message(message.chat.id, message.message_id)		
				
		add_note(
			user_id,			
			user_data[user_id]['title'],			
			user_data[user_id]['text']		
		)
				
		markup = types.InlineKeyboardMarkup(row_width=1)		
		button_main_menu = types.InlineKeyboardButton('🏠 На главную', callback_data='main_menu')	
		markup.add(button_main_menu)	
					
		bot_message_id[user_id] = send_safe(							
			message.chat.id, 							
			bot_message_id.get(user_id), 							
			'✅ Заметка добавлена!', 							
			markup					
		)
			
		user_status.pop(message.from_user.id)		
		bot_message_id.pop(message.from_user.id)
		
	### ОЖИДАНИЕ ВВОДА НОВОГО ТЕКСТА. РЕДАКТИРОВАНИЕ ТЕКСТА SQL ###
	elif user_status.get(user_id) == 'edit_note_text':
		with conn.cursor() as cur: 
		  cur.execute('UPDATE notes SET text = %s WHERE id = %s AND user_id = %s;', (message.text, note_id_Edit[user_id], user_id))
		  
		markup = types.InlineKeyboardMarkup(row_width=1)
		button_main_menu = types.InlineKeyboardButton('🏠 На главную', callback_data='main_menu')	
		markup.add(button_main_menu)
		
		bot_message_id[user_id] = send_safe(							
			message.chat.id, 							
			bot_message_id.get(user_id), 							
			'✅ Заметка обновлена!', 							
			markup					
		)

		note_id_Edit.pop(user_id)
		bot_notes.delete_message(message.chat.id, message.message_id)	
				
		
### ПОКАЗ КНОПОК ДЛЯ ВЫБОРА ЗАМЕТОК ###
def print_button_notes(call, symbol, text):
	with conn.cursor() as cur:				
		cur.execute('SELECT id, title FROM notes WHERE user_id = %s;', (call.from_user.id,))
		notes = cur.fetchall()							
		
	if not notes:				
		markup = types.InlineKeyboardMarkup(row_width=1)	
									
		button_main_menu = types.InlineKeyboardButton('🏠 На главную', callback_data='main_menu')	
		markup.add(button_main_menu)	
									
		bot_message_id[call.from_user.id] = send_safe(									
			call.message.chat.id, 									
			call.message.message_id, 									
			'У вас пока нет заметок 🥲', 									
			markup							
		)				
		return						
		
	markup = types.InlineKeyboardMarkup(row_width=1)
									
	for note_id, title in notes:				
		markup.add(types.InlineKeyboardButton(text=title, callback_data=f'{symbol}Note_{note_id}'))			
						
	markup.add(types.InlineKeyboardButton('🏠 На главную', callback_data='main_menu'))				

	bot_message_id[call.from_user.id] = send_safe(								
		call.message.chat.id, 								
		call.message.message_id, 								
		text, 								
		markup						
	)
	
		
### БЕЗОПАСТНОЯ ОТПРАВКА СООБЩЕНИЙ ###
def send_safe(chat_id, message_id, text, markup):
	try:				
		bot_notes.edit_message_text(									
			chat_id=chat_id, 									
			message_id=message_id,									
			text=text,									
			reply_markup=markup,
			parse_mode='Markdown'				
		)
		return message_id		
	except ApiTelegramException:				
		msg = bot_notes.send_message(														
			chat_id=chat_id, 														
			text=text,														
			reply_markup=markup,
			parse_mode='Markdown'									
		)
		return msg.message_id
		
		
### СОЗДАНИЯ ЗАМЕТОК SQL ###
def add_note(user_id, title, text):
	with conn.cursor() as cur:
		cur.execute('INSERT INTO notes (user_id, title, text) VALUES (%s, %s, %s)', (user_id, title, text))


### ГЛАВНОЕ МЕНЮ ###
def main_menu(chat_id, message_id=None):	
	markup = types.InlineKeyboardMarkup(row_width=2)	
	button_add_note = types.InlineKeyboardButton('🆕 Новая заметка', callback_data='add_note')	
	button_del_note = types.InlineKeyboardButton('🗑 Удалить заметку', callback_data='del_note')	
	button_edit_note = types.InlineKeyboardButton('📝 Ред. заметку', callback_data='edit_note')	
	button_all_note = types.InlineKeyboardButton('🗒 Все заметки', callback_data='all_note')		
	
	markup.add(button_add_note, button_del_note, button_edit_note, button_all_note)	
	
	text = (
		'🎉 *Добро пожаловать в MyNotes!*\n\n'
		'Здесь вы можете:\n'
		'*•* Создавать новые заметки\n'
		'*•* Просматривать все записи\n'
		'*•* Редактировать и удалять\n\n'
		'Выберите действие ниже:'
		)    	
	
	if message_id:	
		send_safe(chat_id, message_id, text, markup)
	else:		
		bot_notes.send_message(chat_id, text, parse_mode='Markdown', reply_markup=markup)    	