import os

from pydantic import (
	BaseSettings,
	RedisDsn,
	PostgresDsn
)


class Settings(BaseSettings):
	TOKEN: str = os.env('TOKEN')
	REDIS_DSN: RedisDsn = 'redis://localhost/1'
	SQLALCHEMY_DATABASE_URL: PostgresDsn  = os.env('SQLALCHEMY_DATABASE_URL')
	MERCHAN_API_KEY = os.env('MERCHAN_API_KEY')
	SHOP_ID = os.env('SHOP_ID')
	ADMIN_LIST: tuple = (5006438421, 1462533880)
	SHOP_ID: int = 19179
	SCI_KEY: str = os.env('SCI_KEY')
	SCI_DOMAIN: str = "6708-92-47-204-103.eu.ngrok.io"
	SCI_TEST: bool = False
	MINIMUM_WIDTH_AMOUNT: int = 350


settings = Settings()
