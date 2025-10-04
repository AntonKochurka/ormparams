from fastapi import Depends, FastAPI
from models import (
    Child,
    ChildCreateSchema,
    ChildReadSchema,
    Parent,
    ParentCreateSchema,
    ParentReadSchema,
    SessionLocal,
)
from sqlalchemy.orm import Session

from ormparams import OrmParamsFastAPI, OrmParamsFilter

app = FastAPI()

ormparams = OrmParamsFastAPI()
ormparams.init_app(app)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/parents", response_model=list[ParentReadSchema])
async def get_parents(
    db: Session = Depends(get_db),
    params=Depends(ormparams.get_params([Parent, Child], include=["children"])),
):
    query = OrmParamsFilter(
        ormparams.policy,
        model=Parent,
        parsed=params,
    ).filter(allowed_relationships=["children"])
    return db.execute(query).scalars().all()


@app.get("/children", response_model=list[ChildReadSchema])
async def get_children(
    db: Session = Depends(get_db),
    params=Depends(ormparams.get_params(Child)),
):
    query = (
        OrmParamsFilter(
            ormparams.policy,
            model=Child,
            parsed=params,
        )
        .apply_logic_executor(field_name="value", parametric_logic_executor="AND")
        .filter()
    )

    return db.execute(query).scalars().all()


@app.post("/parents", response_model=ParentReadSchema)
async def create_parent(parent: ParentCreateSchema, db: Session = Depends(get_db)):
    db_parent = Parent(**parent.dict())
    db.add(db_parent)
    db.commit()
    db.refresh(db_parent)
    return db_parent


@app.post("/children", response_model=ChildReadSchema)
async def create_child(child: ChildCreateSchema, db: Session = Depends(get_db)):
    db_child = Child(**child.dict())
    db.add(db_child)
    db.commit()
    db.refresh(db_child)
    return db_child
