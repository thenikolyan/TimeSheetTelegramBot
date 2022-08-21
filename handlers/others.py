from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext


async def cancel(message: types.Message,  state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.answer('Finish previous action')


def register_handlers_clients(dp: Dispatcher):
    dp.register_message_handler(cancel, commands="quit", state='*')
