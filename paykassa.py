from typing import Union, Optional
import asyncio

from aiohttp import ClientSession


class PayKassa:
	sci_id: int
	sci_key: str
	domain: str
	test: bool
	sci_domain: str = 'https://paykassa.app/sci/0.4/index.php'

	def __init__(self, sci_id, sci_key, domain, test):
		self.sci_id = sci_id
		self.sci_key = sci_key
		self.domain = domain
		self.test = test and 'true' or 'false'

	async def sci_confirm_order(self, private_hash: str):
		return await self.make_request({'func': 'sci_confirm_order', 'private_hash': private_hash})

	async def sci_create_order(self, 
			amount: Union[int, float], 
			currency: str, 
			order_id: Union[str, int], 
			comment: Optional[str] = ''
		):
		coint_id = {"BTC": 11, "ETH": 12, "LTC": 14, "DASH": 16, "ZEC": 19, 
			"XRP": 22, "TRX": 27, "XLM": 28, "BNB": 29, "USDT": 30, "BUSD": 31
		}

		return await self.make_request({
			'func': 'sci_create_order',
			'amount': amount,
			'currency': currency,
			'order_id': order_id,
			'comment': comment,
			'system': coint_id.get(currency),
			'paid_commission': ''
		})

	async def make_request(self, params: dict) -> dict:
		fields = {'sci_id': self.sci_id, 'sci_key': self.sci_key, 'domain': self.domain, 'test': self.test}.copy()
		fields.update(params)
		headers = {'Content-Type': 'application/x-www-form-urlencoded'}
		result: dict = None

		async with ClientSession() as session:
			async with session.post(self.sci_domain, headers=headers, data=fields) as resp:
				result = await resp.json()
			await session.close()

		return result


async def sci_currency_rate(currency_in: str, currency_out: str):
	currency: str = "https://currency.paykassa.pro/index.php"
	data = {"currency_in": currency_in, "currency_out": currency_out}
	result: dict = {}

	async with ClientSession() as session:
		async with session.post("https://currency.paykassa.pro/index.php", data=data) as resp:
			result = await resp.json()
		await session.close()

	return result
