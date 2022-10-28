from typing import Union
from datetime import datetime

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship, Session

from .balance import DemoBalance, Balance, BetAmount
from handlers.util.utils import random_str
from database import Base, get_db
from schemas import UserData


class UserReferal(Base):
	__tablename__ = "user_referal"

	id = Column(Integer, primary_key=True)
	user_id = Column(Integer, ForeignKey('user.id'))
	referal_user_id = Column(String(16))

	def __repr__(self,):
		return str(self.user_id)


class User(Base):
	__tablename__ = "user"

	id = Column(Integer, primary_key=True)
	user_tg_id = Column(String(18), unique=True)
	first_name = Column(String(65), unique=False, nullable=False)
	last_name = Column(String(65), unique=False, nullable=True)
	tg_username = Column(String(40), unique=True, nullable=True)
	date_created = Column(DateTime)
	user_referal_code = Column(String(65), unique=True)
	freeze = Column(Boolean, default=False)
	demo_balance = relationship(DemoBalance)
	user_referal = relationship(UserReferal)
	balance = relationship(Balance)

	def __repr__(self,):
		return self.first_name

	def update(self,):
		db = get_db()
		db.add(self)
		db.commit()
		db.refresh(self)
		db.expunge(self)
		db.close()

		return self

	def get_dict(self,):
		data = self.__dict__.copy()
		del data['_sa_instance_state']
		data['date_created'] = data['date_created'].strftime("%d.%m.%Y %H:%M:%S")

		return data


async def create_user(user_data: UserData, db) -> str:
	date_created = datetime.now()
	referal_code = await random_str(8)

	user = User(user_tg_id=user_data.id, 
		first_name=user_data.first_name, 
		last_name=user_data.last_name,
		tg_username=user_data.username,
		date_created=date_created,
		user_referal_code=referal_code
	)

	db.add(user)
	db.commit()
	
	demo_balance = DemoBalance(user_id = user.id)
	balance = Balance(user_id = user.id)
	bet_amount = BetAmount(user_id = user.id)

	db.add_all([demo_balance, balance, bet_amount])
	db.commit()

	return referal_code, user


async def create_referal(user_id: int, referal_id: str, db: Session) -> None:
	user_referal = UserReferal(user_id = user_id, referal_user_id = referal_id)
	db.add(user_referal)
	db.commit()


async def user_list() -> list:
	db = get_db()
	result = db.query(User).all()

	db.close()
	return result


async def get_user_tg_id(user_tg_id: str, db: Session = None) -> Union[User, None]:
	try:
		auto_close = False
		if db is None:
			db = get_db()
			auto_close = True

		result = db.query(User).filter(User.user_tg_id == user_tg_id).one_or_none()

	except:
		result = await get_user_tg_id(user_tg_id, db)

	finally:
		if auto_close:db.close()
		return result


async def get_user_balance(user_tg_id: str, balance_type: str = None, db: Session = None) -> Union[list, dict]:
	try:
		auto_close = False

		if db is None:
			auto_close = True
			db = get_db()
	
		user_tg_id = str(user_tg_id)
		result = db.query(DemoBalance, Balance).filter(User.user_tg_id == user_tg_id, 
				DemoBalance.user_id == User.id,
				Balance.user_id == User.id
			).one_or_none()

		if balance_type is not None:
			result = result[0] if balance_type == "demo_balance" else result[1]

	except:
		result = await get_user_balance(user_tg_id, balance_type, db)

	finally:
		if auto_close: db.close()
		return result


async def all_user_balance() -> dict:
	db = get_db()
	result: dict = {}

	user_list = db.query(User.user_tg_id).all()
	for user in user_list:
		user_balance = await get_user_balance(user.user_tg_id)
		result[user.user_tg_id] = {"balance": user_balance[1].balance, "demo_balance": user_balance[0].balance}

	db.close()
	return result


async def get_user_referal(user_id: str, db: Session) -> list:
	return db.query(UserReferal).filter(UserReferal.user_id == user_id).all()


async def get_referal_user_id(user_tg_id: str, db: Session = None) -> Union[None, UserReferal]:
	auto_close: bool = False
	if db is None:
		db = get_db()
		auto_close = True

	result = db.query(UserReferal.user_id).filter(UserReferal.referal_user_id == user_tg_id).one_or_none()

	if auto_close:
		db.close()

	return result[0] if result is not None else None


async def get_ref_code(db: Session, ref_code: str):
	return db.query(User).filter(User.user_referal_code == ref_code).one_or_none()
