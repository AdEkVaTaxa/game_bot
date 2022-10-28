from typing import Optional

from pydantic import BaseModel


class UserData(BaseModel):
	id: int
	first_name: str
	last_name: Optional[str]
	username: Optional[str]


class TransactionModel(BaseModel):
	status: str
	invoice_id: str
	amount_crypto: float
	currency: str

