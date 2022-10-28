from typing import Union
from asyncio import sleep

from aiogram import Bot, types
from aiogram.dispatcher.fsm.context import FSMContext
from aiohttp import ClientSession
from sqlalchemy.orm import Session

from ..state import Games, Admin, Pay
from .keyboard import inline_keyboard
from redis import redis_hash, get_redis_data
from schemas import UserData
from settings import settings
from database import get_db
from models.balance import get_bet_amount
from models.user import (
	create_referal, 
	get_user_balance, 
	get_user_tg_id, 
	get_user_referal, 
	user_list, 
	get_referal_user_id,
	get_ref_code
)

async def check_bid(state: FSMContext) -> int:
	state_data = await state.get_data()
	bid = state_data.get('bid')
	if bid is None:
		bid = 10

	return int(bid)


async def referal(text: str, referal_tg_id: str, db: Session) -> None:
	ref_code = text.split(" ")[-1]
	if ref_code != "/start":
		user_data = await get_ref_code(db, ref_code)

		if user_data is not None:
			print("I WORK")
			await create_referal(user_data.id, referal_tg_id, db)
	
	db.close()


async def main_menu(message: types.Message, state: FSMContext, change: bool = False):
	keyboard = {
		"🎲 Игры": "games",
		"💎 Депозит": "top_up_balance",
		"👫 Рефералы": "referal_data",
	}

	if message.chat.id in settings.ADMIN_LIST:
		keyboard['🗄 Админ панель'] = "admin"

	keyboard = inline_keyboard(keyboard, "", 2)
	user_tg_id = str(message.chat.id)
	user_balance = await get_redis_data(f"{user_tg_id}__balance", 
		pickle_dumps=True, 
		cache_update=["user_balance"], 
		one_args={"user_tg_id": user_tg_id}
	)

	text = f"Баланс: <b>{user_balance['balance']}</b> 💎 \n \nДемо: <b>{user_balance['demo_balance']}</b> 🍬\n \nВыберите действие:"
	await state.update_data(user_balance = text)

	if change:
		await message.edit_text(text, reply_markup=keyboard)
	else:
		await message.answer(text, reply_markup=keyboard)


async def games_menu(callback: types.CallbackQuery, state: FSMContext):
	state_data = await state.get_data()
	text = state_data.get("user_balance")
	
	if text is None:
		user_tg_id = str(callback.message.chat.id)
		user_balance = await get_redis_data(f"{user_tg_id}__balance", 
			pickle_dumps=True, 
			cache_update=["user_balance"], 
			one_args={"user_tg_id": user_tg_id}
		)
		text = f"Баланс: <b>{user_balance['balance']}</b> 💎 \n \nДемо: <b>{user_balance['demo_balance']}</b> 🍬\n \nВыберите действие:"
		await state.update_data(user_balance = text)
	
	buttons = inline_keyboard({
		"🎰 Слоты": "slots",
		"🎲 Кубик": "game_dice",
		"🏀 Баскет": "basketball",
		"🎯 Дартс": "darts",
		"🎳 Боулинг": "bouling",
		"⚽️ Футбол": "football",
		"< Назад": "base_menu"
		}, "", row=3
	)

	await callback.message.edit_text(text, reply_markup=buttons)
	await state.set_state(Games.selection_game)


async def deposit(callback: types.CallbackQuery, state: FSMContext):
	buttons = inline_keyboard({"📥 Пополнить": "replenish", "📤 Вывести": "withdrawal", "< Меню": "base_menu"}, "", row=2)

	text: str = f"""💸 Мой кошелек

Курс: 100 💎 = 70 ₽\n \nМинимальная сумма вывода {settings.MINIMUM_WIDTH_AMOUNT} 💎"""
	
	await state.update_data(withdrawal_type="balance")
	await state.set_state(Pay.select)
	await callback.message.edit_text(text, reply_markup=buttons)


async def referal_menu(callback: types.CallbackQuery, state: FSMContext, bot_data: str):
	db = get_db()
	user_tg_id = str(callback.message.chat.id)
	buttons = inline_keyboard({"📤 Вывести": "withdrawal", "< Назад": "base_menu", }, "", row=1)

	user_data = await get_user_tg_id(user_tg_id, db)
	referal_data = await get_user_referal(str(user_data.id), db)
	bet_amount = await get_bet_amount(user_data.id, db)

	await state.update_data(withdrawal_type="referal_balance")
	await state.set_state(Pay.select)
	await callback.message.edit_text(f"""👬 Реферальная программа

Приглашайте своих друзей и зарабатывайте 15% от всех их ставок, независимо от того, выиграют или проиграют! 

• Приглашено: {len(referal_data)}
• Сумма ставок: {bet_amount.bet_amount if bet_amount is not None else 0} 💎

Пригласительная ссылка: t.me/{bot_data.username}?start={user_data.user_referal_code}""", reply_markup=buttons)


async def games_data(callback: types.CallbackQuery, state: FSMContext):
	state_data = await state.get_data()
	bid = await check_bid(state)
	balance_type = state_data.get("balance_type")
	emoji = state_data.get("emoji")
	
	if balance_type is None:
		balance_type = callback.data

	user_tg_id = str(callback.message.chat.id)
	user_balance = await get_redis_data(f"{user_tg_id}__balance", 
		pickle_dumps=True, 
		cache_update=["user_balance"], 
		one_args={"user_tg_id": user_tg_id}
	)
	symb = "💎" if balance_type == "balance" else "🍬"
	balance = f"{user_balance['balance']}" if balance_type == "balance" else f"{user_balance['demo_balance']}"

	if bid > int(balance):
		bid = int(balance)

	return bid, balance_type, symb, int(balance), emoji


async def dice_win(dice_value: int, dice_selection: str,):
	if len(dice_selection) == 1 and int(dice_selection) == dice_value:
		return 0.05

	elif dice_selection in ["odd", "even"]:
		valuee_res = "even" if dice_value % 2 == 0 else "odd"
		return 0.018 if valuee_res == dice_selection else None

	else:
		for i in dice_selection.split('-'):
			if int(i) == dice_value:
				return 0.027

	return None


async def warnings(callback: types.CallbackQuery, warning_type:str = "game_dice"):
	await callback.message.delete()

	if warning_type == "game_dice":
		text = "❌ Вы не выбрали исход для ставки"
		buttons = inline_keyboard({"ok": "warnings"}, "", row=1)
	
	elif warning_type == "insufficient_funds":
		text = "❌ Для игры необходимо иметь не менее 10 на балансе"
		buttons = inline_keyboard({"💰 Пополнить баланс": "top_up_balance", "< Назад" : "balance_selection"}, "", row=1)

	await callback.message.answer(text, reply_markup=buttons)


async def admin_panel(message: types.Message, state: FSMContext, update: bool = True):
	text = "Welcome to Админ панель 💩"
	buttons = inline_keyboard({
			"🔫 Блокировка пользователей": "user_blocking",
			"✉️ Рассылка сообщений": "broadcast",
			"📤 Заявки на вывод": "withdrawal",
			"< Меню": "base_menu"
		}, "", row=1)

	await state.set_state(Admin.admin_panel)
	
	if update:
		await message.edit_text(text, reply_markup=buttons)
	else:
		await message.answer(text, reply_markup=buttons)


async def broadcast(message: str, bot: Bot):
	users = await user_list()

	for user in users:
		await bot.send_message(user.user_tg_id, message)


async def referral_perccent(user_tg_id: str, bet_amount: int, balance_type: str) -> None:
	if balance_type == "balance":
		db = get_db()
		user_id: int = await get_referal_user_id(user_tg_id, db)

		if user_id is not None:
			user_bet_amount = await get_bet_amount(user_id, db)
			user_bet_amount.bet_amount += (bet_amount / 100) * 0.6
			db.add(user_bet_amount)
			db.commit()

		db.close()
