from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class Host(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    ip: str
    agents_installed: bool = Field(default=False)
    last_health_status: Optional[str] = None
    last_checked_at: Optional[datetime] = None