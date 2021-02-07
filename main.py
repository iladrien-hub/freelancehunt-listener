import asyncio
import json
import logging
import threading

import colorlog
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.markdown import hide_link, hbold

import settings
from fparser import FreelanceHuntParser

with open(settings.SETTINGS, "r") as fp:
    SETTINGS = json.load(fp)

loop = asyncio.get_event_loop()
BOT = Bot(SETTINGS["bot"], parse_mode="HTML")
DISPATCHER = Dispatcher(BOT, loop=loop)
PARSER = None


def save_settings():
    with open(settings.SETTINGS, "w") as fp:
        json.dump(SETTINGS, fp, indent=2, sort_keys=True)


async def on_startup(dp):
    logging.info("Bot started.")


@DISPATCHER.message_handler(commands=['settimeout'])
async def cmd_settimeout(message: types.Message):
    try:
        if message.chat.id != SETTINGS["admin"]:
            raise PermissionError()
        timeout = int(message.get_args())
        if timeout < 0:
            raise ValueError()
        SETTINGS["timeout"] = timeout
        save_settings()
        PARSER.set_timeout(timeout)
        await message.answer(f"Timeout set to {timeout} seconds.")
    except ValueError:
        await message.answer("Enter a valid count of seconds!")
    except PermissionError:
        await message.answer("You have no rights for this action.")


async def on_new_project(project):
    logging.info(project)
    text = f"{hide_link(project['url'])}" \
           f"{hbold(project['name'])} " \
           f"{hbold(project['budget'])}\n\n" \
           f"{project['description']}\n\n "
    await BOT.send_message(chat_id=SETTINGS["admin"], text=text)


if __name__ == '__main__':
    colorlog.basicConfig(format=settings.LOGGING_FORMAT, level=logging.INFO, datefmt="%H:%M:%S")
    logging.info("Starting app...")
    PARSER = FreelanceHuntParser(SETTINGS["categories"], eventloop=loop, on_project_listener=on_new_project)
    PARSER.set_timeout(SETTINGS["timeout"])
    parsing_thread = threading.Thread(target=PARSER.listen, name="ParsingThread")
    parsing_thread.start()
    logging.info("Starting bot...")
    executor.start_polling(DISPATCHER, on_startup=on_startup)
