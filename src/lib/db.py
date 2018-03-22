import logging
from contextlib import contextmanager

from sqlalchemy import create_engine, Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

from .helpers import Singleton

__all__ = [
    'DB',
]


class DB(metaclass=Singleton):
    Model = declarative_base()
    setattr(Model, '__repr__',
            lambda self: f'<{self.__name__} ' +
                         f'{str({key: getattr(self, key) for key, item in self.__dict__ if isinstance(item, Column)})}>'
            )

    def __init__(self, *, echo=False):
        self.logger = logging.getLogger('DB')

        self.logger.info('Creating database engine...')
        self._engine = DB.create(echo=echo)

        self.logger.info('Creating session factory...')
        self._session_factory = sessionmaker(bind=self._engine)
        self._scoped_session_factory = scoped_session(self._session_factory)


    @contextmanager
    def get_session(self, *, scoped=False):
        session = self._scoped_session_factory() if scoped else self._session_factory()
        self.logger.info(f"Started session: {session}")
        try:
            yield session
            session.commit()
        except:
            self.logger.warning(f"Session interrupted, rolling back changes")
            session.rollback()
            raise
        finally:
            session.close()
            self.logger.info(f"Ended session: {session}")

    @staticmethod
    def create(*, echo=False, descriptor='sqlite:///:memory:'):
        engine = create_engine(descriptor, echo=echo)
        DB.Model.metadata.create_all(engine)
        return engine
