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

    :param name: Символ монеты (BTC, ETH, USDT и т.д.)
    :param price: Текущая цена монеты в USD
    :return: None
    """
    session = Session()
    coin = session.query(Coins).filter(Coins.name == name).first()
    if coin:
        coin.price = price
    else:
        coin = Coins(name=name, price=price)
        session.add(coin)
    session.commit()
    session.close()

def get_all_coins() -> list:
    """
    Получает все криптовалюты из базы данных

    Возвращает список объектов Coins со всеми монетами и их ценами.
    Используется для сравнения текущих цен с ценами в БД.

    :return: Список объектов Coins [Coins(id=1, name='BTC', price=50000), ...] (отсортированный по id)
    :rtype: list

    Пример:
        #>>> coins = get_all_coins()
        #>>> for coin in coins:
        #...     print(f"{coin.name}: {coin.price}")
        BTC: 50000.00
        ETH: 3000.00
    """
    session = Session()
    all_coins = session.query(Coins).order_by(Coins.id).all()
    session.close()
    return all_coins

def get_coins_sub_user(id: int) -> list:
    """
    Получает объект пользователя из базы данных

    Выполняет поиск пользователя по ID в таблице Users и возвращает
    полный объект модели Users. Содержит все поля пользователя:
    - id: ID пользователя в Telegram
    - target: Строка с ID подписок (например, "2_5_10")
    - alerts: Статус уведомлений (True/False)
    - percent: Процент изменения для алерта

    Используется для получения всей информации о пользователе,
    включая его подписки на криптовалюты.

    :param id: ID пользователя в Telegram (chat.id)
    :return: Объект модели Users с данными пользователя
             Пример: Users(id=5803395877, target="2_5_10", alerts=True, percent=5)
    :raises AttributeError: Если пользователь не найден (вернёт None)
    Пример:
        #>>> user = get_coins_sub_user(5803395877)
        #>>> user.target
        "2_5_10"  # Строка с ID подписок

        #>>> user.percent
        5  # Порог изменения цены в процентах

        #>>> user.alerts
        True  # Уведомления включены
    """
    session = Session()
    coins = session.query(Users).filter(Users.id == id).first()
    session.close()
    return coins

def get_coin_from_user(coins_id: list) -> list:
    """
    Получает объекты криптовалют по списку ID

    Выполняет поиск монет в таблице Coins по переданным ID и возвращает
    список объектов моделей. Используется для получения информации о монетах,
    на которые подписан пользователь (например, для отправки уведомлений).

    Для каждого ID из списка делается отдельный запрос к базе данных.
    Если монета с указанным ID не найдена, в список добавляется None.

    :param coins_id: Список ID монет для получения
                     Пример: [2, 5, 10] для BTC, XRP, DOGE
    :type coins_id: list
    :return: Список объектов модели Coins
             Пример: [Coins(id=2, name='BTC', price=50000), Coins(id=5, name='XRP', price=1.34), ...]
             Если монета не найдена — на её месте будет None
    :rtype: list
    """
    session = Session()
    coins = []
    for coin in coins_id:
        if coin and coin.strip():
            coins.append(session.query(Coins).filter(Coins.id == coin).first())
    session.close()
    return coins

def get_user_info(id: int) -> dict:
    """
    Получает полную информацию о пользователе из базы данных

    Выполняет поиск пользователя по ID в таблице Users и возвращает
    объект модели со всеми полями: id, target, alerts, percent.

    Используется для получения настроек пользователя перед отправкой
    уведомлений или при проверке статуса подписки.

    :param id: ID пользователя в Telegram (chat.id)
    :type id: int
    :return: Объект модели Users с данными пользователя
             Пример: Users(id=5803395877, target="2_5_10", alerts=True, percent=5)
             Если пользователь не найден — возвращает None
    :rtype: Users или None

    Пример:
        #>>> get_user_info(5803395877)
        Users(id=5803395877, target="2_5_10", alerts=True, percent=5)
    """
    session = Session()
    user_info = session.query(Users).filter(Users.id == id).first()
    session.close()
    return user_info


def update_user_percent(id: int, new_percent: int) -> bool:
    """
    Обновляет процент изменения цены для пользователя

    Изменяет значение поля percent в таблице Users для указанного пользователя.
    Используется когда пользователь хочет изменить порог срабатывания уведомлений.

    :param id: ID пользователя в Telegram (chat.id)
    :type id: int
    :param new_percent: Новый процент изменения (например, 5 для 5%)
    :type new_percent: int
    :return: True если обновление успешно, False если пользователь не найден
    :rtype: bool

    Пример:
        #>>> update_user_percent(5803395877, 10)
        True  # Процент изменён на 10%

        #>>> update_user_percent(1234567890, 5)
        False  # Пользователь не найден
    """
    session = Session()
    user = session.query(Users).filter(Users.id == id).first()

    if user:
        user.percent = new_percent
        session.commit()
        session.close()
        return True

    session.close()
    return False

def update_user_alert(id: int, new_alert: bool) -> bool:
    """
    Обновляет статус уведомлений для пользователя

    Изменяет значение поля alerts в таблице Users для указанного пользователя.
    Используется когда пользователь хочет включить или выключить получение
    уведомлений об изменении цен криптовалют.

    :param id: ID пользователя в Telegram (chat.id)
    :type id: int
    :param new_alert: Новый статус уведомлений (True = включены, False = выключены)
    :type new_alert: bool
    :return: True если обновление успешно, False если пользователь не найден
    :rtype: bool

    Пример:
        #>>> update_user_alert(5803395877, True)
        True  # Уведомления включены

        #>>> update_user_alert(5803395877, False)
        True  # Уведомления выключены
    """
    session = Session()
    user = session.query(Users).filter(Users.id == id).first()

    if user:
        user.alerts = new_alert
        session.commit()
        session.close()
        return True

    session.close()
    return False

def add_coin_to_target(id: int, add_coin_id: str) -> bool:
    """
    Добавляет ID монеты в список подписок пользователя
    :param id: ID пользователя в Telegram
    :param add_coin_id: ID монеты для добавления
    :return: True если успешно, False если пользователь не найден
    """
    session = Session()
    user = session.query(Users).filter(Users.id == id).first()
    if user:
        all_coin_id = user.target.split("_")
        if add_coin_id not in all_coin_id:
            all_coin_id.append(add_coin_id)
        user.target = "_".join(all_coin_id)
        session.commit()
        return True
    session.close()
    return False

def delete_coin_from_target(id: int, del_coin_id: str) -> bool:
    """
    Удаляет ID монеты из списка подписок пользователя
    :param id: ID пользователя в Telegram
    :param del_coin_id: ID монеты для удаления
    :return: True если успешно, False если пользователь не найден
    """
    session = Session()
    user = session.query(Users).filter(Users.id == id).first()
    if user:
        all_coin_id = user.target.split("_")
        for coin_id in all_coin_id:
            if coin_id == del_coin_id:
                all_coin_id.remove(del_coin_id)
        user.target = "_".join(all_coin_id)
        session.commit()
        session.close()
        return True
    session.close()
    return False

def get_all_users_with_alerts() -> list:
    """
    Получает список всех пользователей с активными уведомлениями

    Выполняет выборку всех пользователей из таблицы Users и фильтрует
    только тех, у кого включены уведомления (поле alerts = True).
    Используется для рассылки уведомлений об изменении цен криптовалют.

    :return: Список объектов модели Users, у которых alerts = True
             Пример: [Users(id=5803395877, target="2_5_10", alerts=True, percent=5), ...]
             Если нет пользователей с активными уведомлениями — возвращает пустой список []
    :rtype: list

    Пример:
        #>>> get_all_users_with_alerts()
        [Users(id=5803395877, target="2_5_10", alerts=True, percent=5),
         Users(id=1234567890, target="3_7", alerts=True, percent=10)]

        #>>> get_all_users_with_alerts()
        []  # Нет пользователей с включёнными уведомлениями
    """
    users_with_alerts = []
    session = Session()
    users = session.query(Users).all()
    for user in users:
        if user.alerts:
            users_with_alerts.append(user)
    session.close()
    return users_with_alerts

