from sqlalchemy import Column, Integer, String, Sequence
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "product_buyers"
    id = Column(Integer, Sequence("user_id_seq"), primary_key=True)
    username = Column(String(50), unique=True)
    firstname = Column(String(100))
    lastname = Column(String(100))
    password = Column(String(100))
    email_id = Column(String(100))
    phone_number = Column(String(20))
