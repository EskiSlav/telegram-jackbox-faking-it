import asyncio
import logging
import logging.config
import sys
from os import getenv
from random import choice
# from pprint import pprint
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from sqlite3 import OperationalError
from aiogram import F

from models import ActionCallback
from keyboards import join_game_builder, game_stage1_q1_builder, game_stage1_q2_builder, game_stage1_q3_builder
from db import Database
from logging_config import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)

# Bot token can be obtained via https://t.me/BotFather
TOKEN = getenv("BOT_TOKEN")

# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()
# Initialize Bot instance with default bot properties which will be passed to all API calls
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
db = Database()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    user = message.from_user
    try:
        db.create_user(
            id=user.id,
            username=user.username,
            last_name=user.last_name,
            is_bot=user.is_bot)
        await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!\nNow you can play games in the chat!")
    except OperationalError as e:
        await message.answer(f"Error, please try again later")


@dp.message(Command('game'))
async def command_game_handler(message: Message) -> None:
    """_summary_

    Args:
        message (Message): _description_
    """
    chat = message.chat
    if db.create_chat(chat.id, chat.title, chat.type, chat.description):
        print("chat was not created")
    logging.info("Created chat")

    
    if (ret := db.create_game(message.chat.id, message.from_user.id, message.message_id)) == 1:
        await message.answer("Error occured")    
    elif ret == 2:
        await message.answer("Game is already started")
        logging.info("Game is already started")
    else:
        await message.answer("Game created. Join the game", reply_markup=join_game_builder.as_markup())
        logging.info("started game")
    
@dp.message(Command('stopgame'))
async def command_game_handler(message: Message) -> None:
    """_summary_

    Args:
        message (Message): _description_
    """
    db.stop_game(message.chat.id)
    await message.answer("Ended Game. Good luck!")


@dp.callback_query(ActionCallback.filter(F.action == 'joingame'))
async def join_game(callback: CallbackQuery) -> None:
    if db.add_user_to_game(callback.from_user.id, callback.message.chat.id):
        await callback.answer(f'Already in game')
    else:
        users = db.get_users_in_game_by_chat_id(callback.message.chat.id)
        msg = 'Game created. Join the game\n ----'
        for user in users:
            msg += f'\n{user[1]}'
        await callback.answer(f'{callback.from_user.username} joined')
        await callback.message.edit_text(msg, reply_markup=join_game_builder.as_markup())
    
@dp.callback_query(ActionCallback.filter(F.action == 'stopgame'))
async def stop_game(callback: CallbackQuery) -> None:
    if not db.get_game_admin(callback.message.chat.id) == callback.from_user.id:
        await callback.answer('Ви не адміністратор цієї гри')
        return
    
    db.stop_game(callback.message.chat.id)
    await callback.answer('Done', show_alert=False)
    await callback.message.edit_text("Ended Game. Good luck!")


@dp.callback_query(ActionCallback.filter(F.action == 'startgame'))
async def start_game(callback: CallbackQuery) -> None:
    admin_id =db.get_game_admin(callback.message.chat.id)
    if not db.get_game_admin(callback.message.chat.id) == callback.from_user.id:
        await callback.answer('Ви не адміністратор цієї гри')
        return
    
    await callback.message.edit_text(callback.message.text + '\nGame started!')
    await callback.message.answer("The first question soon will be sent to participants!\n\nAdmin should continue when everyone is ready.", reply_markup=game_stage1_q1_builder.as_markup())

    users = db.get_users_in_game_by_chat_id(callback.message.chat.id)
    for user in users:
        # if not user[0] == admin_id:
        await bot.send_message(user[0], 'Адміністратор встановлює питання')
    
    print(f'{admin_id=}')
    db.update_user_status(admin_id, 'post_questions')
    await bot.send_message(admin_id, 'Надішліть питання одним повідомленням')
    
@dp.callback_query(ActionCallback.filter(F.action == 'continuegame1'))
async def continue_game(callback: CallbackQuery) -> None:
    if not db.get_game_admin(callback.message.chat.id) == callback.from_user.id:
        await callback.answer('Ви не адміністратор цієї гри')
        return
    
    game_id = db.get_game_id_by_admin_id(callback.from_user.id)
    question_for_user = db.get_random_question(game_id)
    traitors = db.get_traitors_by_game_id(game_id)
    users = db.get_users_in_game(game_id)
    print(users, [t.id for t in traitors])
    for user in users:
        if user[0] not in [t.id for t in traitors]:
            await bot.send_message(user[0], 'Ви звичайний гравець.\n\n' + question_for_user.question)
    db.set_question_as_used(question_for_user.id)

    question_for_traitor = db.get_random_question(game_id)
    # Send message for traitors
    for traitor in traitors:
        await bot.send_message(traitor.id, 'Ви Жулік.\n\n' + question_for_traitor.question)
    db.set_question_as_used(question_for_traitor.id)

    await callback.message.edit_text(callback.message.text, reply_markup=game_stage1_q2_builder.as_markup())

@dp.callback_query(ActionCallback.filter(F.action == 'continuegame2'))
async def continue_game(callback: CallbackQuery) -> None:
    if not db.get_game_admin(callback.message.chat.id) == callback.from_user.id:
        await callback.answer('Ви не адміністратор цієї гри')
        return
    
    game_id = db.get_game_id_by_admin_id(callback.from_user.id)
    question_for_user = db.get_random_question(game_id)
    traitors = db.get_traitors_by_game_id(game_id)
    users = db.get_users_in_game(game_id)

    for user in users:
        if user[0] not in [t.id for t in traitors]:
            await bot.send_message(user[0], 'Ви звичайний гравець.\n\n' + question_for_user.question)
    db.set_question_as_used(question_for_user.id)

    # Send message for traitors
    question_for_traitor = db.get_random_question(game_id)
    for traitor in traitors:
        await bot.send_message(traitor.id, 'Ви Жулік.\n\n' + question_for_traitor.question)
    db.set_question_as_used(question_for_traitor.id)

    await callback.message.edit_text(callback.message.text, reply_markup=game_stage1_q3_builder.as_markup())
    
@dp.callback_query(ActionCallback.filter(F.action == 'endgame'))
async def continue_game(callback: CallbackQuery) -> None:
    if not db.get_game_admin(callback.message.chat.id) == callback.from_user.id:
        await callback.answer('Ви не адміністратор цієї гри')
        return

# TODO
# Continue3 button
# Set picture for the bot
# Test with 2 users 
# write condition for minimal users
# Extract similar parts from continue buttons to separate func
# Add comments to functions


@dp.message()
async def message_handler(message: Message) -> None:
    if db.get_user_status(message.from_user.id) == 'post_questions':
        questions = message.text.split('\n')
        if len(questions) < 6:
            await message.answer('Замало питань, надішліть ще')
            return
        
        game_id = db.get_game_id_by_admin_id(message.from_user.id)
        for question in questions:
            if question == "": # create good empty line filtering or check if telegram does that
                continue 
            db.create_question(question, game_id)
        await message.answer('Питання отримані. Розсилаю учасникам')

        users = db.get_users_in_game(game_id)
        question_for_user = db.get_random_question(game_id)
        traitor = choice(users) # move this to gamestart
        db.set_traitor_in_game(traitor[0], game_id) # move this to gamestart

        for user in users:
            if not user[0] == message.from_user.id or not user[0] == traitor[0]:
                await bot.send_message(user[0], 'Ви звичайний гравець.\n\n' + question_for_user.question)
        db.set_question_as_used(question_for_user.id)
 
        # Send message for traitors
        question_for_traitor = db.get_random_question(game_id)
        await bot.send_message(traitor[0], 'Ви Жулік.\n\n' + question_for_traitor.question)
        db.set_question_as_used(question_for_traitor.id)
        db.update_user_status(message.from_user.id, 'none')

async def main() -> None:
    # And the run events dispatching
    await dp.start_polling(bot)


# def lambda_handler(event, context):
#     """AWS Lambda handler."""
#     asyncio.run(main())

if __name__ == "__main__":
    asyncio.run(main())