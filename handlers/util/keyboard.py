from typing import Union

from aiogram.utils.keyboard import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def make_row_keyboard(items: dict) -> ReplyKeyboardMarkup:
	row = [KeyboardButton(text=item, request_location=items[item]) for item in items]
	return ReplyKeyboardMarkup(keyboard=[row], resize_keyboard=True)


def inline_keyboard(items: Union[dict, list], switch_in_qr: Union[str, None] = None, row = None) -> InlineKeyboardMarkup:
	row_num: int = 0
	key_num: int = 0
	key_len: int = len(items.keys())
	buttons: list = []
	ram: list = []

	for it in items:
		button = InlineKeyboardButton(
				text=it,
				callback_data=items[it] if type(items) == dict else it,
				switch_inline_query=switch_in_qr
			)
		
		if row is not None:
			ram.append(button)
			row_num += 1
			if row_num >= row or key_num+1 >= key_len:
				buttons.append(ram)
				ram = []
				row_num = 0
		
		else:
			buttons.append([button])

		key_num += 1

	return InlineKeyboardMarkup(row_width=2, inline_keyboard=buttons)
