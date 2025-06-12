from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime

class Host(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    ip: str
    agents_installed: bool = False
    last_health_status: Optional[str] = None
    last_checked_at: Optional[datetime] = None
