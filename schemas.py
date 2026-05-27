from enum import Enum
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from typing import Optional
from pydantic import BaseModel, HttpUrl
from datetime import date
from typing import Optional
from typing import List
from datetime import datetime

class ClientStatus(str, Enum):
    active = "A"
    terminated = "T"
    pass_status = "P"
    completed = "C"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    role: str
    employee_id: Optional[str] = None
    client_id: Optional[int] = None
    user_type: Optional[str] = None
    name: Optional[str] = None

class UserCreate(BaseModel):
   
    first_name: str | None = None
    last_name: str | None = None
    mobile: str | None = None
    designation: str | None = None
    email: EmailStr
    password: str
    role: str = "user"
    aadhar_number: Optional[str] = None
    location: Optional[str] = None
    reporting_to: Optional[str] = None
    HR: Optional[str] = None
    notes: Optional[str] = None


class UserLimitedUpdate(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    mobile: Optional[str] = None
    designation: Optional[str] = None
    role: Optional[str] = None
    reporting_to: Optional[str] = None
    HR: Optional[str] = None
    password: Optional[str] = None
    notes: Optional[str] = None


class UserResponse(BaseModel):
    employee_id: str
    email: Optional[str]
    role: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    mobile: Optional[str]
    designation: Optional[str]
    reporting_to: Optional[str]
    reporting_to_name: Optional[str]
    HR: Optional[str]
    hr_name: Optional[str]
    aadhaar_number: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    location: Optional[str]
    notes: Optional[str]
    is_active: Optional[bool]
    
    class Config:
        from_attributes = True

class ClientCreate(BaseModel):
    client_name: str
    mobile: str
    technology: str
    status: ClientStatus
    employee_id: str

class ClientResponse(BaseModel):
    id: int
    client_name: Optional[str]
    mobile: Optional[str]
    email: Optional[str]
    password: Optional[str] =None
    technology: Optional[str]
    status: Optional[str]
    professional_role: Optional[str]
    aadhaar_number: Optional[str]
    location: Optional[str]
    employee_name: Optional[str]
    employee_id: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    notes: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class ClientUpdate(BaseModel):
    client_name: Optional[str] = None
    mobile: Optional[str] = None
    technology: Optional[str] = None
    status: Optional[str] = None
    employee_id: Optional[str] = None

    
class PlatformEnum(str, Enum):
    naukri = "Naukri"
    linkedin = "LinkedIn"
    career_pages = "Career Pages"
    cold_emails = "Cold Emails"
    other = "Other"


class ApplicationCreate(BaseModel):
    platform: PlatformEnum
    company_name: str
    role: str
    date_applied: date
    application_link: Optional[HttpUrl] = None
    notes: Optional[str] = None

class ApplicationUpdate(BaseModel):
    platform: Optional[str] = None
    company_name: Optional[str] = None
    role: Optional[str] = None
    date_applied: Optional[date] = None
    application_link: Optional[str] = None
    notes: Optional[str] = None

class CredentialCreate(BaseModel):

    portal_name:str
    portal_link:str
    username:str
    password:str
    notes:str

class CredentialUpdate(BaseModel):

    portal_name:str | None=None
    portal_link:str | None=None
    username:str | None=None
    password:str | None=None
    notes:str | None=None

class ReportCreate(BaseModel):
    company_name:str
    recruiter_name:Optional[str]=None
    recruiter_contact:Optional[str]=None
    recruiter_email:Optional[str]=None
    type:str
    status:Optional[str]=None
    date:str
    notes:str | None = None

class ReportUpdate(BaseModel):
    company_name: Optional[str]
    recruiter_name: Optional[str]=None
    recruiter_contact: Optional[str]=None
    recruiter_email: Optional[str]=None
    type: Optional[str]
    status: Optional[str]
    date: Optional[date]
    notes: Optional[str]

class SourceLink(BaseModel):
    link: str
    link_type: str

class SourceLinksRequest(BaseModel):
    links: List[SourceLink]
#-------------------------------calander schemas apis-------------------

from datetime import date
from typing import List
from models import DayStatus


class CalendarResponse(BaseModel):
    id: int
    date: date
    status: DayStatus

    class Config:
        from_attributes = True


class CalendarUpdate(BaseModel):
    status: DayStatus


from typing import Optional
from datetime import date
from pydantic import BaseModel
from models import DayStatus


class CalendarWithHoursResponse(BaseModel):
    id: int
    date: date
    status: DayStatus
    total_hours: float = 0

    class Config:
        from_attributes = True


from pydantic import BaseModel, EmailStr
from typing import Optional


class ClientUserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    role: str 



class ClientUserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    
class ClientUserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    role: str
    

    class Config:
        orm_mode = True
