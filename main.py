from fastapi import FastAPI
from db import init_db
from api.routes import hosts
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(hosts.router, prefix="/api")
