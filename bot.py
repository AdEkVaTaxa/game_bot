import asyncio
from aiogram import Bot, Dispatcher
from os import system

from multiprocessing import Process

from settings import settings
from database import engine
from models import *
from handlers import commands, games, admin, balance
from redis import project_cache

async def main():
	bot = Bot(settings.TOKEN, parse_mode="HTML")
	dp = Dispatcher()

	Base.metadata.create_all(bind=engine)
	dp.include_router(commands.router)
	dp.include_router(games.router)
	dp.include_router(admin.router)
	dp.include_router(balance.router)
	await project_cache()

	print("BOT WORKS")
	await bot.delete_webhook(drop_pending_updates=True)
	await dp.start_polling(bot)


if __name__ == '__main__':
	try:
		Process(target=system, args=("python asgi.py",)).start()
		asyncio.run(main())

	except KeyboardInterrupt:
		print("\n@GoodBye :)")
