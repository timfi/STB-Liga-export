# -*- coding: utf-8 -*-
import enum

from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Date, Float
from sqlalchemy.orm import relationship

from .lib import DB

__all__ = [
    'STBDB',
    'League',
    'Team',
    'Gymnast',
    'Standoff',
    'Routine',
]


class STBDB(DB):
    DEFAULT_INDEXDB_TABLES = ('person', 'mannschaft', 'tabelle', 'verein', 'halle', 'saison', 'cache', 'begegnung')


class League(DB.Model):
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


class Team(DB.Model):
    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    league = relationship('League', back_populates='teams')


class Gymnast(DB.Model):
    __tablename__ = 'gymnasts'

    id = Column(Integer, primary_key=True)
    firs_tname = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    team = relationship('Team', back_populates='gymnasts')


class Standoff(DB.Model):
    __tablename__ = 'standoffs'

    id = Column(Integer, primary_key=True)
    timestamp = Column(Date, nullable=False)
    location = Column(String, nullable=False)
    host_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    host = relationship('Team', back_populates='standoffs')
    guest_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    guest = relationship('Team', back_populates='standoffs')


class Routine(DB.Model):
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

    @property
    def total(self):
        return 10 + self.D - self.E
