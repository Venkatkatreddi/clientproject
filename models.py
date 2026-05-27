from sqlalchemy import Column, Integer, String, ForeignKey, Date, Text, Boolean
from database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, DateTime
from datetime import datetime
from sqlalchemy.sql import func


class BlacklistedToken(Base):

    __tablename__ = "blacklisted_tokens"

    id = Column(Integer, primary_key=True, index=True)

    token = Column(String, unique=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    employee_id = Column(String, unique=True, index=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    mobile = Column(String, nullable=True)
    designation = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")
    reporting_to = Column(String, ForeignKey("users.employee_id"), nullable=True)
    HR = Column(String, ForeignKey("users.employee_id"), nullable=True)
    aadhaar_number = Column(String, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    location = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    photo = Column(String, nullable=True)
    documents = Column(String, nullable=True)  
    profile_pic = Column(String, nullable=True)
    created_at = Column(
    DateTime,
    default=datetime.utcnow
)

    updated_at = Column(
    DateTime,
    default=datetime.utcnow,
    onupdate=datetime.utcnow
)
    notes = Column(String, nullable=True)
    
class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String)
    mobile = Column(String)
    technology = Column(String)
    status = Column(String)
    employee_id = Column(String, ForeignKey("users.employee_id"), nullable=True)
    professional_role = Column(String)
    aadhaar_number = Column(String)
    location = Column(String)
    email = Column(String)
    password = Column(String)
    photo = Column(String)
    documents = Column(String)  
    source_links = Column(Text, nullable=True)
    link_type = Column(String,nullable=True)
    profile_picture = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    updated_at = Column(
    DateTime,
    default=datetime.utcnow,
    onupdate=datetime.utcnow
    )


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    company_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    date_applied = Column(Date, nullable=False)
    application_link = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    source = Column(String)
    created_at = Column(
    DateTime,
    default=datetime.utcnow
)
    updated_at = Column(
    DateTime,
    default=datetime.utcnow,
    onupdate=datetime.utcnow
)
    
class Credential(Base):

    __tablename__ = "credentials"

    id = Column(Integer,primary_key=True,index=True)

    client_id = Column(Integer,ForeignKey("clients.id"))

    portal_name = Column(String,nullable=False)
    portal_link = Column(String,nullable=False)
    username = Column(String,nullable=False)
    password = Column(String,nullable=False)
    notes =  Column(String,nullable=True)
    client = relationship("Client")
    created_at = Column(
    DateTime,
    default=datetime.utcnow
)

    updated_at = Column(
    DateTime,
    default=datetime.utcnow,
    onupdate=datetime.utcnow
)

class Reports(Base):

    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)

    client_id = Column(Integer, ForeignKey("clients.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String)
    company_name = Column(String)
    recruiter_name = Column(String,nullable=True)
    recruiter_contact = Column(String,nullable=True)
    recruiter_email = Column(String,nullable=True)
    date = Column(Date)
    status = Column(String, default="PENDING")
    notes = Column(String,nullable=True)
    created_at = Column(
    DateTime,
    default=datetime.utcnow
)

    updated_at = Column(
    DateTime,
    default=datetime.utcnow,
    onupdate=datetime.utcnow
)
    source = Column(String,nullable=True)


    #---------------------------calander apis------------------------------------------

from sqlalchemy import Date, Enum
import enum


class DayStatus(str, enum.Enum):
    normal = "normal"
    publicholiday = "publicholiday"
    leave = "leave"


class Calendar(Base):
    __tablename__ = "calendar"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, nullable=False, index=True)
    status = Column(Enum(DayStatus), default=DayStatus.normal, nullable=False)
    description = Column(String, nullable=True)

class PublicHoliday(Base):
    __tablename__ = "public_holidays"

    id = Column(Integer, primary_key=True, index=True)

    holiday_date = Column(Date, nullable=False, unique=True)

    description = Column(String, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base


class ClientUser(Base):
    __tablename__ = "client_users"

    id = Column(Integer, primary_key=True, index=True)

    

    role = Column(
        String,
        default="client"
    )

    first_name = Column(String, nullable=False)

    last_name = Column(String, nullable=False)

    email = Column(String, unique=True, nullable=False)

    password = Column(String, nullable=False)

    is_active = Column(Boolean, default=True)
