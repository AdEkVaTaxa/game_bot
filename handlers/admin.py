from typing import Union
from asyncio import sleep, create_task

from aiogram import Router, Bot
from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.dispatcher.fsm.context import FSMContext

from .util.minor_func import main_menu, broadcast, admin_panel
from .state import Admin
from .util.keyboard import inline_keyboard
from redis import get_redis_data, add_redis_data
from models.user import get_user_tg_id, get_user_balance
from models.balance import all_withdrawals, withdrawals_id, get_bet_amount
from database import get_db

router = Router()


@router.callback_query(state=Admin.admin_panel)
async def admin_action(callback: types.CallbackQuery, state: FSMContext):
	if callback.data == "base_menu":
		await state.clear()
		await main_menu(callback.message, state, True)

	elif callback.data == "broadcast":
		text = "Напишите текст сообщения (Длина текста не менее 3 символов)"
		await state.set_state(Admin.broadcast)

		await callback.message.edit_text(text)

	elif callback.data == "user_blocking":
		text = "Для блокировки пришлите мне Telegram id пользователя"
		await state.set_state(Admin.user_block)

		await callback.message.edit_text(text)

	elif callback.data == "withdrawal":
		withdrawals = await all_withdrawals()
		await state.set_state(Admin.withdrawal_list)

		for entry in withdrawals:
			text = f"Монета: {entry.coin}\n \nАдресс:\n{entry.adress_data}\n \nСумма вывода: {entry.amount} 💎\n \nВывод с {'Рефералки' if entry.referal_balance else 'Баланса'}"
			buttons = inline_keyboard({"Подтвердить": f'{entry.id}__confirm', "Удалить": f'{entry.id}__delete', "< Назад": "base_menu"}, "", 1)
			await callback.message.answer(text, reply_markup=buttons)


@router.message(lambda message: len(message.text) > 2, state=Admin.broadcast)
async def broadcast_message(message: types.Message, bot: Bot, state: FSMContext):
	create_task(broadcast(message.text, bot,))
	
	await message.answer("Процесс запущен")
	await state.clear()
	await admin_panel(message, state, False)


@router.message(state=Admin.user_block)
async def user_block(message: types.Message, state: FSMContext):
	user = await get_user_tg_id(str(message.text))
	text = "Пользователь с таким Telegram id не найден"

	if user is not None:
		user.freeze = True
		user.update()
		text = "Пользователь заблокирован"

	await message.answer(text)
	await state.clear()
	await admin_panel(message, state, False)


@router.callback_query(state=Admin.withdrawal_list)
async def withdrawal_list(callback: types.CallbackQuery, state: FSMContext):
	if callback.data == "base_menu":
		await state.clear()
		await main_menu(callback.message, state, True)

	else:
		db = get_db()
		entry_id, status = int(callback.data.split("__")[0]), callback.data.split("__")[1]
		withdrawals = await withdrawals_id(entry_id, db)
		user_tg_id = withdrawals.user_tg_id

		if status == "delete":
			if withdrawals.referal_balance:
				bet = await get_bet_amount(withdrawals.user_id, db)
				bet.bet_amount += withdrawals.amount
				bet.update(db)

			else:
				user_balance = await get_user_balance(user_tg_id, db=db)
				user_balance[1].balance += withdrawals.amount
				user_balance[1].update(db)
				await add_redis_data(f"{user_tg_id}__balance", {"balance": user_balance[1].balance, "demo_balance": user_balance[0].balance})


		db.delete(withdrawals)
		db.commit()
		db.close()
		
		await callback.message.delete()
