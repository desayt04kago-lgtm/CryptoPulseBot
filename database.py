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
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True)
    target = Column(String, nullable=True)
    alerts = Column(Boolean, nullable=False, default=True)

class Coins(Base):
    __tablename__ = "coins"
    id = Column(BigInteger, primary_key=True)
    name = Column(String, nullable=False)
    price = Column(Numeric, nullable=False)

Base.metadata.create_all(engine)

def check_new_user(id: int) -> bool:
    """
    returns False if user exists in DB\n
    returns True if user does not exist in DB
    :param id:
    """
    session = Session()
    all_users = session.query(Users).all()
    for user in all_users:
        if user.id == id:
            return False
    return True

def register_new_user(id: int, target: str, alerts: bool) -> None:
    """
    adds user to DB\n
    :param id:
    :param target:
    :param alerts:
    """
    session = Session()
    user = Users(id=id, target=target, alerts=alerts)
    session.add(user)
    session.commit()
    session.close()


def add_new_coin(name: str, price: int) -> None:
    """
    adds new coin to DB\n
    :param name:
    :param price:
    :return:
    """
    session = Session()
    coin = Coins(id=len(session.query(Coins).all())+1, name=name, price=price)
    session.add(coin)
    session.commit()
    session.close()

def get_all_coins() -> list:
    session = Session()
    all_coins = session.query(Coins).all()
    session.close()
    return all_coins
