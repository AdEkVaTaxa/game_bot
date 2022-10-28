from asyncio import sleep, create_task

from aiogram import Router, Bot
from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest
from aiogram.dispatcher.fsm.context import FSMContext

from .state import Games
from .util.keyboard import inline_keyboard
from .util.minor_func import (
	main_menu, 
	games_menu, 
	games_data,
	dice_win, 
	warnings, 
	deposit, 
	referral_perccent
)
from text import games_text, emojis, winning_amount
from models.user import get_user_balance
from models.balance import balance_update
from redis import add_redis_data
from database import get_db

router = Router()

@router.callback_query(state=Games.selection_game)
async def selection_games(callback: types.CallbackQuery, state: FSMContext):
	base_menu_state: bool = False
	state_data: dict = await state.get_data()
	bid: int = state_data.get("bid")
	s_emoji: str = callback.data if emojis.get(callback.data) is not None else state_data.get("emoji")

	if callback.data == "base_menu" or base_menu_state:
		await state.clear()
		await main_menu(callback.message, state, True)

	elif s_emoji in ("slots", "game_dice", "basketball", "darts", "bouling", "football"):
		await state.clear()
		await state.update_data(bid=bid)
		buttons = inline_keyboard({
				"💎 Играть на": "balance",
				"🍬 Демо": "demo_balance",
				"< Меню": "games_menu",
			}, "", row=2
		)

		await callback.message.edit_text(f"{games_text.get(s_emoji)}\n \nВыберите режим:", reply_markup=buttons)
		await state.update_data(emoji=s_emoji)

		if s_emoji == "game_dice":
			await state.set_state(Games.game_dice)
		else:
			await state.set_state(Games.bet)


@router.callback_query(state=Games.bet)
async def bet(callback: types.CallbackQuery, bot: Bot, state: FSMContext, update: bool = True, play: bool = True):
	if callback.data == "games_menu":
		await games_menu(callback, state)

	elif callback.data == "top_up_balance":
		await state.clear()
		await deposit(callback, state)

	elif callback.data == "balance_selection":
		await state.set_state(Games.selection_game)
		await selection_games(callback, state)

	elif callback.data == "play" and play:
		await game_start(callback, bot, state)

	elif callback.data == "dice_menu":
		await state.set_state(Games.game_dice)
		await game_dice(callback, bot, state)

	else:
		bid, balance_type, symb, balance, emoji = await games_data(callback, state)
		if balance < 10:
			await warnings(callback, "insufficient_funds")
			return 

		old_bid: int = bid

		if callback.data == "add_bet" or callback.data == "take_bet":
			bid = (bid + 10 if bid + 10 <= balance and bid < 5000 else bid) if callback.data == 'add_bet' else (bid - 10 if bid > 10 else 10)

		elif callback.data == "min" or callback.data == "max":
			bid = (10) if callback.data == "min" else (5000 if balance >= 5000 else balance)


		elif callback.data == "double_bet":
			bid = bid * 2 if bid * 2 <= 5000 and balance >= bid * 2 else bid

		buttons = {
			"-": "take_bet",
			f"{bid} {symb}": "d",
			"+": "add_bet",
			"Мин.": "min",
			"Удвоить": "double_bet",
			"Макс.": "max",
		}
		
		if emoji is None or emoji != "game_dice":
			buttons["< Назад"] =  "balance_selection"
			buttons["Играть"] = "play"
		
		elif  emoji == "game_dice":
			buttons['< Назад'] = "dice_menu"

		buttons = inline_keyboard(buttons, "", row=3)

		try:
			if update:
				await callback.message.edit_text(
					f"{'Баланс:' if balance_type == 'balance' else 'Демо:'} <b>{balance}</b> {symb}\n\nОтправь или выбери размер ставки:",
					reply_markup=buttons,
					parse_mode="html"
				)

			else:
				await callback.message.answer(
					f"{'Баланс:' if balance_type == 'balance' else 'Демо:'} <b>{balance}</b> {symb}\n\nОтправь или выбери размер ставки:",
					reply_markup=buttons,
					parse_mode="html"
				)
		except TelegramBadRequest:
			print("Собщения не модифиципровано")

		await state.update_data(user_balance=balance, balance_type=balance_type, bid=bid)


@router.callback_query(state=Games.game_dice,)
async def game_dice(callback: types.CallbackQuery, bot: Bot, state: FSMContext, update: bool = True, play: bool = True):
	state_data = await state.get_data()

	if callback.data == "games_menu":
		await games_menu(callback, state)

	elif callback.data == "top_up_balance":
		await state.clear()
		await deposit(callback, state)

	elif callback.data == "play" and play:
		if state_data.get("dice_selection") is not None:
			await game_start(callback, bot, state)

		else:
			await warnings(callback)

	elif callback.data == "balance_selection":
		await state.set_state(Games.selection_game)
		await selection_games(callback, state)

	elif callback.data == "bet":
		await state.set_state(Games.bet)
		await bet(callback, bot, state, True, True)

	else:
		bid, balance_type, symb, balance, _ = await games_data(callback, state)
		if balance < 10:
			await warnings(callback, "insufficient_funds")
			return 
		
		b_data = callback.data

		buttons = [[InlineKeyboardButton(text=f"Сумма ставки {bid} {symb}", callback_data='bet')], 
			[InlineKeyboardButton(text=f"{f'•{i}•' if str(i) == b_data else i}", callback_data=i) for i in range(1, 7)],
			[InlineKeyboardButton(text=f"{f'•{i}•' if b_data == i else i}", callback_data=i) for i in ['1-2','3-4','5-6']],
			[
				InlineKeyboardButton(text="Четное" if b_data != 'even' else '•Четное•', callback_data="even"), 
				InlineKeyboardButton(text="Нечетное" if b_data != 'odd' else '•Нечетное•', callback_data="odd")
			],
			[
				InlineKeyboardButton(text="< Назад", callback_data="balance_selection"),
				InlineKeyboardButton(text="Играть", callback_data="play"),
			]
		]

		if update:
			try:
				await callback.message.edit_text(
					f"{'Баланс:' if balance_type == 'balance' else 'Демо:'} <b>{balance}</b> {symb}\n\nОтправь сумму ставки и выбери исход:", 
					reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="html"
				)
			except TelegramBadRequest:
				print("Собщения не модифиципровано")

		else:
			await callback.message.answer(
				f"{'Баланс:' if balance_type == 'balance' else 'Демо:'} <b>{balance}</b> {symb}\n\nОтправь сумму ставки и выбери исход:", 
				reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="html"
			)

		if callback.data in ['1','2','3','4','5','6','1-2','3-4','5-6','odd','even']:
			await state.update_data(dice_selection=callback.data)

		await state.update_data(user_balance=balance, balance_type=balance_type, bid=bid)


async def game_start(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
	db = get_db()
	state_data: dict = await state.get_data()
	bid: int = state_data.get("bid")
	emoji: str = state_data.get('emoji')
	user_tg_id: str = str(callback.message.chat.id)
	balance_type: str = state_data.get("balance_type")
	message: types.Message = await callback.message.edit_text("🍀 Удачи!")
	dice_result: int = await bot.send_dice(callback.message.chat.id, emoji=emojis[emoji])
	winning: float = winning_amount.get(emoji)

	await create_task(referral_perccent(user_tg_id, bid, balance_type))
	await sleep(2)

	redis_data = {}
	all_user_balance = await get_user_balance(user_tg_id, db=db)

	if balance_type == "demo_balance":
		user_balance = all_user_balance[0]
		redis_data = {"balance": all_user_balance[1].balance}

	elif balance_type == "balance":
		user_balance = all_user_balance[1]
		redis_data = {"demo_balance": all_user_balance[0].balance}

	text = "❌ К сожалению вы проиграли"

	if emoji == "game_dice":
		winning: float = await dice_win(dice_result.dice.value, state_data.get('dice_selection'))

	elif emoji != "game_dice":
		winning = winning.get(dice_result.dice.value)

	if winning is not None:
		winning_percent = winning
		winning = int((bid * winning) * 100)
		text = f"✅️ Вы выиграли {winning} {'🍬' if balance_type == 'demo_balance' else '💎'}"
		winning = int(winning + user_balance.balance)
		winning -= bid
		user_balance.balance = winning

	else:
		user_balance.balance = int(user_balance.balance - bid)

	redis_data[balance_type] = user_balance.balance

	await balance_update(user_balance, db)
	await add_redis_data(f"{user_tg_id}__balance", redis_data)
	await message.edit_text(text)
	db.close()

	if emoji == "game_dice":
		await state.update_data(dice_selection=None)
		await game_dice(callback, bot, state, False, False)

	else:
		await bet(callback, bot, state, update = False, play = False)
