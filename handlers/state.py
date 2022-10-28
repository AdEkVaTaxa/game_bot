from aiogram.dispatcher.filters.state import State, StatesGroup


class Games(StatesGroup):
	selection_game = State()
	bet = State()
	game_dice = State()
	selection = State()
	game_start = State()


class Admin(StatesGroup):
	admin_panel = State()
	broadcast = State()
	user_block = State()
	withdrawal_list = State()


class Pay(StatesGroup):
	select = State()
	selection_sum = State()
	select_crypto = State()


class Withdrawal(StatesGroup):
	select_crypto = State()
	crypto_adress = State()
	sum_select = State()
