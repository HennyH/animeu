# /animeu/models.py
#
# Database models for the animeu site.
#
# See /LICENCE.md for Copyright information
"""Database models for the animeu site."""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

# pylint: disable=invalid-name
engine = create_engine(os.environ["DATABASE"])
# pylint: disable=invalid-name
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflash=False,
                                         bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()

# pylint: disable=too-few-public-methods
class User(Base):
    """Table which represents a user of the application."""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False)
    username = Column(String(30), nullable=False)
    password_hash = Column(String(), nullable=False)
