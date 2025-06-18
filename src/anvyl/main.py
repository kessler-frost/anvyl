from fastapi import FastAPI
from contextlib import asynccontextmanager

from anvyl.db.session import init_db
from anvyl.api.routes import hosts

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(hosts.router, prefix="/api")