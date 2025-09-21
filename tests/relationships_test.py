import pytest
from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, Session, relationship

from ormparams.suffixes import DefaultSuffixSet
from ormparams.parser import Parser, ParserRules
from ormparams.filter import OrmFilter

Base = declarative_base()


class Address(Base):
    __tablename__ = "addresses"
    id = Column(Integer, primary_key=True)
    city = Column(String)


class Profile(Base):
    __tablename__ = "profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    address_id = Column(Integer, ForeignKey("addresses.id"))

    address = relationship("Address")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String)
    profile = relationship("Profile", uselist=False)


@pytest.fixture(scope="module")
def session():
    engine = create_engine("sqlite:///:memory:", echo=True, future=True)
    Base.metadata.create_all(engine)

    addr1 = Address(city="Kyiv")
    addr2 = Address(city="Lviv")

    user1 = User(username="alice", profile=Profile(address=addr1))
    user2 = User(username="bob", profile=Profile(address=addr2))
    user3 = User(username="charlie", profile=Profile(address=addr1))

    with Session(engine) as session:
        session.add_all([user1, user2, user3])
        session.commit()
        yield session


@pytest.fixture(scope="module")
def parser():
    suffix_set = DefaultSuffixSet()
    return Parser(rules=ParserRules(suffix_set=suffix_set))


def test_relationship_filter(session, parser):
    orm_filter = OrmFilter(parser)

    query = orm_filter.filter(User, "profile@address@city=Kyiv").query
    print("SQL:", query)

    result = session.execute(query).scalars().all()
    usernames = [u.username for u in result]
    print(usernames)

    assert set(usernames) == {"alice", "charlie"}
