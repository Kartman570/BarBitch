from fastapi import FastAPI, HTTPException
from sqlmodel import select

from app.core.database import SessionDep, create_db_and_tables
from app.api.router import api_router

app = FastAPI()


# @app.on_event("startup") # TODO thats for mvp testing. remove when DB ready
# def on_startup():
#     create_db_and_tables()


@app.get("/")
async def root():
    return {"message": "Hello World"}


app.include_router(api_router, prefix="/api")
