from aiogram import Bot, Dispatcher
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import token
import logging

storage = MemoryStorage()

bot = Bot(token=token)
dp = Dispatcher(bot, storage=storage)

logging.basicConfig(level=logging.INFO)
dp.middleware.setup(LoggingMiddleware())
