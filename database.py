from sqlalchemy import create_engine
from sqlalchemy import Integer, String, Boolean, Column, BigInteger
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


