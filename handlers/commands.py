import asyncio
from time import time

from aiogram import Router, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher.fsm.context import FSMContext

from .util.minor_func import referal, main_menu, games_menu, referal_menu, deposit, admin_panel
from .util.utils import admin_validator
from .util.keyboard import inline_keyboard
from .state import Games, Admin
from models.user import create_user, get_user_tg_id, get_user_balance
from redis import redis_l
from schemas import UserData
from database import get_db

router = Router()

@router.message(commands=["start"])
async def cmd_start(message: Message, bot: Bot, state: FSMContext):
	await message.delete()
	if await state.get_state() is not None:
		await state.clear()

	user_data = message.chat
	user_tg_list = await redis_l("user_registered_list", data_set=False, project_data=True)

	if str(user_data.id) not in user_tg_list:
		db = get_db()
		user_data = UserData(**user_data.dict())
		bot_data = await bot.get_me()

		referal_code = await create_user(user_data, db)
		asyncio.create_task(referal(message.text, user_data.id, db))
		await redis_l("user_registered_list", user_data.id)
		await main_menu(message, state)

	else:
		user = await get_user_tg_id(str(message.chat.id))
		if not user.freeze:
			await main_menu(message, state)

		else:
			await message.answer("Ваша учетная запись заблокирована")


@router.callback_query(state=None)
async def all_callback_query(callback: CallbackQuery, bot: Bot, state: FSMContext):
	func_rules = {"base_menu": {"func": main_menu, "args": (callback.message, state, True)},
		"games": {"func": games_menu, "args": (callback, state)},
		"referal_data": {"func": referal_menu, "args": (callback, state, await bot.get_me())},
		"top_up_balance": {"func": deposit, "args": (callback, state)},
		"admin": {"func": admin_panel, "args": (callback.message, state)}
	}

	func_data = func_rules.get(callback.data)
	if func_data is not None:
		await func_data['func'](*func_data['args'])
