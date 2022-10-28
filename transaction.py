from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from paykassa import PayKassa
from database import get_db
from models.balance import get_balance_replenishment, balance_update
from models.user import get_user_balance
from redis import add_redis_data

app = FastAPI()

@app.get("/success")
async def read_item(request: Request):
	return RedirectResponse("http://t.me/GrrbBot", status_code=303)


@app.post("/fail")
async def read_item():
	return RedirectResponse("http://t.me/GrrbBot", status_code=303)


@app.post("/process")
async def transaction_process(request: Request, db: Session = Depends(get_db)):
	paykassa: PayKassa = PayKassa(19179, 'PayKassa_-132442', '6708-92-47-204-103.eu.ngrok.io', False)
	data = await request.body()
	result = {i.split('=')[0]: i.split('=')[1] for i in data.decode('utf-8').split("&")}
	resp = await paykassa.sci_confirm_order(result['private_hash'])

	if not resp['error']:
		order_id: str = result['order_id']
		balance_replenishment = await get_balance_replenishment(order_id, db)

		if balance_replenishment is not None:
			daimond_amount = round(balance_replenishment.amount / 0.7)
			user_balance: tuple = await get_user_balance(balance_replenishment.user_tg_id, None, db)
			user_balance[1].balance += daimond_amount
			await balance_update(user_balance[1], db)
			await add_redis_data(f"{balance_replenishment.user_tg_id}__balance", 
				{"balance": user_balance[1].balance, "demo_balance": user_balance[0].balance}
			)

			db.delete(balance_replenishment)
			db.commit()

	db.close()
	return {}

