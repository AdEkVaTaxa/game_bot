from typing import Union
from datetime import datetime

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Float
from sqlalchemy.orm import relationship, Session

from database import Base, get_db

class DemoBalance(Base):
	__tablename__ = "demo_balance"

	id = Column(Integer, primary_key=True)
	user_id = Column(Integer, ForeignKey("user.id"))
	balance = Column(Integer, default=10000)


class Balance(Base):
	__tablename__ = "balance"

	id = Column(Integer, primary_key=True)
	user_id = Column(Integer, ForeignKey("user.id"))
	balance = Column(Integer, default=0)

	def update(self, db: Session):
		db.add(self)
		db.commit()


class BalanceReplenishment(Base):
	__tablename__ = "balance_replenishment"

	id = Column(Integer, primary_key=True)
	user_tg_id = Column(String(18))
	invoice_id = Column(String(30), unique=True)
	amount = Column(Integer)


class Withdrawals(Base):
	__tablename__ = "withdrawals"

	id = Column(Integer, primary_key=True)
	user_id = Column(Integer)
	user_tg_id = Column(String(18))
	coin = Column(String(10))
	adress_data = Column(String(1500))
	amount = Column(Integer)
	referal_balance = Column(Boolean, default=False)


class BetAmount(Base):
	__tablename__ = "bet_amount"

	id = Column(Integer, primary_key=True)
	user_id = Column(Integer, ForeignKey("user.id"), unique=True)
	bet_amount = Column(Float, default=0)

	def update(self, db: Session):
		db.add(self)
		db.commit()


async def balance_update(balance: Union[DemoBalance, Balance], db: Session = None) -> None:
	auto_close: bool = False
	if balance.balance < 0:
		balance.balance = 0

	if db is None:
		db = get_db()
		auto_close = True

	db.add(balance)
	db.commit()

	if auto_close: db.close()


async def create_replenishment(user_tg_id: str, invoice_id: str, amount: int, db: Session = None) -> None:
	auto_close: bool = False
	if db is None:
		auto_close = True
		db = get_db()
	
	replenishment = BalanceReplenishment(user_tg_id=user_tg_id, invoice_id=invoice_id, amount=amount)

	db.add(replenishment)
	db.commit()
	db.refresh(replenishment)
	db.expunge(replenishment)

	if auto_close:
		db.close()


async def get_balance_replenishment(order_id: str, db: Session)  -> Union[None, BalanceReplenishment]:
	return db.query(BalanceReplenishment).filter(BalanceReplenishment.invoice_id == order_id).one_or_none()


async def get_bet_amount(user_id: int, db: Session = None) -> Union[None, int]:
	result = db.query(BetAmount).filter(BetAmount.user_id == user_id).one_or_none()

	return result


async def create_withdrawals(user_id: int, user_tg_id: str, coin: str, adress_data: str, amount: int, r_balance, db) -> None:
	withdrawals = Withdrawals(user_id = user_id, user_tg_id=user_tg_id, coin=coin, adress_data=adress_data, amount=amount, referal_balance=r_balance)

	db.add(withdrawals)
	db.commit()


async def all_withdrawals():
	db = get_db()
	result = db.query(Withdrawals).all()
	db.close()

	return result


async def withdrawals_id(entry_id: int, db):
	return db.query(Withdrawals).get(entry_id)
