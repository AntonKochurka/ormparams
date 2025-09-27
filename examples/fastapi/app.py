from typing import List

from fastapi import Depends, FastAPI, HTTPException, Request
from models import (
    AsyncSessionLocal,
    Base,
    Post,
    PostCreate,
    PostResponse,
    User,
    UserCreate,
    UserResponse,
    engine,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ormparams import DEFAULT_SUFFIXES, OrmFilter, Parser, ParserRules
from ormparams.fastapi_ext import get_ormparams

app = FastAPI()


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_rules():
    suffix_set = DEFAULT_SUFFIXES

    # you can register here your suffixes

    return ParserRules(suffix_set=suffix_set)


def get_parser(rules: ParserRules = Depends(get_rules)):
    return Parser(rules)


def get_ormfilter(parser: Parser = Depends(get_parser)):
    return OrmFilter(parser)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_user_params(request: Request, parser: Parser = Depends(get_parser)):
    return await get_ormparams(User, parser, exclude=["id"])(request)


@app.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = User(email=user.email, username=user.username)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


@app.get("/users", response_model=List[UserResponse])
async def get_users(
    db: AsyncSession = Depends(get_db),
    params: dict = Depends(get_user_params),
    ormfilter: OrmFilter = Depends(get_ormfilter),
):
    query = ormfilter.filter(User, params).query
    result = await db.execute(query)

    return result.scalars().all()


@app.post("/posts", response_model=PostResponse)
async def create_post(post: PostCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == post.author_id))
    author = result.scalar_one_or_none()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    db_post = Post(title=post.title, author_id=post.author_id)
    db.add(db_post)
    await db.commit()
    await db.refresh(db_post)
    return db_post


async def get_post_params(request: Request, parser: Parser = Depends(get_parser)):
    return await get_ormparams(Post, parser, include=["age"])(request)


@app.get("/posts", response_model=List[PostResponse])
async def get_posts(
    db: AsyncSession = Depends(get_db),
    params: dict = Depends(get_post_params),
    ormfilter: OrmFilter = Depends(get_ormfilter),
):
    query = ormfilter.filter(Post, params, excluded_operations=["le"]).query
    result = await db.execute(query)

    return result.scalars().all()
