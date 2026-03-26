import requests
from bs4 import BeautifulSoup
from database import add_new_coin, get_all_coins, get_user_percent

class Parser:
    def __init__(self, link: str):
        self.link = link
        self.coins = {}

    def get_all_coins(self) -> dict:
        response = requests.get(self.link).text
        soup = BeautifulSoup(response, "html.parser")
        symbols = soup.find_all("a", class_="cmc-table__column-name--symbol")
        prices = soup.find_all("div", class_="sc-631098c-0 ilZTOW")
        for symbol, price in zip(symbols, prices):
            self.coins[symbol.text.strip()] = price.text.strip().replace("$", "").replace(",", "")
        return self.coins

    def load_to_database(self):
        for name in self.coins.keys():
            add_new_coin(name, self.coins[name])

    def find_coins_with_new_price(self, user_id: int) -> dict:
        all_coins = get_all_coins()
        coins_with_new_price = {}
        for coin in all_coins:
            percent_difficulty = (float(self.coins[coin.name]) - float(coin.price)) / float(coin.price) * 100
            if coin.price != self.coins[coin.name] and abs(percent_difficulty) > get_user_percent(user_id):
                coins_with_new_price[coin.name] = (float(coin.price), float(self.coins[coin.name]), int(percent_difficulty))
        print(coins_with_new_price)
        return coins_with_new_price

parser = Parser("https://coinmarketcap.com/all/views/all/")
parser.get_all_coins()
parser.find_coins_with_new_price(5803395877)