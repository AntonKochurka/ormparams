import pytest

from pprint import pprint
from sqlalchemy import Column, Integer, String, ForeignKey, create_engine, select
from sqlalchemy.orm import declarative_base, relationship, Session

from ormparams.core.suffixes import DefaultSuffixSet
from ormparams.core.mixin import OrmParamsMixin
from ormparams.core.policy import OrmParamsPolicy
from ormparams.core.parser import OrmParamsParser
from ormparams.core.filter import OrmParamsFilter

Base = declarative_base()


class Parent(Base, OrmParamsMixin):
    __tablename__ = "parents"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    children = relationship("Child", back_populates="parent")

    def to_dict(self):
        return {"id": self.id, "name": self.name}


class Child(Base, OrmParamsMixin):
    __tablename__ = "children"
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey("parents.id"))
    value = Column(String)
    parent = relationship("Parent", back_populates="children")

    def to_dict(self):
        return {"id": self.id, "value": self.value, "parent_id": self.parent_id}


@pytest.fixture
def setup_db():
    engine = create_engine("sqlite:///test.db", future=True)
    Base.metadata.create_all(engine)
    print("Database setup complete")
    return engine


@pytest.fixture
def session(setup_db):
    sess = Session(setup_db)

    parent1 = Parent(name="Alice")
    parent2 = Parent(name="Bob")

    child1 = Child(value="C1", parent=parent1)
    child2 = Child(value="C2", parent=parent1)
    child3 = Child(value="C3", parent=parent2)

    # sess.add_all([parent1, parent2, child1, child2, child3])
    # sess.commit()
    print("Database populated with sample data")
    return sess


@pytest.fixture
def policy():
    print("Policy fixture created")
    suffix_set = DefaultSuffixSet()

    suffix_set.register("alice", lambda v, c, m: m.name == "Alice")

    return OrmParamsPolicy(SUFFIX_SET=suffix_set)


@pytest.fixture
def parser(policy):
    print("Parser fixture created")
    return OrmParamsParser(policy=policy)


def test_non_relationship(session, policy, parser):
    print("Running test_non_relationship")
    parsed = parser.parse("id__lt__exact__alice=2")
    print(f"Parsed params: {parsed}")

    f = OrmParamsFilter(
        model=Parent, policy=policy, parsed=parsed
    ).apply_logic_executor(
        "id",
        operational_logic_executor=["OR", "AND"],
        # if id is 2 or less, AND if name of user is Alice
    )

    query = f.filter()
    print(f"Generated SQL: {query}")

    result = session.execute(query).all()
    print("Query result:", pprint(*[v[0].to_dict() for v in result]))
    assert len(result) == 1
    assert result[0][0].name == "Alice"


def test_relationship(session, policy, parser):
    print("Running test_relationship")
    parsed = parser.parse("children.value=C1")
    print(f"Parsed params: {parsed}")

    f = OrmParamsFilter(model=Parent, policy=policy, parsed=parsed)

    query = f.filter(allowed_relationships=["children"])
    print(f"Generated SQL: {query}")

    result = session.execute(query).all()
    print("Query result:", [v[0].to_dict() for v in result])
    assert len(result) == 1
    assert result[0][0].name == "Alice"


def test_multiple_conditions(session, policy, parser):
    print("Running test_multiple_conditions")
    parsed = parser.parse("name=Alice&children.value=C1")
    print(f"Parsed params: {parsed}")

    f = OrmParamsFilter(model=Parent, policy=policy, parsed=parsed)

    query = f.filter(allowed_relationships=["children"])
    print(f"Generated SQL: {query}")

    result = session.execute(query).all()
    print("Query result:", result)
    assert len(result) == 1
    assert result[0][0].name == "Alice"
