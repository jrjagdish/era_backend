from pydantic import BaseModel,HttpUrl,Field
from typing import List,Optional, Union
from datetime import datetime

class ScrapeRequest(BaseModel):
    url: Union[HttpUrl, str] 
    

class TeamMember(BaseModel):
    name: str
    role: str
    linkedin: Optional[str] = None
    focus: List[str] = Field(default_factory=list)
    relevance_score: float = 0.0    

class FirmInfo(BaseModel):
    name: str
    description: str
    logo: Optional[str] = None
    website: str

class ScrapeResponse(BaseModel):
    firm: FirmInfo
    team: List[TeamMember]
    cached_at: Optional[datetime] = None        