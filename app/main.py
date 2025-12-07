from fastapi import FastAPI, HTTPException
from sqlmodel import select

from core.database import SessionDep
from api.router import api_router

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


app.include_router(api_router, prefix="/api")
