from aiogram import executor
from dispatcher import dp
from dispatcher import config
import handlers

from db import DBh
db = DBh(database=config.DATABASE, user=config.USER, password=config.PASSWORD)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)