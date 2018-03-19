# -*- coding: utf-8 -*-
import enum
import inspect
import logging
from contextlib import contextmanager

from sqlalchemy import Column, Integer, String, create_engine, Enum, \
                        ForeignKey, Date, Float
from sqlalchemy.orm import sessionmaker, scoped_session, relationship
from sqlalchemy.ext.declarative import declarative_base

from .helpers import Singleton

__all__ = [
    'DB',
]

def create_reprs(cls):
    for name, attr in cls.__dict__.items():
        if inspect.isclass(attr) and '__tablename__' in attr.__dict__:
            setattr(attr, '__repr__', lambda: f'<{attr.__name__} {str({key: getattr(self, key) for key, item in attr.__dict__ if instanceof(attr, Column)})}>')
    return cls

@create_reprs
class DB(metaclass=Singleton):
    Base = declarative_base()

    def __init__(self, *, echo=False):
        self.logger = logging.getLogger('DB')

        self.logger.debug('Creating database...')
        self._engine = DB.create(echo=echo)

        self.logger.debug('Creating session factory')
        self._session_factory = sessionmaker(bind=self._engine)
        self._scoped_session_factory = scoped_session(self._session_factory)

    @contextmanager
    def get_session(self, *, scoped=False):
        session = self._scoped_session_factory() if scoped else self._session_factory()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    @staticmethod
    def create(*, echo=False, descriptor='sqlite:///:memory:'):
        engine = create_engine(descriptor, echo=echo)
        DB.Base.metadata.create_all(engine)
        return engine

    class League(Base):
        @enum.unique
        class LeagueLevel(enum.Enum):
            OBER = enum.auto()
            VERBANDS = enum.auto()
            LANDES = enum.auto()
            BEZIRKS = enum.auto()
            KREIS = enum.auto()

        __tablename__ = 'leagues'

        id = Column(Integer, primary_key=True)
        name = Column(String, nullable=False)
        level = Column(Enum(LeagueLevel), nullable=False)

    class Team(Base):
        __tablename__ = 'teams'

        id = Column(Integer, primary_key=True)
        name = Column(String, nullable=False)
        league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
        league = relationship('League', back_populates='teams')

    class Gymnast(Base):
        __tablename__ = 'gymnasts'

        id = Column(Integer, primary_key=True)
        firstname = Column(String, nullable=False)
        lastname = Column(String, nullable=False)
        team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
        team = relationship('Team', back_populates='gymnasts')

    class Standoff(Base):
        __tablename__ = 'standoffs'

        id = Column(Integer, primary_key=True)
        timestamp = Column(Date, nullable=False)
        location = Column(String, nullable=False)
        host_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
        host = relationship('Team', back_populates='standoffs')
        guest_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
        guest = relationship('Team', back_populates='standoffs')

    class Routine(Base):
        @enum.unique
        class Event(enum.Enum):
            BODEN = enum.auto()
            PAUSCHENPFERD = enum.auto()
            RINGE = enum.auto()
            SPRUNG = enum.auto()
            BARREN = enum.auto()
            RECK = enum.auto()

        __tablename__ = 'routines'

        id = Column(Integer, primary_key=True)
        E = Column(Float, nullable=False)
        D = Column(Float, nullable=False)
        event = Column(Enum(Event), nullable=False)
        gymnast_id = Column(Integer, ForeignKey('gymnasts.id'), nullable=False)
        gymnast = relationship('Gymnast', back_populates='routines')
        standoff_id = Column(Integer, ForeignKey('standoffs.id'), nullable=False)
        standoff = relationship('Standoff', back_populates='routines')
