import asyncio

from aiogram.utils import executor
from create_bot import dp
from data_base import postgresql

from handlers import clients, others, categories
from schedule_clients import schedule_run


async def on_startup(_):
    postgresql.sql_start()
    asyncio.create_task(schedule_run())
    print("Запустился!")


clients.register_handlers_clients(dp)
categories.register_handlers_clients(dp)
others.register_handlers_clients(dp)


if __name__ == "__main__":
    # start bot
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)

