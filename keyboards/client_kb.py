from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

b1 = KeyboardButton('/start')
b2 = KeyboardButton('/start_meeting')
b3 = KeyboardButton('/end_meeting')

phone = KeyboardButton('Телефон', request_contact=True)
location = KeyboardButton('Местоположение', request_location=True)

kb_client = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)

#kb_client.add(b1).add(b2).insert(b3)

kb_client.row(b1, b2, b3).row(phone, location)
