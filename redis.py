from typing import Union, Optional

from aioredis import from_url

from settings import settings
from models.user import user_list, all_user_balance, get_user_balance
from handlers.util.utils import pickle_data_dumps


async def redis(decode_responses: bool = False) -> from_url:
	return from_url(settings.REDIS_DSN, decode_responses=decode_responses)


async def get_redis_data(key: Union[str, int],
		project_data: bool = True,
		decode_responses: bool = False, 
		pickle_dumps: bool = False,
		all_update: bool = False,
		one = True,
		cache_update: list = [],
		one_args: dict = {}
	):

	redis_conn = await redis(decode_responses)
	result = await redis_conn.get(key)

	if project_data and result is None:
		await project_cache(all_update, one, cache_update=cache_update, one_args=one_args)
		result = await redis_conn.get(key)
	
	if pickle_dumps:
		result = await pickle_data_dumps(result, True)

	await redis_conn.close()
	return result


async def add_redis_data(key:str, value: Union[str, int, float, list, dict], expire=None, pickle_dumps = True) -> None:
	redis_conn = await redis()

	if pickle_dumps:
		value = await pickle_data_dumps(value)

	await redis_conn.set(key, value, expire)
	await redis_conn.close()


async def redis_hash(key: str, value: dict = {}, data_set=True, update=False) -> Union[None, dict]:
	redis_conn = await redis(True)
	result = None

	if data_set:
		if update:
			old_value: dict = await redis_conn.hgetall(key)
			value = {**old_value, **value} if old_value is not None else value

		await redis_conn.hset(key, mapping=value)

	else:
		result = await redis_conn.hgetall(key)

	await redis_conn.close()
	return result


async def redis_l(key: str, *values: list, 
		data_set: bool = True, 
		project_data: bool = False, 
		delete: bool = False,
		amount: int = 1,
		delete_value: Union[str, int] = None,
		duplication_chech: bool = True,
	):
	redis_conn = await redis(True)
	result: Optional[list] = None
	
	if delete:
		redis_conn.lrem(key, amount, delete_value)

	if data_set:
		for value in values:
			await redis_conn.lpush(key, value)

	elif data_set is False:
		result = await redis_conn.lrange(key, 0, -1)
		if project_data and len(result) == 0:
			await project_cache(False, cache_update=[key])
			result = await redis_conn.lrange(key, 0, -1)

	await redis_conn.close()
	return result


async def project_cache(all_update: bool = True, one: bool = False, cache_update: list = [], one_args: dict = {}):
	redis_conn = await redis()
	await redis_conn.delete("user_registered_list")

	if all_update or "user_registered_list" in cache_update:
		for user_data in await user_list():
			await redis_l("user_registered_list", user_data.user_tg_id)

	if all_update or "user_balance" in cache_update:
		if one:
			user_tg_id = str(one_args.get("user_tg_id"))
			balance = await get_user_balance(user_tg_id)
			await add_redis_data(f"{user_tg_id}__balance", {"balance": balance[1].balance, "demo_balance": balance[0].balance})
		
		else:
			all_balance = await all_user_balance()
			for balance in all_balance:
				await add_redis_data(f"{str(balance)}__balance", all_balance[balance])

	await redis_conn.close()
