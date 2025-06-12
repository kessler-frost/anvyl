from fastapi import FastAPI
from db import init_db
from api.routes import hosts

app = FastAPI()
app.include_router(hosts.router)

@app.on_event("startup")
def on_startup():
    init_db()
