coin_list = ('BTC', 'ETH', 'LTC', 'DASH', 'ZEC', 'XRP', 'TRX', 'XLM', 'BNB', 'USDT', 'BUSD')
games_text = {
	"slots": "🎰️ Крути слоты и выбивай выигрышные комбинации",
	"game_dice": "🎲️ Бросайте кубик и испытайте свою удачу",
	"basketball": "🏀 Забрось мяч в корзину, чтобы выиграть. Размер выигрыша зависит от качества попадения",
	"darts": "🎯 Чтобы выиграть, бросай дротик в цель",
	"bouling": "🎳️ Выбейте «страйк» и выиграйте x5 от ставки",
	"football": "⚽️ Забейте «гол» и выиграйте x1.5 от ставки\n\n⭐️ Выигрышных комбинаций больше, чем проигрышных"
}

emojis = {"slots": "🎰️", "game_dice": "🎲️", "basketball": "🏀", "darts": "🎯", "bouling": "🎳️", "football": "⚽️"}

# 0.005 = 50% or 0.5x
# 0.015 = 150% or 1.5x 
# 0.1 = 1000% or 10x 
winning_amount: dict = {
	"basketball": {4: 0.015, 5: 0.025},
	"darts": {4: 0.01, 5: 0.015, 6: 0.03},
	"bouling": {5: 0.005, 6: 0.05},
	"football": {3: 0.015, 4: 0.015, 5: 0.015},
	"slots": {
		1: 0.03, 
		2: 0.0025, 
		3: 0.0025, 
		4: 0.0025,
		6: 0.005,
		11: 0.0025,
		16: 0.01, 
		17: 0.0025, 
		21: 0.005,
		22: 0.1,
		23: 0.005,
		24: 0.005,
		27: 0.0025,
		32: 0.01,
		33: 0.0025,
		38: 0.005,
		41: 0.0025,
		42: 0.0025,
		43: 0.05,
		44: 0.0025, 
		48: 0.01,
		49: 0.0025,
		54: 0.005,
		59: 0.0025,
		61: 0.01,
		62: 0.01,
		63: 0.01,
		64: 0.15
	}
}