
from sqlalchemy import BigInteger
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Unicode
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


class InstanceConfig(Base):
    __tablename__ = 'instance_config'
    name = Column(String(255), primary_key=True, nullable=False)
    value = Column(Unicode(), nullable=True)


class User(Base):
    __tablename__ = 'user'
    wingcash_id = Column(BigInteger(), primary_key=True, nullable=False)
    access_token = Column(String(255), nullable=False)
    display_name = Column(Unicode(255), nullable=False)
    url = Column(String(255), nullable=False)
    image48 = Column(String(255), nullable=True)
    cash_usd = Column(String(20), nullable=True)


class MicroBankRoot(object):

    def __init__(self):
        self.__name__ = None
        self.__parent__ = None

    def __getitem__(self, key):
        session = DBSession()
        try:
            wingcash_id = int(key)
        except (ValueError, TypeError):
            raise KeyError(key)

        user = session.query(User).get(wingcash_id)
        if user is None:
            raise KeyError(key)

        user.__parent__ = self
        user.__name__ = key
        return user

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __iter__(self):
        session = DBSession()
        query = session.query(User).order_by(User.display_name).all()
        return iter(query)


root = MicroBankRoot()


def root_factory(request):
    return root


def initialize_sql(engine):
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    return DBSession


def appmaker(engine):
    initialize_sql(engine)
    return root_factory
