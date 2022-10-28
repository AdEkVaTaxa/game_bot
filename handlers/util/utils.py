from typing import Union
from random import randint, choice
from pickle import dumps, loads

from aiogram import types
from aiogram.dispatcher.fsm.context import FSMContext

from settings import settings


async def check_int(message: types.Message) -> bool:
	try:
		value = int(message.text)
		return value >= 50
	except:
		return False


async def check_sum(message: types.Message, state: FSMContext) -> bool:
	min_width_amount: int = settings.MINIMUM_WIDTH_AMOUNT
	try:
		value = int(message.text)
		state_data = await state.get_data()
		text = "❌ Введенная сумма превышает сумму вашего баланса"
		if value >= min_width_amount and value <= int(state_data['balance']):
			return True

		await message.answer(f"❌ Введенная сумма меньше {min_width_amount}" if value < min_width_amount else text)
	except:
		return False


async def admin_validator(message: types.Message):
	return message.chat.id in settings.ADMIN_LIST


async def random_str(length: int = 6):
	symb = 'abcdefghijklmnopqrstuvwxyz1234567890'
	string = [choice(symb.upper() if randint(0, 1) == 1 else symb) for i in range(length)]

	return ''.join(string)


async def pickle_data_dumps(data: Union[dict, object], status: bool = False) -> Union[bytes, dict, None]:
	if data is None:
		return None

	if status:
		return loads(data)

	else:
		if type(data) == dict:
			picke_dumps = {}
			for i in data:
				picke_dumps[i] = data[i]
		else:
			picke_dumps = data

		return dumps(picke_dumps)
