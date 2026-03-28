from sqlalchemy import create_engine
from sqlalchemy import Integer, String, Boolean, Column, BigInteger, Numeric
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv
import os
load_dotenv()

DB_PASSWORD = os.getenv('database_password')
engine = create_engine(f"postgresql+psycopg2://postgres:{DB_PASSWORD}@localhost/postgres")
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Users(Base):
    """
    Модель таблицы пользователей

    Хранит информацию о пользователях бота:
    - ID пользователя Telegram
    - Целевая монета для отслеживания
    - Статус уведомлений
    - Процент изменения цены для алерта

    Таблица: users
    """
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True)
    target = Column(String, nullable=True)
    alerts = Column(Boolean, nullable=False, default=True)
    percent = Column(Integer, nullable=False)

class Coins(Base):
    """
    Модель таблицы криптовалют

    Хранит текущие цены криптовалют:
    - Символ монеты (BTC, ETH, USDT)
    - Текущая цена в USD

    Таблица: coins
    Поле name имеет уникальное ограничение (unique=True)
    """
    __tablename__ = "coins"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    price = Column(Numeric(18, 8), nullable=False)

Base.metadata.create_all(engine)

def check_new_user(id: int) -> bool:
    """
    Проверяет, зарегистрирован ли пользователь в базе данных

    Выполняет полную выборку всех пользователей и проверяет наличие
    указанного ID. Используется при первом запуске бота пользователем.

    :param id: ID пользователя в Telegram (chat.id)
    :return: False если пользователь существует в БД
             True если пользователь не найден (новый пользователь)

    Пример:
        # >>> check_new_user(5803395877)
        True  # Пользователь новый, нужно зарегистрировать
    """
    session = Session()
    all_users = session.query(Users).all()
    for user in all_users:
        if user.id == id:
            return False
    return True

def register_new_user(id: int, target: str, alerts: bool, percent: int) -> None:
    """
    Регистрирует нового пользователя в базе данных

    Создаёт запись пользователя с настройками уведомлений.
    Вызывается после команды /start когда пользователь подтверждает регистрацию.

    :param id: ID пользователя в Telegram (chat.id)
    :param target: Целевая монета для отслеживания (например, 'BTC')
    :param alerts: Статус уведомлений (True = включены, False = выключены)
    :param percent: Процент изменения цены для срабатывания алерта (например, 5)
    :return: None

    Пример:
        #>>> register_new_user(5803395877, 'BTC', True, 5)
        # Пользователь зарегистрирован с порогом 5%
    """
    session = Session()
    user = Users(id=id, target=target, alerts=alerts, percent=percent)
    session.add(user)
    session.commit()
    session.close()

def get_user_percent(id: int) -> int:
    """
        Получает процент изменения цены для пользователя

        Возвращает индивидуальный порог процента, который пользователь
        указал при регистрации. Используется для фильтрации уведомлений.

        :param id: ID пользователя в Telegram (chat.id)
        :return: Процент изменения (например, 5 для 5%)
        :raises AttributeError: Если пользователь не найден в базе

        Пример:
            #>>> get_user_percent(5803395877)
            5  # Пользователь хочет уведомления при изменении на 5%
        """
    session = Session()
    user = session.query(Users).filter(Users.id == id).first()
    session.close()
    return user.percent

def add_new_coin(name: str, price: float) -> None:
    """
    Добавляет или обновляет цену монеты в базе данных

    Использует session.merge() для автоматического определения:
    - Если монета с таким name существует → обновляет цену
    - Если монеты нет → создаёт новую запись

    Вызывается при каждом парсинге CoinMarketCap для актуализации цен.

    :param name: Символ монеты (BTC, ETH, USDT и т.д.)
    :param price: Текущая цена монеты в USD (например, 50000.00)
    :return: None

    Пример:
        # >>> add_new_coin('BTC', 50000.00)
        # Цена BTC обновлена или добавлена новая запись
    """
    session = Session()
    coin = Coins(name=name, price=price)
    session.merge(coin)
    session.commit()
    session.close()

def get_all_coins() -> list:
    """
    Получает все криптовалюты из базы данных

    Возвращает список объектов Coins со всеми монетами и их ценами.
    Используется для сравнения текущих цен с ценами в БД.

    :return: Список объектов Coins [Coins(id=1, name='BTC', price=50000), ...]
    :rtype: list

    Пример:
        #>>> coins = get_all_coins()
        #>>> for coin in coins:
        #...     print(f"{coin.name}: {coin.price}")
        BTC: 50000.00
        ETH: 3000.00
    """
    session = Session()
    all_coins = session.query(Coins).all()
    session.close()
    return all_coins
