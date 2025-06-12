from fastapi import FastAPI
from contextlib import asynccontextmanager

from sindri.db.session import init_db
from sindri.api.routes import hosts

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(hosts.router, prefix="/api")