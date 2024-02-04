import sqlalchemy
import databases
from fastapi import FastAPI
import aiosqlite
import logging
from pydantic import BaseModel, Field
from typing import List
import re


DATABASE_URL = "sqlite:///homework6.db"

database = databases.Database(DATABASE_URL)

metadata = sqlalchemy.MetaData()
users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("firstname", sqlalchemy.String(32)),
    sqlalchemy.Column("lastname", sqlalchemy.String(32)),
    sqlalchemy.Column("birthday", sqlalchemy.String(10)),
    sqlalchemy.Column("email", sqlalchemy.String(32)),
    sqlalchemy.Column("address", sqlalchemy.String(32)),
    )

engine = sqlalchemy.create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
metadata.create_all(engine)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


class User(BaseModel):
    firstname: str = Field(min_length=2)
    lastname: str = Field(min_length=2)
    birthday: str = Field("d{4}-\d\d-\d\d")
    email: str = Field(max_length=32)
    address: str = Field(min_length=5)


class UserId(User):
    id: int



@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get("/fake_users/{count}")
async def create_users(count: int):
    for i in range(count):
        query = users.insert().values(firstname=f'user{i}', lastname=f'lastname{i}', birthday=f'{1999+i}-12-{10+i}', email=f'mail{i}@mail.ru', address=f'address{i}')
        await database.execute(query)
    return {'message': f'{count} fake users create'}



@app.get("/")
async def root():
    return {"message": "Homework 6"}



@app.get("/users/", response_model=List[User])
async def read_users():
    query = users.select()
    return await database.fetch_all(query)


@app.put("/users/{user_id}", response_model=User)
async def update_user(user_id: int, new_user: User):
    query = users.update().where(users.c.id == user_id).values(**new_user.dict())
    await database.execute(query)
    return {**new_user.dict(), "id": user_id}


@app.get("/users/{user_id}", response_model=User)
async def read_user(user_id: int):
    query = users.select().where(users.c.id == user_id)
    return await database.fetch_one(query)



@app.post("/users/", response_model=UserId)
async def create_user(user: User):
    query = users.insert().values(**user.model_dump())
    last_record_id = await database.execute(query)
    return {**user.model_dump(), "id": last_record_id}


@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    query = users.delete().where(users.c.id == user_id)
    await database.execute(query)
    return {"message": "User deleted"}