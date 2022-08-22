from datetime import datetime, time

from aiogram import Dispatcher, types
from aiogram.dispatcher.filters import Text
from aiogram.utils.markdown import text, bold
from aiogram.dispatcher import FSMContext
from aiogram.types import ParseMode, ReplyKeyboardRemove
from aiogram.dispatcher.filters.state import State, StatesGroup

from emoji.core import emojize

from create_bot import bot
from data_base import postgresql

from keyboards import kb_client


class Meet(StatesGroup):
    start = State()
    category = State()
    end = State()


class Work(StatesGroup):
    start = State()
    category = State()
    comment = State()
    end = State()


async def welcome(message: types.Message):
    await message.delete()
    message_text = text(emojize(f'Добро пожаловать, {message.from_user.username} :smirk:', language='alias'))

    await bot.send_message(
        message.from_user.id,
        message_text,
        parse_mode=ParseMode.MARKDOWN
    )

    await postgresql.sql_user_add({'uid': message.from_user.id,
                                   'username': message.from_user.username,
                                   'date_start': str(datetime.now().date())})


async def menu(message: types.Message):

    await message.delete()
    check = await postgresql.sql_check_user(message.from_user.id)
    if check == []:
        await bot.send_message(
            message.from_user.id,
            text(emojize(f'So... \nWho are u? :hushed: \nPlease, click this: /start', language='alias')),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        menu_keyboards = types.InlineKeyboardMarkup(row_width=2)
        button = []

        for item in ['Meet', 'Work', 'Settings']:
            button.append(types.InlineKeyboardButton(text=item, callback_data=item))

        await bot.send_message(
                message.from_user.id,
                'What do you wish?',
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=menu_keyboards.add(*button).add(types.InlineKeyboardButton(text='Cancel', callback_data='cancel'))
            )


async def menu_callback(callback: types.CallbackQuery):

    await callback.bot.delete_message(callback.from_user.id, callback.message.message_id)
    menu_keyboards = types.InlineKeyboardMarkup(row_width=2)
    button = []

    for item in ['Meet', 'Work', 'Settings']:
        button.append(types.InlineKeyboardButton(text=item, callback_data=item))

    await bot.send_message(
            callback.from_user.id,
            'What do you wish?',
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=menu_keyboards.add(*button).add(types.InlineKeyboardButton(text='Cancel', callback_data='cancel'))
        )


async def clients_settings(callback: types.CallbackQuery):

    await callback.bot.delete_message(callback.from_user.id, callback.message.message_id)
    menu_keyboards = types.InlineKeyboardMarkup(row_width=2)
    button = []

    for item in ['Add category', 'Rename caterory', 'Delete category', 'Change time of work']:
        button.append(types.InlineKeyboardButton(text=item, callback_data=item))

    await bot.send_message(
            callback.from_user.id,
            'What do you wish to modify?',
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=menu_keyboards.add(*button).add(types.InlineKeyboardButton(text='Menu', callback_data='Menu'),
                                                         types.InlineKeyboardButton(text='Cancel', callback_data='cancel'))
        )


async def start_meeting(callback: types.CallbackQuery, state=None):
    # state
    await state.finish()
    await Meet.start.set()

    await bot.delete_message(callback.from_user.id, callback.message.message_id)
    cancel = types.InlineKeyboardButton(text='Cancel', callback_data='cancel')
    inkb = types.InlineKeyboardMarkup(row_width=2).add(types.InlineKeyboardButton(text='Finish meet', callback_data='finish_meet')).add(cancel)

    date = datetime.now().replace(microsecond=0)
    day = date.strftime("%d.%m.%Y %H:%M:%S").split(' ')
    message_text = text(emojize(f'Started meeting at {day[0]} in {day[1]} 🥺', language='alias') +
                        "\nPush the button, after meet")

    async with state.proxy() as data:
        data['start'] = date

    await bot.send_message(
        callback.from_user.id,
        message_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=inkb
    )


async def end_meeting(callback: types.CallbackQuery, state: FSMContext):

    await bot.delete_message(callback.from_user.id, callback.message.message_id)

    date = datetime.now().replace(microsecond=0)
    day = date.strftime("%d.%m.%Y %H:%M:%S").split(' ')

    async with state.proxy() as data:
        data['end'] = date

    start_date = data["start"].strftime("%d.%m.%Y %H:%M:%S").split(' ')

    message_text = text(
        emojize(f'Started meeting at {start_date[0]} in {start_date[1]} 🥺',
                language='alias') + '\n' +
        emojize(f'Finished meeting at {day[0]} in {day[1]} 🎉', language='alias'))

    await bot.send_message(
        callback.from_user.id,
        message_text,
        parse_mode=ParseMode.MARKDOWN
    )

    await postgresql.sql_entries_add({'uid': callback.from_user.id,
                                      'category': 'meet',
                                      'time': (data['end'] - data['start']).seconds,
                                      'date': day[0],
                                      'comment': 'не реализовано'})
    await state.finish()


async def start_working(callback: types.CallbackQuery, state=None):
    # state
    await state.finish()
    await Work.start.set()

    await bot.delete_message(callback.from_user.id, callback.message.message_id)
    categories = await postgresql.show_categories(callback.from_user.id)

    inkb = types.InlineKeyboardMarkup(row_width=2)
    button = []

    for item in categories:
        button.append(types.InlineKeyboardButton(text=item['category'], callback_data='job~' + item['category']))

    date = datetime.now().replace(microsecond=0)
    day = date.strftime("%d.%m.%Y %H:%M:%S").split(' ')
    message_text = text(emojize(f'Started working at {day[0]} in {day[1]} 🥺', language='alias') + '\nChoose category for work, please!')

    async with state.proxy() as data:
        data['start'] = date

    await bot.send_message(
        callback.from_user.id,
        message_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=inkb.add(*button).add(types.InlineKeyboardButton(text='Cancel', callback_data='cancel'))
    )


async def start_working_2(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['category'] = callback.data.split('~')[1]
    await bot.delete_message(callback.from_user.id, callback.message.message_id)

    inkb = types.InlineKeyboardMarkup(row_width=2)
    button = [types.InlineKeyboardButton(text='Finish work', callback_data='finish_work'),
              types.InlineKeyboardButton(text='Add comment', callback_data='add_comment')]

    day = str(datetime.strftime(data['start'], "%d.%m.%Y %H:%M:%S")).split(' ')

    message_text = text(emojize(f'Started working at {day[0]} in {day[1]} 🥺',
                                language='alias') + "\nPush the button, after work")

    await bot.send_message(callback.from_user.id, message_text, reply_markup=inkb.add(*button))
    await callback.answer()
    await Work.next()


async def add_comment_work(callback: types.CallbackQuery, state: FSMContext):
    # async with state.proxy() as data:
    #     data['category'] = callback.data

    await bot.delete_message(callback.from_user.id, callback.message.message_id)

    await bot.send_message(callback.from_user.id, "Leave a comment, please!")
    await callback.answer()
    await Work.next()


async def end_working_with_comment(message: types.Message, state: FSMContext):

    await bot.delete_message(message.from_user.id, message.message_id-1)

    date = datetime.now().replace(microsecond=0)
    day = date.strftime("%d.%m.%Y %H:%M:%S").split(' ')

    async with state.proxy() as data:
        data['comment'] = message.text
        data['end'] = date

    start_date = data["start"].strftime("%d.%m.%Y %H:%M:%S").split(' ')

    message_text = text(emojize(f'Started working on the problem «{bold(data["category"])}» at {start_date[0]} in {start_date[1]} 🥺', language='alias') + '\n' +
                        emojize(f'Finished working at {day[0]} in {day[1]} 🎉', language='alias'))

    await bot.send_message(
        message.from_user.id,
        message_text,
        parse_mode=ParseMode.MARKDOWN
    )

    await postgresql.sql_entries_add({'uid': message.from_user.id,
                                      'category': data['category'],
                                      'time': (data['end'] - data['start']).seconds,
                                      'date': day[0],
                                      'comment': data['comment']})
    await state.finish()


async def end_working_without_comment(callback: types.CallbackQuery, state: FSMContext):

    await bot.delete_message(callback.from_user.id, callback.message.message_id)

    date = datetime.now().replace(microsecond=0)
    day = date.strftime("%d.%m.%Y %H:%M:%S").split(' ')

    async with state.proxy() as data:
        data['comment'] = 'без комментария'
        data['end'] = date

    start_date = data["start"].strftime("%d.%m.%Y %H:%M:%S").split(' ')

    message_text = text(emojize(f'Started working on the problem «{bold(data["category"])}» at {start_date[0]} in {start_date[1]} 🥺', language='alias') + '\n' +
                        emojize(f'Finished working at {day[0]} in {day[1]} 🎉', language='alias'))

    await bot.send_message(
        callback.from_user.id,
        message_text,
        parse_mode=ParseMode.MARKDOWN
    )

    await postgresql.sql_entries_add({'uid': callback.from_user.id,
                                      'category': data['category'],
                                      'time': (data['end'] - data['start']).seconds,
                                      'date': day[0],
                                      'comment': data['comment']})
    await state.finish()
    await callback.answer()


async def over_work():
    df = await postgresql.sql_work_sum()
    for user in df:
        overWorkTime = time.strftime("%H:%M:%S", time.gmtime(user['time'] - user['daily_work_rate']))
        await bot.send_message(user['uid'], f"Hello! It's time to rest, you've reworked {overWorkTime}")


def register_handlers_clients(dp: Dispatcher):
    dp.register_message_handler(welcome, commands=["start"])

    dp.register_callback_query_handler(start_meeting, Text(equals='Meet', ignore_case=True), state=None)
    dp.register_callback_query_handler(end_meeting, Text('finish_meet'), state=Meet.start)

    dp.register_callback_query_handler(start_working, Text(equals='Work', ignore_case=True), state=None)
    dp.register_callback_query_handler(start_working_2, Text(startswith='job~', ignore_case=True), state=Work.start)
    dp.register_callback_query_handler(add_comment_work, Text(equals='add_comment', ignore_case=True), state=Work.category)
    dp.register_message_handler(end_working_with_comment, content_types=['text'], state=Work.comment)
    dp.register_callback_query_handler(end_working_without_comment, Text(equals='finish_work', ignore_case=True), state=Work.category)

    dp.register_message_handler(menu, commands=["menu"])
    dp.register_callback_query_handler(menu, Text(equals='menu', ignore_case=True))

    dp.register_callback_query_handler(clients_settings, Text(equals='settings', ignore_case=True))
