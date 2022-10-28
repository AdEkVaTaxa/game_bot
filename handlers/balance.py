from typing import Union, List
from random import randint

from aiogram import Router, types
from aiogram.dispatcher.fsm.context import FSMContext

from paykassa import PayKassa, sci_currency_rate
from models.balance import create_replenishment, get_bet_amount, create_withdrawals
from models.user import get_user_balance, get_user_tg_id
from settings import settings
from text import coin_list
from database import get_db
from redis import add_redis_data
from .state import Pay, Withdrawal
from .util.utils import check_int, check_sum
from .util.minor_func import main_menu
from .util.keyboard import inline_keyboard

router = Router()

@router.callback_query(state=Pay.select)
async def balance_select(callback: types.CallbackQuery, state: FSMContext):
	if callback.data == "replenish":
		await state.set_state(Pay.selection_sum)
		text = "<b>Пополнение баланса (Минимальная сумма 50 ₽)</b> \n<em>Введите сумму на которую хотите пополнить Ваш баланс или выберете из предложенных</em>"
		buttons = inline_keyboard({
				"100 ₽": 100,
				"250 ₽": 250,
				"500 ₽": 500,
				"1000 ₽": 1000,
				"Назад": "balance_menu"
			},'', row=2)

		await callback.message.edit_text(text, reply_markup=buttons)

	elif callback.data == "withdrawal":
		db = get_db()
		user_tg_id = str(callback.message.chat.id)
		text = f"❌ Минимальная сумма вывода {settings.MINIMUM_WIDTH_AMOUNT} 💎"
		state_data = await state.get_data()
		buttons_list: dict = {}
		
		if state_data['withdrawal_type'] == "referal_balance":
			user_data = await get_user_tg_id(user_tg_id, db)
			balance = await get_bet_amount(user_data.id, db)
			balance = round(balance.bet_amount)

		else:
			balance = await get_user_balance(user_tg_id, 'balance', db)
			balance = balance.balance

		if balance >= settings.MINIMUM_WIDTH_AMOUNT:
			await state.set_state(Withdrawal.select_crypto)
			await state.update_data(balance=balance)
			text = "Выберите криптовалюту"
			for crypto in coin_list:
				buttons_list[crypto] = crypto

		db.close()
		buttons_list['< Меню'] = 'base_menu'
		buttons = inline_keyboard(buttons_list, "", row=2)
		await callback.message.edit_text(text, reply_markup=buttons)

	else:
		await state.clear()
		await main_menu(callback.message, state, True)


@router.callback_query(state=Withdrawal.select_crypto)
async def with_crypto_select(callback: types.CallbackQuery, state: FSMContext):
	if callback.data == "base_menu":
		await state.clear()
		await main_menu(callback.message, state, True)

	else:
		text = "Отправьте мне\n \n• Адресс кошелька \n• Сеть (если есть) \n• Tag или Memo (если есть) \n• Комментарии (не обязательно)\n \nВывод и проверка происходит в ручном режиме\n"
		text += '\n<b>Предупреждения</b>\nНа время вывода средства будут заморожены'

		await state.update_data(withdrawal_crypto=callback.data)
		await state.set_state(Withdrawal.crypto_adress)
		await callback.message.edit_text(text)


@router.message(state=Withdrawal.crypto_adress)
async def with_sum_select(message: types.Message, state: FSMContext):
	await state.update_data(adress_data=message.text)
	text = "Ведите сумму вывода"

	await state.set_state(Withdrawal.sum_select)
	await message.answer(text)


@router.message(check_sum, state=Withdrawal.sum_select)
async def with_create(message: types.Message, state: FSMContext):
	state_data = await state.get_data()
	text = '✅ Заявка на вывод была создана'
	user_tg_id: str = str(message.chat.id)
	db = get_db()
	user_data = await get_user_tg_id(user_tg_id, db)
	with_sum: int = int(message.text)

	await create_withdrawals(user_data.id, user_tg_id, 
		state_data['withdrawal_crypto'],
		state_data['adress_data'],
		int(message.text),
		False if state_data['withdrawal_type'] == 'balance' else True,
		db
	)

	if state_data['withdrawal_type'] == "referal_balance":
		bet = await get_bet_amount(user_data.id, db)
		bet.bet_amount -= with_sum
		bet.update(db)

	elif state_data['withdrawal_type'] == "balance":
		user_balance = await get_user_balance(user_tg_id, db=db)
		user_balance[1].balance -= with_sum
		user_balance[1].update(db)
		await add_redis_data(f"{user_tg_id}__balance", {"balance": user_balance[1].balance, "demo_balance": user_balance[0].balance})


	await message.answer(text)
	await state.clear()
	db.close()
	await main_menu(message, state, False)


@router.callback_query(state=Pay.selection_sum)
async def pay_link_selected_amount(callback: types.CallbackQuery, state: FSMContext):
	if callback.data == "balance_menu":
		await balance_select(callback, state)

	else:
		await select_crypro(callback, state)


@router.message(check_int, state=Pay.selection_sum)
async def pay_link_own_amount(message: types.Message, state: FSMContext):
	await select_crypro(message, state)


async def select_crypro(message: Union[types.Message, types.CallbackQuery], state: FSMContext):
	await state.update_data(amount=int(message.text) if type(message) == types.Message else int(message.data))

	crypto = {i:i for i in coin_list}
	crypto['< Меню'] = 'base_menu'
	buttons = inline_keyboard(crypto,'', row=2)
	text = "выберите криптовалюту для оплаты"

	await state.set_state(Pay.select_crypto)

	if type(message) == types.Message:
		await message.answer(text, reply_markup=buttons)

	else:
		await message.message.edit_text(text, reply_markup=buttons)


@router.callback_query(state=Pay.select_crypto)
async def pay_link(callback: types.CallbackQuery, state: FSMContext):
	if callback.data == "base_menu":
		await state.clear()
		await main_menu(callback.message, state, True)

	else:
		await callback.message.edit_text("⌛ Генерация платёжной ссылки")

		text: str = 'Не удалось сгенерировать платёжную ссылку'
		butons_i: List[list] = [[types.InlineKeyboardButton(text="< Меню", callback_data="base_menu")]]
		state_data: dict = await state.get_data()
		usd_curse: float = 0.016
		amount: int = state_data.get('amount')
		usd: float = (amount * usd_curse) + 0.20

		value: dict = await sci_currency_rate(callback.data, "USD")
		crypto_value: float = usd / float(value['data']['value'])
		trans_id: str = ''.join([str(randint(0,9)) for i in range(8)])

		paykassa: PayKassa = PayKassa(settings.SHOP_ID, settings.SCI_KEY, settings.SCI_DOMAIN, settings.SCI_TEST)
		link: dict = await paykassa.sci_create_order(crypto_value, callback.data, int(trans_id))
		
		if not link['error']:
			text = '💳 Для пополнения счета перейдите по ссылке:'
			await create_replenishment(str(callback.message.chat.id), trans_id, amount)
			butons_i.insert(0, [types.InlineKeyboardButton(text="Оплатить", url=link['data']['url'])])

		await state.set_state(Pay.select)
		buttons = types.InlineKeyboardMarkup(inline_keyboard=butons_i)
		await callback.message.edit_text(text, reply_markup=buttons)
