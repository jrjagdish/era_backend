from pydantic import BaseModel, HttpUrl
from typing import List, Optional

class TeamMember(BaseModel):
    name: str
    email: Optional[str] = None
    linkedin_url: Optional[HttpUrl] = None

class CompanyInfo(BaseModel):
    name: str
    about: Optional[str] = None
    address: Optional[str] = None
    contact_info: Optional[dict] = None
    team_members: List[TeamMember] = []