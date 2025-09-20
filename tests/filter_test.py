import pytest
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, Session

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
            ]
        )
        session.commit()
        yield session


def print_result(result):
    print("Result:", *[res.to_dict() for res in result])


def test_filter_exact(session):
    parser = Parser(ParserRules())
    orm_filter = OrmFilter(parser)
    query = orm_filter.filter(User, "username=alice").query
    print("SQL:", str(query))
    result = session.execute(query).scalars().all()
    print_result(result)
    assert len(result) == 1
    assert result[0].username == "alice"


def test_filter_gt(session):
    parser = Parser(ParserRules())
    orm_filter = OrmFilter(parser)
    query = orm_filter.filter(User, "age__gt=18").query
    print("SQL:", str(query))
    result = session.execute(query).scalars().all()
    print_result(result)
    assert all(u.age > 18 for u in result)


def test_filter_range(session):
    parser = Parser(ParserRules())
    orm_filter = OrmFilter(parser)
    query = orm_filter.filter(User, "age__gt=18&age__lt=30").query
    print("SQL:", str(query))
    result = session.execute(query).scalars().all()
    print_result(result)
    assert all(18 < u.age < 30 for u in result)


def test_filter_contains(session):
    parser = Parser(ParserRules())
    orm_filter = OrmFilter(parser)
    query = orm_filter.filter(User, "username__contains=ali").query
    print("SQL:", str(query))
    result = session.execute(query).scalars().all()
    print_result(result)
    assert any("ali" in u.username for u in result)
