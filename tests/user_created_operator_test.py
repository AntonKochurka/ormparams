import pytest
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, Session

from ormparams.suffixes import DefaultSuffixSet
from ormparams.parser import Parser, ParserRules
from ormparams.filter import OrmFilter

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String)
    age = Column(Integer)

    def to_dict(self) -> dict:
        return {"id": self.id, "username": self.username, "age": self.age}


@pytest.fixture(scope="module")
def session():
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all(
            [
                User(username="alice", age=25),
                User(username="bob", age=17),
                User(username="charlie", age=35),
                User(username="alice", age=13),
            ]
        )
        session.commit()
        yield session


@pytest.fixture(scope="module")
def parser():
    suffix_set = DefaultSuffixSet()

    suffix_set.register_suffix("alice", lambda col, _v, t: t.username == "alice")

    return Parser(rules=ParserRules(suffix_set=suffix_set))


def print_result(result):
    print("Result:", *[res.to_dict() for res in result])


def test_two_operators(session, parser):
    orm_filter = OrmFilter(parser)
    query = orm_filter.filter(User, "age__gt__alice=18").query
    print("SQl: ", str(query))

    result = session.execute(query).scalars().all()
    print_result(result)
