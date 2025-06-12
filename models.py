from typing import Optional, List
from sqlmodel import SQLModel, Field, Column, JSON

class Host(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    ip: str
    tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    status: str = Field(default="active")
