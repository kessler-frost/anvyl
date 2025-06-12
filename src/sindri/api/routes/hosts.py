from fastapi import APIRouter, HTTPException, Body
from sqlmodel import select
from sindri.models.host import Host
from sindri.db.session import get_session
from sindri.sdk.install_agents import install_beszel, install_dozzle, install_nomad
import httpx
from datetime import datetime, UTC

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
        for field, value in updated.model_dump(exclude_unset=True).items():
            setattr(host, field, value)
        session.add(host)
        session.commit()
        session.refresh(host)
        return host

@router.post("/hosts/{host_id}/install-agents")
def install_agents(host_id: int, beszel_public_key: str = Body(...)):
    with get_session() as session:
        host = session.get(Host, host_id)
        if not host:
            raise HTTPException(status_code=404, detail="Host not found")

        install_result_beszel = install_beszel(host.ip, public_key=beszel_public_key)
        install_result_dozzle = install_dozzle(host.ip)
        install_result_nomad = install_nomad(host.ip)

        host.agents_installed = True
        session.add(host)
        session.commit()
        session.refresh(host)

    return {
        "host": host.name,
        "ip": host.ip,
        "beszel": str(install_result_beszel),
        "dozzle": str(install_result_dozzle),
        "nomad": str(install_result_nomad),
    }

@router.get("/hosts/{host_id}/status")
def check_host_status(host_id: int):
    with get_session() as session:
        host = session.get(Host, host_id)
        if not host:
            raise HTTPException(status_code=404, detail="Host not found")

    beszel_url = f"http://{host.ip}:45876/health"
    try:
        response = httpx.get(beszel_url, timeout=3)
        if response.status_code == 200:
            status = "healthy"
        else:
            status = f"unhealthy ({response.status_code})"
    except httpx.RequestError:
        status = "unreachable"

    with get_session() as session:
        host = session.get(Host, host_id)
        host.last_health_status = status
        host.last_checked_at = datetime.now(UTC)
        session.add(host)
        session.commit()

    return {"beszel": status}