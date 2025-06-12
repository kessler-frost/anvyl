from fastapi import APIRouter, HTTPException
from sqlmodel import select
from models import Host
from db import get_session

router = APIRouter()

@router.get("/hosts")
def list_hosts():
    with get_session() as session:
        return session.exec(select(Host)).all()

@router.post("/hosts")
def add_host(host: Host):
    with get_session() as session:
        session.add(host)
        session.commit()
        session.refresh(host)
        return host

@router.delete("/hosts/{host_id}")
def delete_host(host_id: int):
    with get_session() as session:
        host = session.get(Host, host_id)
        if not host:
            raise HTTPException(status_code=404, detail="Host not found")
        session.delete(host)
        session.commit()
        return {"ok": True}

@router.patch("/hosts/{host_id}")
def update_host(host_id: int, updated: Host):
    with get_session() as session:
        host = session.get(Host, host_id)
        if not host:
            raise HTTPException(status_code=404, detail="Host not found")
        for field, value in updated.dict(exclude_unset=True).items():
            setattr(host, field, value)
        session.add(host)
        session.commit()
        session.refresh(host)
        return host
