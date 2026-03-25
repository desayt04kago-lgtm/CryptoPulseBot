from sqlalchemy import create_engine
from sqlalchemy import Integer, String, Column, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

engine = create_engine(f"postgresql+psycopg2://postgres:{os.getenv("database_password")}/@localhost/postgres")
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    target = Column(String, nullable=True)
    alerts = Column(Boolean, nullable=True)

Base.metadata.create_all(engine)

def check_new_user(id: int) -> bool:
    """
    returns True if user exists in DB\n
    returns False if user does not exist in DB
    """
    session = Session()
    all_users = session.query().all()
    for user in all_users:
        if user.id == id:
            return False
    return True


