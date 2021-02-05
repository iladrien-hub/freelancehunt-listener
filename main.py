import asyncio
import logging
import threading
import colorlog

from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.markdown import hbold, hide_link

import settings
from fparser import FreelanceHuntParser

loop = asyncio.get_event_loop()
BOT = Bot(settings.BOT_TOKEN, parse_mode="HTML")
DISPATCHER = Dispatcher(BOT, loop=loop)


async def on_new_project(project):
    logging.info(project)
    text = f"{hide_link(project['url'])}" \
           f"{hbold(project['name'])} " \
           f"{hbold(project['budget'])}\n\n" \
           f"{project['description']}\n\n "
    await BOT.send_message(chat_id=settings.ADMIN_ID, text=text)


async def on_startup(dp):
    logging.info("Bot started.")


@DISPATCHER.message_handler(commands=['clear'])
async def cmd_start(message: types.Message):
    await message.answer("Обработчик команды /clear")


if __name__ == '__main__':
    colorlog.basicConfig(format=settings.LOGGING_FORMAT, level=logging.INFO, datefmt="%H:%M:%S")
    logging.info("Starting app...")
    parser = FreelanceHuntParser(settings.CATEGORIES, eventloop=loop, on_project_listener=on_new_project)
    parsing_thread = threading.Thread(target=parser.listen, name="ParsingThread")
    parsing_thread.start()
    logging.info("Starting bot...")
    executor.start_polling(DISPATCHER, on_startup=on_startup)
