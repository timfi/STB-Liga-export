# -*- coding: utf-8 -*-
import enum
import inspect
import logging
from collections import namedtuple
from functools import wraps
from threading import RLock

import pandas as pd
from sqlalchemy import Column, Integer, String, create_engine, Enum, \
                        ForeignKey, Date, Float
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

__all__ = [
    'DB',
]


# taken from https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

def threadsafe(cls):
    _lock = RLock()
    for name, attr in cls.__dict__.items():
        if callable(attr) and name != '__init__':
            @wraps(attr)
            def wrapper(*args, **kwargs):
                with _lock:
                    val = attr(*args, **kwargs)
                return val
            setattr(cls, name, wrapper)
    return cls

def create_reprs(cls):
    for name, attr in cls.__dict__.items():
        if inspect.isclass(attr) and '__tablename__' in attr.__dict__:
            setattr(attr, '__repr__', lambda: f'<{attr.__name__} {str({key: getattr(self, key) for key, item in attr.__dict__ if instanceof(attr, Column)})}>')
    return cls

@create_reprs
class DB(metaclass=Singleton):
    _session = list()

    def __init__(self, *, echo=False):
        self.logger = logging.getLogger('DB')
        self.logger.debug('Creating database...')
        self._engine = DB.create(echo=echo)
        self.logger.debug('Creating session factory')
        self._session_factory = sessionmaker(bind=self._engine)
        self._scoped_session = scoped_session(self._session_factory)
        DB.sessions = []

    def get_session(self):
        session = self._scoped_session()
        self.sessions.append(session)
        return session

    @staticmethod
    def create(*, echo=False):
        engine = create_engine('sqlite:///:memory:', echo=echo)
        DB.Base.metadata.create_all(engine)
        return engine

    Base = declarative_base()

    class League(Base):
        @enum.unique
        class LeagueLevel(enum.Enum):
            OBER = enum.auto()
            VERBANDS = enum.auto()
            LANDES = enum.auto()
            BEZIRKS = enum.auto()
            KREIS = enum.auto()

        __tablename__ = 'league'

        id = Column(Integer, primary_key=True)
        name = Column(String, nullable=False)
        level = Column(Enum(LeagueLevel), nullable=False)

    class Team(Base):
        __tablename__ = 'team'

        id = Column(Integer, primary_key=True)
        name = Column(String, nullable=False)
        league = Column(Integer, ForeignKey("league.id"), nullable=False)

    class Gymnast(Base):
        __tablename__ = 'gymnast'

        id = Column(Integer, primary_key=True)
        firstname = Column(String, nullable=False)
        lastname = Column(String, nullable=False)
        team = Column(Integer, ForeignKey("team.id"), nullable=False)

    class Standoff(Base):
        __tablename__ = 'standoff'

        id = Column(Integer, primary_key=True)
        timestamp = Column(Date, nullable=False)
        location = Column(String, nullable=False)
        host = Column(Integer, ForeignKey('team.id'), nullable=False)
        guest = Column(Integer, ForeignKey('team.id'), nullable=False)

    class Routine(Base):
        @enum.unique
        class Event(enum.Enum):
            BODEN = enum.auto()
            PAUSCHENPFERD = enum.auto()
            RINGE = enum.auto()
            SPRUNG = enum.auto()
            BARREN = enum.auto()
            RECK = enum.auto()

        __tablename__ = 'routine'

        id = Column(Integer, primary_key=True)
        E = Column(Float, nullable=False)
        D = Column(Float, nullable=False)
        event = Column(Enum(Event), nullable=False)
        gymnast = Column(Integer, ForeignKey('gymnast.id'), nullable=False)
        standoff = Column(Integer, ForeignKey('standoff.id'), nullable=False)
