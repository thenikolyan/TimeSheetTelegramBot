import time

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import ParseMode
from aiogram.utils.markdown import bold

from data_base import postgresql
from aiogram.dispatcher.filters.state import State, StatesGroup

from create_bot import bot


class NameSpaceToAdd(StatesGroup):
    new_name = State()


class NameSpace(StatesGroup):
    last_name = State()
    new_name = State()


class ChangeTime(StatesGroup):
    time = State()


async def add_category(callback: types.CallbackQuery, state=None):
    # state
    await state.finish()
    await NameSpaceToAdd.new_name.set()

    await bot.delete_message(callback.from_user.id, callback.message.message_id)

    async with state.proxy() as data:
        data['uid'] = callback.from_user.id

    inkb = types.InlineKeyboardMarkup(row_width=2)
    cancel = types.InlineKeyboardButton(text='Cancel', callback_data='cancel')

    await bot.send_message(callback.from_user.id,
                           'Enter category name, please!',
                           reply_markup=inkb.add(cancel))
    await callback.answer()


async def add_category_2(message: types.Message, state: FSMContext):
    await message.delete()

    await bot.delete_message(message.from_user.id, message.message_id-1)

    async with state.proxy() as data:
        data['new_name'] = message.text

    await postgresql.sql_user_category_add(
        {'uid': data['uid'], 'category': data['new_name']})

    await state.finish()

    await bot.send_message(message.from_user.id,
                           f'Category «{bold(data["new_name"])}» successful saved!',
                           parse_mode=ParseMode.MARKDOWN)


async def del_category(callback: types.CallbackQuery, state: FSMContext):

    await state.finish()
    await bot.delete_message(callback.from_user.id, callback.message.message_id)

    categories = await postgresql.show_categories(callback.from_user.id)

    inkb = types.InlineKeyboardMarkup(row_width=2)
    button = []

    for item in categories:
        button.append(types.InlineKeyboardButton(text=item['category'], callback_data='del~' + item['category']))
    cancel = types.InlineKeyboardButton(text='Cancel', callback_data='cancel')
    await bot.send_message(callback.from_user.id, 'Choose category name, please!', reply_markup=inkb.add(*button).add(cancel))
    await callback.answer()


async def del_category_2(callback: types.CallbackQuery):

    await bot.delete_message(callback.from_user.id, callback.message.message_id)
    if callback.data != 'cancel':
        data = callback.data.split('~')[1]
        await postgresql.sql_user_category_del(
            {'uid': callback.from_user.id, 'category': f'{data}'})
        await bot.send_message(callback.from_user.id,
                               f'Category «{bold(data)}» successful deleted!',
                               parse_mode=ParseMode.MARKDOWN)
        await callback.answer()


async def rename_category(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await NameSpace.last_name.set()

    categories = await postgresql.show_categories(callback.from_user.id)
    await bot.delete_message(callback.from_user.id, callback.message.message_id)
    inkb = types.InlineKeyboardMarkup(row_width=2)
    button = []

    for item in categories:
        button.append(types.InlineKeyboardButton(text=item['category'], callback_data='re~' + item['category']))
    cancel = types.InlineKeyboardButton(text='Cancel', callback_data='cancel')
    await bot.send_message(callback.from_user.id, 'Choose category what do you wish change, please!',
                           reply_markup=inkb.add(*button).add(cancel))
    await callback.answer()


async def rename_category_2(callback: types.CallbackQuery, state: FSMContext):
    if callback.data != 'cancel':
        await bot.send_message(callback.from_user.id, 'Choose new name, please!')
        async with state.proxy() as data:
            data['last_name'] = callback.data
        await callback.answer()

        await NameSpace.next()


async def rename_category_3(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['new_name'] = message.text

    await postgresql.sql_user_category_rename(
        {'uid': message.from_user.id, 'last_name': f'{data["last_name"]}', 'new_name': f'{data["new_name"]}'})
    await bot.send_message(message.from_user.id,
                           f'Category «{data["last_name"]}» has been successfully replaced by «{data["new_name"]}»!',
                           parse_mode=ParseMode.MARKDOWN)
    await state.finish()


async def change_time_of_work(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await ChangeTime.time.set()
    await bot.delete_message(callback.from_user.id, callback.message.message_id)

    inkb = types.InlineKeyboardMarkup(row_width=2)

    message_text = 'Please, enter the time in one of the specified formats\n\n'+\
                   '- «12»\n' + '- «12:00»\n' + '- «12:00:00»\n\n' +\
                   'The number of hours must be greater than -1 and less than 24\n' + \
                   'The number of minutes must be greater than -1 and less than 60\n' + \
                   'The number of hours must be greater than -1 and less than 60\n'

    await bot.send_message(callback.from_user.id,
                           message_text,
                           reply_markup=inkb.add(types.InlineKeyboardButton(text='Menu', callback_data='Menu'),
                                                 types.InlineKeyboardButton(text='Cancel', callback_data='cancel')))


async def change_time_of_work_2(message: types.Message, state: FSMContext):
    await bot.delete_message(message.from_user.id, message.message_id-1)
    await bot.delete_message(message.from_user.id, message.message_id)
    if len(message.text) <= 2:
        try:
            hou = time.strptime(message.text, '%H')[3]
            async with state.proxy() as data:
                data['time'] = hou * 3600
                data['uid'] = message.from_user.id

            await postgresql.sql_change_time_of_work(data)

            await bot.send_message(message.from_user.id, f"You've successfully changed the time on {message.text}!")
        except ValueError:
            await change_time_of_work(message, state)
    elif len(message.text) == 5:
        try:
            hou, min = time.strptime(message.text, '%H:%M')[3:5]

            async with state.proxy() as data:
                data['time'] = hou * 3600 + min * 60
                data['uid'] = message.from_user.id

            await postgresql.sql_change_time_of_work(data)

            await bot.send_message(message.from_user.id, f"You've successfully changed the time on {message.text}!")
        except ValueError:
            await change_time_of_work(message, state)
    elif len(message.text) == 8:
        try:
            hou, min, sec = time.strptime(message.text, '%H:%M:%S')[3:6]
            async with state.proxy() as data:
                data['time'] = hou * 3600 + min * 60 + sec
                data['uid'] = message.from_user.id

            await postgresql.sql_change_time_of_work(data)

            await bot.send_message(message.from_user.id, f"You've successfully changed the time on {message.text}!")

        except ValueError:
            await change_time_of_work(message, state)
    else:
        await change_time_of_work(message, state)



async def cancel(callback: types.Message,  state: FSMContext):
    current_state = await state.get_state()
    await bot.delete_message(callback.from_user.id, callback.message.message_id)
    if current_state is None:
        return
    await state.finish()
    await callback.answer()


def register_handlers_clients(dp: Dispatcher):
    dp.register_callback_query_handler(add_category, Text(equals='Add category', ignore_case=True), state='*')
    dp.register_message_handler(add_category_2, content_types=['text'], state=NameSpaceToAdd.new_name)

    dp.register_callback_query_handler(del_category, Text(equals='Delete category', ignore_case=True), state='*')
    dp.register_callback_query_handler(del_category_2, Text(startswith='del~', ignore_case=True))

    dp.register_callback_query_handler(rename_category, Text(equals='Rename caterory', ignore_case=True), state='*')
    dp.register_callback_query_handler(rename_category_2, Text(startswith='re~', ignore_case=True), state=NameSpace.last_name)
    dp.register_message_handler(rename_category_3, content_types=['text'], state=NameSpace.new_name)

    dp.register_callback_query_handler(cancel, Text(equals='cancel', ignore_case=True), state='*')

    dp.register_callback_query_handler(change_time_of_work, Text(equals='Change time of work', ignore_case=True), state='*')
    dp.register_message_handler(change_time_of_work_2, content_types=['text'], state=ChangeTime.time)
