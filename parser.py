import requests
from bs4 import BeautifulSoup
from database import add_new_coin, get_all_coins, get_user_percent

class Parser:
    def __init__(self, link: str):
        self.link = link
        self.coins = {}

    def get_all_coins(self) -> dict:
        """
        Парсит текущие цены криптовалют с CoinMarketCap

        Извлекает символы (BTC, ETH) и цены, убирает знаки $ и запятые.
        Сохраняет результаты в self.coins для последующего сравнения.

        :return: Словарь {символ: цена}, например {'BTC': '50000', 'ETH': '3000'}
        """
        response = requests.get(self.link).text
        soup = BeautifulSoup(response, "html.parser")
        symbols = soup.find_all("a", class_="cmc-table__column-name--symbol")
        prices = soup.find_all("div", class_="sc-631098c-0 ilZTOW")
        for symbol, price in zip(symbols, prices):
            self.coins[symbol.text.strip()] = price.text.strip().replace("$", "").replace(",", "")
        return self.coins

    def load_to_database(self):
        """
        Загружает спарсенные цены монет в базу данных

        Проходит по всем монетам из self.coins и добавляет каждую
        через функцию add_new_coin(). Используется для первичного
        заполнения БД или обновления текущих цен.

        :return: None
        """
        for name in self.coins.keys():
            add_new_coin(name, self.coins[name])

    def find_coins_with_new_price(self, user_id: int) -> dict:
        """
        Находит монеты, цена которых изменилась больше чем на заданный процент

        Сравнивает текущие цены (self.coins) с ценами в базе данных.
        Проверяет, превышает ли изменение процента порог пользователя
        (получает через get_user_percent).

        :param user_id: ID пользователя в Telegram для получения его порога процента
        :return: Словарь {символ: (старая_цена, новая_цена, процент_изменения)}
               например: {'BTC': (50000.0, 52500.0, 5)}
        """
        all_coins = get_all_coins()
        coins_with_new_price = {}
        for coin in all_coins   :
            percent_difficulty = abs((float(self.coins[coin.name]) - float(coin.price)) / float(coin.price) * 100)
            if coin.price != self.coins[coin.name] and percent_difficulty > get_user_percent(user_id):
                coins_with_new_price[coin.name] = (float(coin.price), float(self.coins[coin.name]), int(percent_difficulty))
        print(coins_with_new_price)
        return coins_with_new_price

