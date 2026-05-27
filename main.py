from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session
from auth import router as auth_router
from database import engine, get_db
from db_dependencies import admin_only
from schemas import UserCreate, UserResponse, UserLimitedUpdate, ClientCreate, ClientResponse, ReportCreate
from schemas import ClientUpdate, ApplicationUpdate, SourceLinksRequest, SourceLink
from security import hash_password
from db_dependencies import get_db, admin_only, get_current_user
from models import Base, User, Client, Application, Credential, Reports, ClientUser, BlacklistedToken
from schemas import ApplicationCreate, CredentialCreate, CredentialUpdate, ReportUpdate, ClientStatus
from datetime import datetime
from schemas import ClientUserCreate, ClientUserResponse, ClientUserUpdate
from sqlalchemy import func
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import UploadFile, File, Form
from typing import Optional, List
from timesheet_schedular import move_drafts_to_timesheet
from calendar_router import router as calendar_router
from timesheet_router import router as timesheet_router
import timesheet_models
from datetime import date
from timesheet_models import Leave
from fastapi import Query
from fastapi.responses import FileResponse
import os
from fastapi.staticfiles import StaticFiles
from fastapi import UploadFile, File
from typing import List
from sqlalchemy import distinct
from models import PublicHoliday
from timesheet_models import Leave, Timesheet, DraftTimesheet
from sqlalchemy import desc
from fastapi import APIRouter, Query
import requests

app = FastAPI()

os.makedirs("uploads", exist_ok=True)
os.makedirs("uploads/photos", exist_ok=True)
os.makedirs("uploads/docs", exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
print("THIS FILE IS RUNNING")
# ------------------ CORS CONFIG ------------------
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",       
    "http://127.0.0.1:5174", 
    "https://msstechno-timesheet.vercel.app",
    "https://pathway.msstechno.com",
    "https://pathway-project-i1psqt2sa-mss-techno-solutions-projects.vercel.app",
    "https://pathway-project-psi.vercel.app"     
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ------------------ CREATE TABLES ------------------
Base.metadata.create_all(bind=engine)
# ------------------ SCHEDULER (Commented as you kept) ------------------
scheduler = BackgroundScheduler()
scheduler.add_job(
     move_drafts_to_timesheet,
     "cron",
     hour=23,
     minute=59
 )
scheduler.start()
# ------------------ CLIENT ROUTER ------------------
router = APIRouter()

from fastapi import APIRouter, Form, File, UploadFile, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional
import os
import uuid
'''@router.post("/create-client")
async def create_client(
    client_name: str = Form(...),
    mobile: str = Form(...),

    technology: Optional[str] = Form(None),
    status: Optional[str] = Form(None),

    # Employee value example: "MSS001 - John Doe"
    employee_id: str = Form(...),

    # Dates
    start_date: Optional[date] = Form(None),
    end_date: Optional[str] = Form(None),

    professional_role: Optional[str] = Form(None),
    aadhaar_number: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),

    db: Session = Depends(get_db),
    admin=Depends(admin_only)
):
    try:

        # ✅ Extract only employee_id
        if " - " in employee_id:
            emp_id = employee_id.split(" - ")[0].strip()
        else:
            emp_id = employee_id.strip()

        # ✅ Check employee exists
        employee = db.query(User).filter(
            User.employee_id == emp_id
        ).first()

        if not employee:
            raise HTTPException(
                status_code=404,
                detail="Employee not found"
            )

        # ✅ Create client
        new_client = Client(
            client_name=client_name,
            mobile=mobile,
            email=email,
            password=password,
            technology=technology,
            status=status,
            employee_id=emp_id,

            # Dates
            start_date=start_date,
            end_date=end_date,

            professional_role=professional_role,
            aadhaar_number=aadhaar_number,
            location=location,
            notes=notes
        )

        db.add(new_client)
        db.commit()
        db.refresh(new_client)

        # ✅ Display end date text
        display_end_date = (
            "Currently In Process"
            if not new_client.end_date
            else str(new_client.end_date)
        )

        return {
            "message": "Client created successfully",

            "client": {
                "id": new_client.id,
                "client_name": new_client.client_name,
                "mobile": new_client.mobile,
                "email": new_client.email,
                "password": new_client.password,
                "technology": new_client.technology,
                "status": new_client.status,

                "employee_id": emp_id,
                "employee_name": f"{employee.first_name} {employee.last_name}",

                "start_date": (
                    str(new_client.start_date)
                    if new_client.start_date
                    else None
                ),

                "end_date": display_end_date,

                "professional_role": new_client.professional_role,
                "aadhaar_number": new_client.aadhaar_number,
                "location": new_client.location,
                "notes": new_client.notes
            }
        }

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )'''

@router.post("/create-client")
async def create_client(
    client_name: str = Form(...),
    mobile: str = Form(...),

    technology: Optional[str] = Form(None),
    status: Optional[str] = Form(None),

    # Employee value example: "MSS001 - John Doe"
    employee_id: str = Form(...),

    # Dates
    start_date: Optional[date] = Form(None),
    end_date: Optional[str] = Form(None),

    professional_role: Optional[str] = Form(None),
    aadhaar_number: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),

    db: Session = Depends(get_db),

    # ✅ Admin & Super Admin Access
    current_user=Depends(admin_only)
):
    try:

        # ==========================================
        # EXTRACT EMPLOYEE ID
        # ==========================================

        if " - " in employee_id:
            emp_id = employee_id.split(" - ")[0].strip()
        else:
            emp_id = employee_id.strip()

        # ==========================================
        # CHECK EMPLOYEE EXISTS
        # ==========================================

        employee = db.query(User).filter(
            User.employee_id == emp_id
        ).first()

        if not employee:
            raise HTTPException(
                status_code=404,
                detail="Employee not found"
            )

        # ==========================================
        # CHECK EMAIL ALREADY EXISTS
        # ==========================================

        if email:

            existing_client = db.query(Client).filter(
                Client.email == email.strip().lower()
            ).first()

            if existing_client:
                raise HTTPException(
                    status_code=400,
                    detail="Email already exists"
                )

        # ==========================================
        # CREATE CLIENT
        # ==========================================

        new_client = Client(
            client_name=client_name,
            mobile=mobile,
            email=email.strip().lower() if email else None,
            password=password,
            technology=technology,
            status=status,
            employee_id=emp_id,

            # Dates
            start_date=start_date,
            end_date=end_date,

            professional_role=professional_role,
            aadhaar_number=aadhaar_number,
            location=location,
            notes=notes
        )

        db.add(new_client)
        db.commit()
        db.refresh(new_client)

        # ==========================================
        # DISPLAY END DATE
        # ==========================================

        display_end_date = (
            "Currently In Process"
            if not new_client.end_date
            else str(new_client.end_date)
        )

        return {
            "message": "Client created successfully",

            "client": {
                "id": new_client.id,
                "client_name": new_client.client_name,
                "mobile": new_client.mobile,
                "email": new_client.email,
                "password": new_client.password,
                "technology": new_client.technology,
                "status": new_client.status,

                "employee_id": emp_id,
                "employee_name": f"{employee.first_name} {employee.last_name}",

                "start_date": (
                    str(new_client.start_date)
                    if new_client.start_date
                    else None
                ),

                "end_date": display_end_date,

                "professional_role": new_client.professional_role,
                "aadhaar_number": new_client.aadhaar_number,
                "location": new_client.location,
                "notes": new_client.notes
            }
        }

    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
#------------------update client---------------------------



@router.put("/update-client/{client_id}")
async def update_client(
    client_id: int,

    client_name: str = Form(...),
    mobile: str = Form(...),

    technology: Optional[str] = Form(None),
    status: Optional[str] = Form("In Process"),

    # Employee value example: "MSS001 - John Doe"
    employee_id: str = Form(...),

    # Dates
    start_date: Optional[date] = Form(None),
    end_date: Optional[str] = Form(None),

    professional_role: Optional[str] = Form(None),
    aadhaar_number: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),

    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:

        # ✅ Find existing client
        client = db.query(Client).filter(
            Client.id == client_id
        ).first()

        if not client:
            raise HTTPException(
                status_code=404,
                detail="Client not found"
            )

        # ✅ Extract clean employee_id
        if " - " in employee_id:
            emp_id = employee_id.split(" - ")[0].strip()
        else:
            emp_id = employee_id.strip()

        # ✅ Validate employee exists
        employee = db.query(User).filter(
            User.employee_id == emp_id
        ).first()

        if not employee:
            raise HTTPException(
                status_code=404,
                detail="Employee not found"
            )

        # ✅ Update fields
        client.client_name = client_name
        client.mobile = mobile
        client.technology = technology
        client.status = status
        client.employee_id = emp_id

        # Dates
        client.start_date = start_date
        client.end_date = end_date

        client.professional_role = professional_role
        client.aadhaar_number = aadhaar_number
        client.location = location
        client.email = email
        client.password = password
        client.notes = notes

        db.commit()
        db.refresh(client)

        # ✅ Display end date text
        display_end_date = (
            "Currently In Process"
            if not client.end_date
            else str(client.end_date)
        )

        # ✅ Response
        return {
            "message": "Client updated successfully",

            "client": {
                "id": client.id,
                "client_name": client.client_name,
                "mobile": client.mobile,
                "email": client.email,
                "password": client.password,
                "technology": client.technology,
                "status": client.status,

                "employee_id": emp_id,
                "employee_name": f"{employee.first_name} {employee.last_name}",

                "start_date": (
                    str(client.start_date)
                    if client.start_date
                    else None
                ),

                "end_date": display_end_date,

                "professional_role": client.professional_role,
                "aadhaar_number": client.aadhaar_number,
                "location": client.location,
                "notes": client.notes
            }
        }

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

#----------------------to add source links---------------
@router.post("/clients/{client_id}/add-source-links")
def add_source_links(
    client_id: int,
    request: SourceLinksRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    clean_links = []

    for item in request.links:
        # extra safety (even though Pydantic validates)
        if item.link and item.link_type:
            clean_links.append(f"{item.link}::{item.link_type}")

    existing = client.source_links.split(",") if client.source_links else []

    # جلوگیری duplicates
    all_links = list(set(existing + clean_links))

    client.source_links = ",".join(all_links)

    db.commit()
    db.refresh(client)

    formatted = [
        {"link": entry.split("::")[0], "link_type": entry.split("::")[1]}
        for entry in all_links if "::" in entry
    ]

    return {
        "message": "Source links added successfully",
        "client_id": client.id,
        "source_links": formatted
    }

#--------------get source link---------------------

@router.get("/clients/{client_id}/source-links")
def get_source_links(
    client_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
    
):
    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    raw_links = client.source_links.split(",") if client.source_links else []

    formatted = [
        {"link": entry.split("::")[0], "link_type": entry.split("::")[1]}
        for entry in raw_links if "::" in entry
    ]

    return {
        "client_id": client.id,
        "source_links": formatted
    }
#-----------------------delete source link-------------
@router.delete("/clients/{client_id}/delete-source-link")
def delete_source_link(
    client_id: int,
    link: str,  # only URL
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
    
):
    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if not client.source_links:
        raise HTTPException(status_code=400, detail="No links to delete")

    existing = client.source_links.split(",")

    # remove by matching URL part
    updated_links = [
        l for l in existing if not l.startswith(link + "::")
    ]

    if len(existing) == len(updated_links):
        raise HTTPException(status_code=404, detail="Link not found")

    client.source_links = ",".join(updated_links) if updated_links else None

    db.commit()
    db.refresh(client)

    return {
        "message": "Source link deleted successfully",
        "client_id": client.id,
        "source_links": updated_links
    }

#-----------------client profile------------------------
@router.get("/client-profile/{client_id}")
def get_client_profile(
    client_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    import time

    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # ✅ BASE URL (PRODUCTION SAFE)
    base_url = "https://timesheet-api-790373899641.asia-south1.run.app"

    # ✅ PHOTO URL
    photo_url = None
    if client.photo:
        filename = client.photo.split("/")[-1]
        photo_url = f"{base_url}/clients/photos/{filename}?t={int(time.time())}"

    # ✅ DOCUMENTS
    documents_list = []
    if client.documents:
        for doc in client.documents.split(","):
            filename = doc.split("/")[-1]

            documents_list.append({
                "file_name": filename,
                "view_url": f"{base_url}/clients/documents/{filename}",
                "download_url": f"{base_url}/clients/documents/{filename}?download=true"
            })

    return {
        "client_id": client.id,
        "client_name": client.client_name,
        "professional_role": client.professional_role,
        "mobile": client.mobile,
        "email": client.email,
        "aadhaar_number": client.aadhaar_number,
        "location": client.location,

        "photo": photo_url,
        "documents": documents_list
    }
#--------------------get clients----------------------------

'''@router.get("/clients", response_model=list[ClientResponse])
def get_clients(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    # 🔹 Get logged-in user
    user = db.query(User).filter(
        User.id == current_user["id"]
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # 🔹 Single optimized query using JOIN
    query = db.query(
        Client,
        User.first_name,
        User.last_name
    ).outerjoin(
        User,
        Client.employee_id == User.employee_id
    )

    # 🔹 Role filter
    if current_user["role"] != "admin":

        query = query.filter(
            Client.employee_id == user.employee_id
        )

    # 🔹 Latest updated/created first
    clients = query.order_by(
        Client.updated_at.desc(),
        Client.created_at.desc()
    ).all()

    response = []

    for client, first_name, last_name in clients:

        employee_name = (
            f"{first_name or ''} {last_name or ''}"
        ).strip()

        display_end_date = (
            "Currently In Process"
            if not client.end_date
            else str(client.end_date)
        )

        response.append({

            "id": client.id,
            "client_name": client.client_name,
            "mobile": client.mobile,
            "email": client.email,
            "technology": client.technology,
            "status": client.status,

            "employee_id": client.employee_id,
            "employee_name": employee_name,

            "start_date": (
                str(client.start_date)
                if client.start_date
                else None
            ),

            "end_date": display_end_date,

            "professional_role": client.professional_role,
            "aadhaar_number": client.aadhaar_number,
            "location": client.location,
            "notes": client.notes,

            "created_at": client.created_at,
            "updated_at": client.updated_at
        })

    return response'''

@router.get("/clients", response_model=list[ClientResponse])
def get_clients(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    # 🔹 Super Admin handling
    if current_user["role"] == "super admin":

        user_employee_id = None

    else:

        # 🔹 Get logged-in user
        user = db.query(User).filter(
            User.id == current_user["id"]
        ).first()

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        user_employee_id = user.employee_id

    # 🔹 Single optimized query using JOIN
    query = db.query(
        Client,
        User.first_name,
        User.last_name
    ).outerjoin(
        User,
        Client.employee_id == User.employee_id
    )

    # 🔹 Role filter
    # Super Admin & Admin → See all clients
    # Users → See only own clients

    if current_user["role"] not in ["admin", "super admin"]:

        query = query.filter(
            Client.employee_id == user_employee_id
        )

    # 🔹 Latest updated/created first
    clients = query.order_by(
        Client.updated_at.desc(),
        Client.created_at.desc()
    ).all()

    response = []

    for client, first_name, last_name in clients:

        employee_name = (
            f"{first_name or ''} {last_name or ''}"
        ).strip()

        display_end_date = (
            "Currently In Process"
            if not client.end_date
            else str(client.end_date)
        )

        response.append({

            "id": client.id,
            "client_name": client.client_name,
            "mobile": client.mobile,
            "email": client.email,
            "technology": client.technology,
            "status": client.status,
            "password": client.password,
            "employee_id": client.employee_id,
            "employee_name": employee_name,

            "start_date": (
                str(client.start_date)
                if client.start_date
                else None
            ),

            "end_date": display_end_date,

            "professional_role": client.professional_role,
            "aadhaar_number": client.aadhaar_number,
            "location": client.location,
            "notes": client.notes,

            "created_at": client.created_at,
            "updated_at": client.updated_at
        })

    return response



#------------------get client by id--------------------
'''@router.get("/clients/{client_id}", response_model=ClientResponse)
def get_client_by_id(
    client_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    # 🔹 Get logged-in user
    user = db.query(User).filter(
        User.id == current_user["id"]
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # 🔹 Get client
    client = db.query(Client).filter(
        Client.id == client_id
    ).first()

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )

    # 🔐 Role-based access check
    if current_user["role"] != "admin":

        if client.employee_id != user.employee_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to access this client"
            )

    # 🔹 Get employee details
    emp_user = db.query(User).filter(
        User.employee_id == client.employee_id
    ).first()

    employee_name = None

    if emp_user:
        employee_name = (
            f"{emp_user.first_name or ''} "
            f"{emp_user.last_name or ''}"
        ).strip()

    # 🔹 End date display
    display_end_date = (
        "Currently In Process"
        if not client.end_date
        else str(client.end_date)
    )

    # 🔹 Return response
    return {
        "id": client.id,
        "client_name": client.client_name,
        "mobile": client.mobile,
        "email": client.email,
        "password": client.password,
        "technology": client.technology,
        "status": client.status,

        "employee_id": client.employee_id,
        "employee_name": employee_name,

        # Dates
        "start_date": (
            str(client.start_date)
            if client.start_date
            else None
        ),

        "end_date": display_end_date,

        "professional_role": client.professional_role,
        "aadhaar_number": client.aadhaar_number,
        "location": client.location,
        "notes": client.notes,

        # Timestamps
        "created_at": client.created_at,
        "updated_at": client.updated_at
    }'''

@router.get("/clients/{client_id}", response_model=ClientResponse)
def get_client_by_id(
    client_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    # ==========================================
    # GET CLIENT
    # ==========================================

    client = db.query(Client).filter(
        Client.id == client_id
    ).first()

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )

    # ==========================================
    # ROLE-BASED ACCESS CHECK
    # ==========================================

    # Only admin & super admin can access all clients
    if current_user["role"] not in ["admin", "super admin"]:

        # Get logged-in user
        user = db.query(User).filter(
            User.id == current_user["id"]
        ).first()

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # Employee can access only assigned clients
        if client.employee_id != user.employee_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to access this client"
            )

    # ==========================================
    # GET EMPLOYEE DETAILS
    # ==========================================

    emp_user = db.query(User).filter(
        User.employee_id == client.employee_id
    ).first()

    employee_name = None

    if emp_user:
        employee_name = (
            f"{emp_user.first_name or ''} "
            f"{emp_user.last_name or ''}"
        ).strip()

    # ==========================================
    # END DATE DISPLAY
    # ==========================================

    display_end_date = (
        "Currently In Process"
        if not client.end_date
        else str(client.end_date)
    )

    # ==========================================
    # RESPONSE
    # ==========================================

    return {
        "id": client.id,
        "client_name": client.client_name,
        "mobile": client.mobile,
        "email": client.email,

        # ❌ Do NOT expose password in APIs
        # "password": client.password,

        "technology": client.technology,
        "status": client.status,

        "employee_id": client.employee_id,
        "employee_name": employee_name,

        # Dates
        "start_date": (
            str(client.start_date)
            if client.start_date
            else None
        ),

        "end_date": display_end_date,

        "professional_role": client.professional_role,
        "aadhaar_number": client.aadhaar_number,
        "location": client.location,
        "notes": client.notes,

        # Timestamps
        "created_at": client.created_at,
        "updated_at": client.updated_at
    }
#--------------------------delete client-----------------------

@router.delete("/clients/{client_id}")
def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:

        client = db.query(Client).filter(
            Client.id == client_id
        ).first()

        if not client:
            raise HTTPException(
                status_code=404,
                detail="Client not found"
            )

        # ✅ Delete applications
        db.query(Application).filter(
            Application.client_id == client_id
        ).delete()

        # ✅ Delete reports
        db.query(Reports).filter(
            Reports.client_id == client_id
        ).delete()

        # ✅ Delete credentials
        db.query(Credential).filter(
            Credential.client_id == client_id
        ).delete()

        # ✅ Finally delete client
        db.delete(client)

        db.commit()

        return {
            "success": True,
            "message": "Client deleted successfully"
        }

    except Exception as e:

        db.rollback()

        return {
            "success": False,
            "message": f"Something went wrong: {str(e)}"
        }
#-------------------application router----------
application_router = APIRouter(prefix="/applications", tags=["Applications"])

@application_router.post("/create_application/{client_id}")
def create_application(

    client_id:int,   # from URL
    data: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):

    client = db.query(Client).filter(
        Client.id == client_id
    ).first()

    if not client:
        return {"message":"Client not found"}


    new_application = Application(

        client_id=client_id,   # from URL (FIX)
        platform=data.platform.value,
        company_name=data.company_name,
        role=data.role,
        date_applied=data.date_applied,
        application_link=str(data.application_link) if data.application_link else None,
        notes=data.notes
    )

    db.add(new_application)
    db.commit()
    db.refresh(new_application)

    return {
        "message":"Application saved successfully"
    }

from sqlalchemy import func
'''@application_router.get("/applications/{client_id}")
def get_applications(
    client_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    # 🔹 Get client
    client = db.query(Client).filter(
        Client.id == client_id
    ).first()

    if not client:
        return {"message": "Client not found"}

    # 🔹 Latest updated/created first
    applications = db.query(Application).filter(
        Application.client_id == client_id
    ).order_by(
        Application.updated_at.desc(),
        Application.created_at.desc()
    ).all()

    # 🔹 Stats
    stats_query = db.query(
        Application.platform,
        func.count(Application.id)
    ).filter(
        Application.client_id == client_id
    ).group_by(
        Application.platform
    ).all()

    stats = {
        "Naukri": 0,
        "LinkedIn": 0,
        "Career Pages": 0,
        "Cold Emails": 0,
        "Other": 0
    }

    for platform, count in stats_query:

        if platform in stats:
            stats[platform] = count
        else:
            stats["Other"] += count

    # 🔹 Platform grouped data
    platform_data = {
        "Naukri": [],
        "LinkedIn": [],
        "Career Pages": [],
        "Cold Emails": [],
        "Other": []
    }

    for app in applications:

        application_obj = {

            "id": app.id,
            "company_name": app.company_name,
            "role": app.role,

            "date": (
                app.date_applied.strftime("%b %d, %Y")
                if app.date_applied
                else None
            ),

            "application_link": app.application_link,
            "platform": app.platform,

            # timestamps
            "created_at": app.created_at,
            "updated_at": app.updated_at
        }

        if app.platform in platform_data:
            platform_data[app.platform].append(application_obj)
        else:
            platform_data["Other"].append(application_obj)

    return {
        "stats": stats,
        "applications": platform_data
    }'''

@application_router.get("/applications/{client_id}")
def get_applications(
    client_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    # ==========================================
    # ✅ Get client
    # ==========================================

    client = db.query(Client).filter(
        Client.id == client_id
    ).first()

    if not client:
        return {"message": "Client not found"}

    # ==========================================
    # ✅ Get applications (latest first)
    # ==========================================

    applications = db.query(Application).filter(
        Application.client_id == client_id
    ).order_by(
        Application.updated_at.desc(),
        Application.created_at.desc()
    ).all()

    # ==========================================
    # ✅ Stats
    # ==========================================

    stats_query = db.query(
        Application.platform,
        func.count(Application.id)
    ).filter(
        Application.client_id == client_id
    ).group_by(
        Application.platform
    ).all()

    stats = {
        "Naukri": 0,
        "LinkedIn": 0,
        "Career Pages": 0,
        "Cold Emails": 0,
        "Other": 0
    }

    for platform, count in stats_query:
        if platform in stats:
            stats[platform] = count
        else:
            stats["Other"] += count

    # ==========================================
    # ✅ Data containers
    # ==========================================

    all_applications = []
    platform_data = {
        "Naukri": [],
        "LinkedIn": [],
        "Career Pages": [],
        "Cold Emails": [],
        "Other": []
    }

    # ==========================================
    # ✅ Process applications
    # ==========================================

    for app in applications:

        application_obj = {
            "id": app.id,
            "company_name": app.company_name,
            "role": app.role,
            "date": (
                app.date_applied.strftime("%b %d, %Y")
                if app.date_applied
                else None
            ),
            "application_link": app.application_link,
            "platform": app.platform,
            "created_at": app.created_at,
            "updated_at": app.updated_at
        }

        # ✅ ALL TAB (important fix)
        all_applications.append(application_obj)

        # ✅ PLATFORM WISE GROUPING
        if app.platform in platform_data:
            platform_data[app.platform].append(application_obj)
        else:
            platform_data["Other"].append(application_obj)

    # ==========================================
    # ✅ FINAL RESPONSE
    # ==========================================

    return {
        "stats": stats,
        "all_applications": all_applications,
        "applications": platform_data
    }

@application_router.put("/update/{application_id}")
def update_application(

    application_id: int,
    data: ApplicationUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)

):

    application = db.query(Application).filter(
        Application.id == application_id
    ).first()

    if not application:
        return {"message": "Application not found"}

    if data.platform:
        application.platform = data.platform

    if data.company_name:
        application.company_name = data.company_name

    if data.role:
        application.role = data.role

    if data.date_applied:
        application.date_applied = data.date_applied

    if data.application_link:
        application.application_link = str(data.application_link)

    if data.notes:
        application.notes = data.notes

    db.commit()
    db.refresh(application)

    return {
        "message": "Application updated successfully",
        "application_id": application.id
    }

@application_router.get("/applcations/application_id")
def get_application(application_id:int,db:Session = Depends(get_db),current_user = Depends(get_current_user)):
    application=db.query(Application).filter(Application.id == application_id).first()
    if not application:
        return {"message":"Application not found"}
    return {
        "id":application.id,
        "platform":application.platform,
        "company_name":application.company_name,
        "role":application.role,
        "date_applied":application.date_applied,
        "application_link":application.application_link,
        "notes":application.notes
    } 
 
@application_router.delete("/delete/{application_id}")
def delete_application(

    application_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)

):

    application = db.query(Application).filter(
        Application.id == application_id
    ).first()

    if not application:
        return {"message": "Application not found"}

    db.delete(application)
    db.commit()

    return {
        "message": "Application deleted successfully"
    }
#-----------------credentials routers--------------
Credential_router = APIRouter(
    prefix="/credentials",
    tags=["Credentials"]
)
@Credential_router.post("/create_credentials/{client_id}")
def create_credential(

    client_id:int,
    data:CredentialCreate,

    db:Session = Depends(get_db),
    current_user = Depends(get_current_user)

):

    client = db.query(Client).filter(
        Client.id == client_id
    ).first()

    if not client:
        return {"message":"Client not found"}

   

    new_credential = Credential(

        client_id=client_id,

        portal_name=data.portal_name,
        portal_link=data.portal_link,
        username=data.username,
        password=data.password,
        notes=data.notes
    )

    db.add(new_credential)

    db.commit()

    db.refresh(new_credential)

    return {

        "message":"Credential added successfully",

        "data":{
            "id":new_credential.id,
            "portal_name":new_credential.portal_name,
            "username":new_credential.username
        }
    }

'''@Credential_router.get("/{client_id}")
def get_credentials(

    client_id:int,
    db:Session = Depends(get_db)

):

    client = db.query(Client).filter(
        Client.id == client_id
    ).first()

    if not client:
        raise HTTPException(404,"Client not found")

    credentials = db.query(Credential).filter(
        Credential.client_id == client_id
    ).all()

    result=[]

    for cred in credentials:

        result.append({

            "id":cred.id,
            "portal_name":cred.portal_name,
            "portal_link":cred.portal_link,
            "username":cred.username,
            "password":cred.password,
            "notes":cred.notes
        })

    return {
        "credentials":result
    }'''

@Credential_router.get("/{client_id}")
def get_credentials(

    client_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)

):

    # 🔹 Check client
    client = db.query(Client).filter(
        Client.id == client_id
    ).first()

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )

    # 🔹 Latest updated/created first
    credentials = db.query(Credential).filter(
        Credential.client_id == client_id
    ).order_by(
        Credential.updated_at.desc(),
        Credential.created_at.desc()
    ).all()

    result = []

    for cred in credentials:

        result.append({

            "id": cred.id,
            "portal_name": cred.portal_name,
            "portal_link": cred.portal_link,
            "username": cred.username,
            "password": cred.password,
            "notes": cred.notes,

            # timestamps
            "created_at": cred.created_at,
            "updated_at": cred.updated_at
        })

    return {
        "credentials": result
    }
    

@Credential_router.put("/update/{credential_id}")
def update_credential(

    credential_id:int,
    data:CredentialUpdate,
    db:Session = Depends(get_db),
    current_user = Depends(get_current_user)

):

    credential = db.query(Credential).filter(
        Credential.id == credential_id
    ).first()

    if not credential:
        raise HTTPException(404,"Credential not found")

    if data.portal_name:
        credential.portal_name = data.portal_name
    
    if data.portal_link:
        credential.portal_link = data.portal_link
        
    if data.username:
        credential.username = data.username

    if data.password:
        credential.password = data.password
   
    if data.notes:
        credential.notes = data.notes

    db.commit()
    db.refresh(credential)

    return {
        "message":"Updated successfully",
        "credential_id":credential.id
    }

@Credential_router.get("/credentials/{credential_id}")
def get_credentials(credential_id:int,db:Session = Depends(get_db),current_user = Depends(get_current_user)):
    credential=db.query(Credential).filter(Credential.id == credential_id).first()
    if not credential:
        raise HTTPException(404,"credential not found")

    return{
        "id":credential.id,
        "portal_name":credential.portal_name,
        "portal_link":credential.portal_link,
        "username":credential.username,
        "password":credential.password,
        "notes":credential.notes
    }


@Credential_router.delete("/delete/{credential_id}")
def delete_credential(

    credential_id:int,
    db:Session = Depends(get_db),
    current_user = Depends(get_current_user)

):

    credential = db.query(Credential).filter(
        Credential.id == credential_id
    ).first()

    if not credential:
        raise HTTPException(404,"Credential not found")

    db.delete(credential)
    db.commit()

    return {"message":"Deleted successfully"}
        #------------------reports Api-------------------------------

reports_router = APIRouter(prefix="/reports", tags=["Reports"])

@reports_router.post("/clients/{client_id}/reports")
def create_report(

    client_id:int,
    data: ReportCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):

    client = db.query(Client).filter(
        Client.id == client_id
    ).first()

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )


    new_report = Reports(

        client_id = client_id,
        user_id = None if current_user["role"] == "super admin" else current_user["id"],
        company_name = data.company_name,
        recruiter_name = data.recruiter_name,
        recruiter_contact = data.recruiter_contact,
        recruiter_email = data.recruiter_email,
        type = data.type,
        status = data.status,
        date = data.date,
        notes = data.notes
    )

    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    return {
        "message":"Report added successfully"
    }


'''@reports_router.get("/clients/{client_id}/reports")
def get_reports(
    client_id: int,
    db: Session = Depends(get_db)
):

    # ===================================================
    # ✅ Check client
    # ===================================================

    client = db.query(Client).filter(
        Client.id == client_id
    ).first()

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )

    # ===================================================
    # ✅ Get reports
    # ===================================================

    reports = db.query(Reports).filter(
        Reports.client_id == client_id
    ).order_by(
        Reports.updated_at.desc(),
        Reports.created_at.desc()
    ).all()

    # ===================================================
    # ✅ Stats
    # ===================================================

    stats = {
        "calls_received": 0,
        "mails_received": 0,
        "l1_interviews": 0,
        "l2_interviews": 0,
        "offer_letters": 0
    }

    companies = {}

    # ===================================================
    # ✅ Normalize stage
    # ===================================================

    def normalize(stage):

        if not stage:
            return ""

        stage = stage.lower().strip()

        if "call" in stage:
            return "call"

        if "mail" in stage:
            return "mail"

        if "l1" in stage:
            return "l1"

        if "l2" in stage:
            return "l2"

        if "offer" in stage:
            return "offer"

        return stage

    order = ["call", "mail", "l1", "l2", "offer"]

    # ===================================================
    # ✅ Process Reports
    # ===================================================

    for r in reports:

        company_key = (r.company_name or "").lower().strip()

        stage = normalize(r.type)

        status = (r.status or "").strip()

        # ---------------------------------------------------
        # ✅ Create company object once
        # ---------------------------------------------------

        if company_key not in companies:

            companies[company_key] = {

                "report_id": r.id,

                "company": r.company_name,
                "created_date": (
                    r.created_at.strftime("%Y-%m-%d")
                    if r.created_at
                    else None
                ),


                "stages": []
            }

        # ---------------------------------------------------
        # ✅ Add stage history
        # ---------------------------------------------------

        companies[company_key]["stages"].append({

            "stage": stage,

            "status": status,

            "date": (
                r.date.strftime("%Y-%m-%d")
                if r.date
                else None
            )
        })

        # ---------------------------------------------------
        # ✅ Stats
        # ---------------------------------------------------

        if status.lower() == "cleared": 

            if stage == "call":
                stats["calls_received"] += 1
                
            elif stage == "mail":
                stats["mails_received"] += 1
            
            elif stage == "l1":
                stats["l1_interviews"] += 1
                
            elif stage == "l2":
                stats["l2_interviews"] += 1
                
            elif stage == "offer":
                stats["offer_letters"] += 1
    # ===================================================
    # ✅ Final Response
    # ===================================================

    return {
        "client_id": client.id,
        "client_name": client.client_name,
        "pipeline_overview": stats,
        "company_progression": list(companies.values())
    }'''

@reports_router.get("/clients/{client_id}/reports")
def get_reports(
    client_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):

    # ===================================================
    # ✅ CHECK CLIENT
    # ===================================================

    client = db.query(Client).filter(
        Client.id == client_id
    ).first()

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )

    # ===================================================
    # ✅ GET REPORTS
    # ===================================================

    reports = db.query(Reports).filter(
        Reports.client_id == client_id
    ).order_by(
        Reports.updated_at.desc(),
        Reports.created_at.desc()
    ).all()

    # ===================================================
    # ✅ STATS
    # ===================================================

    stats = {
        "calls_received": 0,
        "mails_received": 0,
        "l1_interviews": 0,
        "l2_interviews": 0,
        "offer_letters": 0
    }

    companies = {}

    # ===================================================
    # ✅ PIPELINE STAGES ORDER
    # ===================================================

    PIPELINE_STAGES = [
        "call",
        "mail",
        "l1",
        "l2",
        "offer"
    ]

    # ===================================================
    # ✅ NORMALIZE STAGE
    # ===================================================

    def normalize(stage):

        if not stage:
            return ""

        stage = stage.lower().strip()

        if "call" in stage:
            return "call"

        if "mail" in stage:
            return "mail"

        if "l1" in stage:
            return "l1"

        if "l2" in stage:
            return "l2"

        if "offer" in stage:
            return "offer"

        return stage

    # ===================================================
    # ✅ PROCESS REPORTS
    # ===================================================

    for r in reports:

        company_key = (r.company_name or "").lower().strip()

        stage = normalize(r.type)

        status = (r.status or "").strip()

        # ---------------------------------------------------
        # ✅ CREATE COMPANY OBJECT
        # ---------------------------------------------------

        if company_key not in companies:

            companies[company_key] = {

                "report_id": r.id,

                "company": r.company_name,

                "created_date": (
                    r.created_at.strftime("%Y-%m-%d")
                    if r.created_at
                    else None
                ),

                # temporary storage
                "stage_map": {}
            }

        # ---------------------------------------------------
        # ✅ STORE ACTUAL STAGE
        # ---------------------------------------------------

        companies[company_key]["stage_map"][stage] = {

            "stage": stage,

            "status": status,

            "date": (
                r.date.strftime("%Y-%m-%d")
                if r.date
                else None
            )
        }

        # ---------------------------------------------------
        # ✅ STATS COUNT
        # ---------------------------------------------------

        if status.lower() == "cleared":

            if stage == "call":
                stats["calls_received"] += 1

            elif stage == "mail":
                stats["mails_received"] += 1

            elif stage == "l1":
                stats["l1_interviews"] += 1

            elif stage == "l2":
                stats["l2_interviews"] += 1

            elif stage == "offer":
                stats["offer_letters"] += 1

    # ===================================================
    # ✅ BUILD COMPLETE PIPELINE
    # ===================================================

    final_companies = []

    for company in companies.values():

        stage_map = company.pop("stage_map")

        completed_stages = list(stage_map.keys())

        highest_index = -1

        # ---------------------------------------------------
        # ✅ FIND HIGHEST COMPLETED STAGE
        # ---------------------------------------------------

        for s in completed_stages:

            if s in PIPELINE_STAGES:

                idx = PIPELINE_STAGES.index(s)

                if idx > highest_index:
                    highest_index = idx

        final_stages = []

        # ---------------------------------------------------
        # ✅ CREATE FULL PIPELINE
        # ---------------------------------------------------

        for i, stage_name in enumerate(PIPELINE_STAGES):

            # actual stage exists
            if stage_name in stage_map:

                final_stages.append(stage_map[stage_name])

            else:

                # previous skipped stages
                if i < highest_index:

                    final_stages.append({

                        "stage": stage_name,

                        "status": "Skipped",

                        "date": None
                    })

        company["stages"] = final_stages

        final_companies.append(company)

    # ===================================================
    # ✅ FINAL RESPONSE
    # ===================================================

    return {

        "client_id": client.id,

        "client_name": client.client_name,

        "pipeline_overview": stats,

        "company_progression": final_companies
    }

@reports_router.get("/reports/{report_id}")
def get_single_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    report = db.query(Reports).filter(
        Reports.id == report_id
    ).first()

    if not report:
        raise HTTPException(404, "Report not found")

    return {
        "id": report.id,
        "company_name": report.company_name,
        "recruiter_name": report.recruiter_name,
        "recruiter_contact": report.recruiter_contact,
        "recruiter_email": report.recruiter_email,
        "type": report.type,
        "status": report.status,
        "date": report.date,
        "notes": report.notes
    }
    


from datetime import datetime

@reports_router.put("/reports/{report_id}")
def update_report(
    report_id: int,
    data: ReportUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
    
):

    # ===================================================
    # ✅ Get existing report
    # ===================================================

    old_report = db.query(Reports).filter(
        Reports.id == report_id
    ).first()

    if not old_report:
        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )

    # ===================================================
    # ✅ SAME STAGE UPDATE
    # ===================================================

    if data.type == old_report.type:

        if data.status is not None:
            old_report.status = data.status

        # ✅ update selected date
        if data.date is not None:
            old_report.date = data.date

        # ✅ actual update timestamp
        old_report.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(old_report)

        return {
            "message": "Report updated successfully",
            "report": old_report
        }

    # ===================================================
    # ✅ REMOVE EXISTING SAME STAGE
    # ===================================================

    db.query(Reports).filter(

        Reports.client_id == old_report.client_id,

        Reports.company_name == old_report.company_name,

        Reports.type == data.type

    ).delete()

    # ===================================================
    # ✅ CREATE NEW STAGE ROW
    # ===================================================

    new_report = Reports(

        client_id=old_report.client_id,

        company_name=old_report.company_name,

        recruiter_name=old_report.recruiter_name,

        recruiter_contact=old_report.recruiter_contact,

        recruiter_email=old_report.recruiter_email,

        notes=old_report.notes,

        type=data.type,

        status=data.status,

        # ✅ USER SELECTED DATE
        date=data.date,

        # ✅ REAL DB CREATED TIME
        created_at=datetime.utcnow(),

        # ✅ REAL DB UPDATED TIME
        updated_at=datetime.utcnow()
    )

    db.add(new_report)

    db.commit()

    db.refresh(new_report)

    return {
        "message": "New stage added successfully",
        "report": new_report
    }


@reports_router.delete("/reports/{report_id}")
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    # ==========================================
    # ✅ Fetch report first
    # ==========================================

    report = db.query(Reports).filter(
        Reports.id == report_id
    ).first()

    if not report:
        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )

    # ✅ STORE values BEFORE delete (IMPORTANT FIX)
    company_name = report.company_name
    client_id = report.client_id

    # ==========================================
    # ✅ Delete all related stages
    # ==========================================

    db.query(Reports).filter(
        Reports.client_id == client_id,
        Reports.company_name == company_name
    ).delete(synchronize_session=False)

    db.commit()

    # ==========================================
    # ✅ Safe response (NO ORM ACCESS AFTER DELETE)
    # ==========================================

    return {
        "message": f"All stages for {company_name} deleted successfully"
    }
@reports_router.get("/dashboard/overview/{client_id}")
def get_overview(
    client_id: int,
    db: Session = Depends(get_db)
):

    # =====================================================
    # ✅ CHECK CLIENT
    # =====================================================

    client = db.query(Client).filter(
        Client.id == client_id
    ).first()

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )

    # =====================================================
    # ✅ APPLICATIONS PLATFORM COUNT
    # =====================================================

    applications_data = db.query(
        Application.platform,
        func.count(Application.id).label("count")
    ).filter(
        Application.client_id == client_id
    ).group_by(
        Application.platform
    ).all()

    applications_map = {
        "naukri": 0,
        "linkedin": 0,
        "cold_emails": 0,
        "careers_page": 0,
        "others": 0
    }

    # =====================================================
    # ✅ NORMALIZE PLATFORM
    # =====================================================

    def normalize_platform(platform: str):

        if not platform:
            return "others"

        p = platform.lower().strip()

        if "naukri" in p:
            return "naukri"

        elif "linkedin" in p:
            return "linkedin"

        elif "cold" in p:
            return "cold_emails"

        elif "career" in p:
            return "careers_page"

        return "others"

    # =====================================================
    # ✅ PROCESS APPLICATIONS
    # =====================================================

    for platform, count in applications_data:

        key = normalize_platform(platform)

        applications_map[key] += count

    # =====================================================
    # ✅ GET ONLY CLEARED REPORTS
    # =====================================================

    reports = db.query(Reports).filter(
        Reports.client_id == client_id,
        func.lower(Reports.status) == "cleared"
    ).all()

    # =====================================================
    # ✅ STATS
    # =====================================================

    stats = {
        "calls_received": 0,
        "mails_received": 0,
        "l1_interviews": 0,
        "l2_interviews": 0,
        "offer_letters": 0
    }

    # =====================================================
    # ✅ PIPELINE ORDER
    # =====================================================

    PIPELINE_STAGES = [
        "call",
        "mail",
        "l1",
        "l2",
        "offer"
    ]

    # =====================================================
    # ✅ NORMALIZE STAGE
    # =====================================================

    def normalize_stage(stage):

        if not stage:
            return ""

        s = stage.lower().strip()

        if "call" in s:
            return "call"

        if "mail" in s:
            return "mail"

        if "l1" in s:
            return "l1"

        if "l2" in s:
            return "l2"

        if "offer" in s:
            return "offer"

        return ""

    # =====================================================
    # ✅ COMPANY HIGHEST STAGE
    # =====================================================

    company_highest_stage = {}

    for r in reports:

        company_key = (
            (r.company_name or "")
            .lower()
            .strip()
        )

        stage = normalize_stage(r.type)

        if stage not in PIPELINE_STAGES:
            continue

        current_index = PIPELINE_STAGES.index(stage)

        # keep highest stage only
        if (
            company_key not in company_highest_stage
            or
            current_index >
            company_highest_stage[company_key]
        ):

            company_highest_stage[
                company_key
            ] = current_index

    # =====================================================
    # ✅ COUNT STAGES
    # =====================================================

    for highest_index in company_highest_stage.values():

        if highest_index >= 0:
            stats["calls_received"] += 1

        if highest_index >= 1:
            stats["mails_received"] += 1

        if highest_index >= 2:
            stats["l1_interviews"] += 1

        if highest_index >= 3:
            stats["l2_interviews"] += 1

        if highest_index >= 4:
            stats["offer_letters"] += 1

    # =====================================================
    # ✅ FINAL RESPONSE
    # =====================================================

    return {

        "client_id": client.id,

        "client_name": client.client_name,

        "applications_by_platform": [

            {
                "name": "Naukri",
                "count": applications_map["naukri"]
            },

            {
                "name": "LinkedIn",
                "count": applications_map["linkedin"]
            },

            {
                "name": "Career Pages",
                "count": applications_map["careers_page"]
            },

            {
                "name": "Cold Emails",
                "count": applications_map["cold_emails"]
            },

            {
                "name": "Other",
                "count": applications_map["others"]
            }
        ],

        "recruitment_reports": stats
    }
#------------------documents apis---------------------------------------------

'''import os
import uuid
import datetime
from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from google.cloud import storage

from database import get_db
from models import Client


documents_router = APIRouter(prefix="/documents", tags=["Documents"])

GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "client-documents-uploads")

ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg", ".xlsx", ".csv", ".txt"}
MAX_FILE_SIZE_MB = 10


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def validate_file(file: UploadFile):
    ext = os.path.splitext(file.filename)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File '{file.filename}' has unsupported extension '{ext}'. Allowed: {ALLOWED_EXTENSIONS}"
        )


def upload_to_gcs(content: bytes, destination_blob_name: str, content_type: str) -> str:
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_string(content, content_type=content_type)
    return f"gs://{GCS_BUCKET_NAME}/{destination_blob_name}"


def generate_public_url(gcs_path: str) -> str | None:
    """Convert gs://bucket/path to public HTTPS URL."""
    if not gcs_path or not gcs_path.startswith("gs://"):
        return None
    path = gcs_path[5:]
    if "/" not in path:
        return None
    bucket_name, blob_name = path.split("/", 1)
    return f"https://storage.googleapis.com/{bucket_name}/{blob_name}"


def parse_gcs_path(gcs_path: str) -> tuple[str, str]:
    """Return (bucket_name, blob_name) from a gs:// path."""
    if not gcs_path.startswith("gs://"):
        raise ValueError("Invalid GCS path — must start with gs://")
    parts = gcs_path[5:].split("/", 1)
    if len(parts) != 2:
        raise ValueError("Invalid GCS path — missing blob name")
    return parts[0], parts[1]


def generate_signed_url(gcs_path: str, expiration_seconds: int = 3600) -> str:
    """
    Generate a v4 signed URL.
    NOTE: Requires a service-account key JSON (GOOGLE_APPLICATION_CREDENTIALS).
    On Cloud Run with default compute SA this will FAIL — use stream_download() instead.
    """
    import google.auth
    import google.auth.transport.requests
    from google.oauth2 import service_account

    bucket_name, blob_name = parse_gcs_path(gcs_path)

    # Try explicit service account key first (set via env var SA_KEY_PATH or SA_KEY_JSON)
    sa_key_path = os.getenv("SA_KEY_PATH")
    sa_key_json = os.getenv("SA_KEY_JSON")

    if sa_key_json:
        import json
        info = json.loads(sa_key_json)
        credentials = service_account.Credentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
    elif sa_key_path:
        credentials = service_account.Credentials.from_service_account_file(
            sa_key_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
    else:
        raise RuntimeError(
            "Signed URLs require a service-account key. "
            "Set SA_KEY_JSON or SA_KEY_PATH env var, or use the /download endpoint which streams directly."
        )

    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(seconds=expiration_seconds),
        method="GET",
    )


def delete_from_gcs(gcs_path: str):
    bucket_name, blob_name = parse_gcs_path(gcs_path)
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.delete()


def filename_from_path(gcs_path: str) -> str:
    return gcs_path.rstrip("/").split("/")[-1]


# ─────────────────────────────────────────
# UPLOAD
# ─────────────────────────────────────────
@documents_router.post("/clients/{client_id}/upload-documents")
async def upload_documents(
    client_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    admin=Depends(admin_only),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    safe_name = client.client_name.strip().replace(" ", "-").lower()
    folder_name = f"documents/clients/{client.id}-{safe_name}"

    uploaded_paths: list[dict] = []
    failed_files: list[dict] = []

    for file in files:
        try:
            validate_file(file)

            content = await file.read()
            size_mb = len(content) / (1024 * 1024)

            if size_mb > MAX_FILE_SIZE_MB:
                failed_files.append({
                    "filename": file.filename,
                    "error": f"Exceeds {MAX_FILE_SIZE_MB}MB limit (got {size_mb:.2f}MB)",
                })
                continue

            ext = os.path.splitext(file.filename)[-1].lower()
            original_stem = os.path.splitext(file.filename)[0]
            unique_name = f"{original_stem}_{uuid.uuid4().hex}{ext}"
            blob_path = f"{folder_name}/{unique_name}"

            gcs_path = upload_to_gcs(
                content, blob_path, file.content_type or "application/octet-stream"
            )

            uploaded_paths.append({
                "filename": unique_name,          # ← only filename returned
                "original_name": file.filename,
                "path": gcs_path,
                "size_mb": round(size_mb, 2),
            })

        except HTTPException as e:
            failed_files.append({"filename": file.filename, "error": e.detail})
        except Exception as e:
            failed_files.append({"filename": file.filename, "error": str(e)})

    if uploaded_paths:
        existing = (
            [p for p in client.documents.split(",") if p.strip()]
            if client.documents
            else []
        )
        new_paths = [f["path"] for f in uploaded_paths]
        client.documents = ",".join(existing + new_paths)
        db.commit()
        db.refresh(client)

    return {
        "message": "Upload complete",
        "client_id": client_id,
        "uploaded": uploaded_paths,
        "failed": failed_files,
        "total_uploaded": len(uploaded_paths),
        "total_failed": len(failed_files),
    }


# ─────────────────────────────────────────
# GET DOCUMENTS  — filename only
# ─────────────────────────────────────────
@documents_router.get("/clients/{client_id}/documents")
def get_client_documents(
    client_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if not client.documents:
        return {"client_id": client_id, "total": 0, "documents": []}

    paths = [p.strip() for p in client.documents.split(",") if p.strip()]

    documents = []
    for path in paths:
        if not path.startswith("gs://"):
            continue
        documents.append({
            "filename": filename_from_path(path),   # ← ONLY the filename
            "gcs_path": path,                        # kept so frontend can pass it to delete/download
        })

    return {
        "client_id": client_id,
        "total": len(documents),
        "documents": documents,
    }


# ─────────────────────────────────────────
# VIEW DOCUMENT  — streams file inline for browser preview
# ─────────────────────────────────────────
VIEWABLE_INLINE = {
    "pdf":  "application/pdf",
    "png":  "image/png",
    "jpg":  "image/jpeg",
    "jpeg": "image/jpeg",
    "txt":  "text/plain",
}

# These need Google Docs Viewer (can't render natively in browser)
GOOGLE_DOCS_VIEWABLE = {"doc", "docx", "xlsx", "csv"}


@documents_router.get("/clients/{client_id}/view-documents")
def view_client_documents(
    client_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Returns a list of documents with a `view_url` per file:
    - PDF / images / txt  → `/documents/view?gcs_path=...`  (streams inline)
    - doc / docx / xlsx   → Google Docs Viewer URL (opens in browser tab)
    - others              → falls back to the download endpoint
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if not client.documents:
        return {"client_id": client_id, "total": 0, "documents": []}

    paths = [p.strip() for p in client.documents.split(",") if p.strip()]

    documents = []
    for path in paths:
        if not path.startswith("gs://"):
            continue
        fname = filename_from_path(path)
        ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
        encoded_path = path  # frontend encodes when building the URL

        if ext in VIEWABLE_INLINE:
            # Served inline by our /view endpoint
            view_url = f"/documents/view?gcs_path={encoded_path}"
            viewer = "inline"
        elif ext in GOOGLE_DOCS_VIEWABLE:
            # Public URL is needed for Google Docs Viewer
            public_url = generate_public_url(path)
            view_url = f"https://docs.google.com/viewer?url={public_url}&embedded=true"
            viewer = "google_docs"
        else:
            # Unknown type — offer download instead
            view_url = f"/documents/download?gcs_path={encoded_path}"
            viewer = "download"

        documents.append({
            "filename": fname,
            "file_type": ext,
            "gcs_path": path,
            "view_url": view_url,
            "viewer": viewer,      # tells frontend HOW to open it
        })

    return {"client_id": client_id, "total": len(documents), "documents": documents}


@documents_router.get("/view")
def view_file_inline(
    gcs_path: str,
    user=Depends(get_current_user),
):
    if not gcs_path or not gcs_path.startswith("gs://"):
        raise HTTPException(status_code=400, detail="Invalid or missing gcs_path")

    try:
        # ✅ Use correct parser
        bucket_name, blob_name = parse_gcs_path(gcs_path)

        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        if not blob.exists():
            raise HTTPException(status_code=404, detail="File not found in GCS")

        blob.reload()

        fname = filename_from_path(gcs_path)
        ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""

        content_type = VIEWABLE_INLINE.get(
            ext,
            blob.content_type or "application/octet-stream"
        )

        from fastapi.responses import StreamingResponse

        # ✅ DIRECT STREAM (no memory issue)
        return StreamingResponse(
            blob.open("rb"),
            media_type=content_type,
            headers={
                "Content-Disposition": f'inline; filename="{fname}"',
                "Cache-Control": "private, max-age=3600",
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"View failed: {str(e)}")
# ─────────────────────────────────────────
# DOWNLOAD  — streams file directly from GCS
# Works on Cloud Run with NO signed-URL / no SA key needed
# ─────────────────────────────────────────
@documents_router.get("/download")
def download_file(
    gcs_path: str,
    user=Depends(get_current_user),
):
    """
    Streams file from GCS as a download (Cloud Run safe).
    """
    if not gcs_path or not gcs_path.startswith("gs://"):
        raise HTTPException(status_code=400, detail="Invalid or missing gcs_path")

    try:
        # ✅ Correct parsing
        bucket_name, blob_name = parse_gcs_path(gcs_path)

        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        if not blob.exists():
            raise HTTPException(status_code=404, detail="File not found in GCS")

        blob.reload()

        fname = filename_from_path(gcs_path)
        content_type = blob.content_type or "application/octet-stream"

        from fastapi.responses import StreamingResponse

        # ✅ DIRECT STREAM (no memory load)
        return StreamingResponse(
            blob.open("rb"),
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{fname}"',
                "Cache-Control": "no-cache",
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
# ─────────────────────────────────────────
# DELETE DOCUMENT
# ─────────────────────────────────────────
@documents_router.delete("/clients/{client_id}/documents")
def delete_client_document(
    client_id: int,
    gcs_path: str,                                  # query param: ?gcs_path=gs://bucket/path
    db: Session = Depends(get_db),
    admin=Depends(admin_only),
):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    existing = (
        [p.strip() for p in client.documents.split(",") if p.strip()]
        if client.documents
        else []
    )

    if gcs_path not in existing:
        raise HTTPException(status_code=404, detail="Document not found for this client")

    # 1. Delete from GCS
    try:
        delete_from_gcs(gcs_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete from GCS: {e}")

    # 2. Remove from DB
    updated = [p for p in existing if p != gcs_path]
    client.documents = ",".join(updated)
    db.commit()

    return {
        "message": "Document deleted successfully",
        "deleted_filename": filename_from_path(gcs_path),
    }

# ─────────────────────────────────────────
# ALLOWED TYPES FOR PROFILE PICTURE
# ─────────────────────────────────────────
import os
import uuid
import io
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from google.cloud import storage

from database import get_db
from models import Client


ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
MAX_PROFILE_PIC_SIZE_MB = 5
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "client-documents-uploads")


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def delete_from_gcs(gcs_path: str):
    """Delete a blob from GCS silently."""
    try:
        parts = gcs_path[5:].split("/", 1)
        storage_client = storage.Client()
        bucket = storage_client.bucket(parts[0])
        blob = bucket.blob(parts[1])
        blob.delete()
    except Exception as e:
        print(f"GCS delete warning: {e}")


def gcs_blob_from_path(gcs_path: str):
    """Return a GCS Blob object from a gs:// path."""
    bucket_name, blob_name = gcs_path[5:].split("/", 1)
    storage_client = storage.Client()
    return storage_client.bucket(bucket_name).blob(blob_name)


# ─────────────────────────────────────────
# UPLOAD PROFILE PICTURE
# ─────────────────────────────────────────
@documents_router.post("/clients/{client_id}/profile-picture")
async def upload_profile_picture(
    client_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin=Depends(admin_only),
):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    ext = os.path.splitext(file.filename)[-1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{ext}'. Allowed: {ALLOWED_IMAGE_EXTENSIONS}",
        )

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_PROFILE_PIC_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.2f}MB). Max: {MAX_PROFILE_PIC_SIZE_MB}MB",
        )

    # Delete old picture
    if client.profile_picture and client.profile_picture.startswith("gs://"):
        delete_from_gcs(client.profile_picture)

    # Upload new picture
    safe_name = client.client_name.strip().replace(" ", "-").lower()
    unique_name = f"profile_{uuid.uuid4().hex}{ext}"
    blob_path = f"profile-pictures/clients/{client.id}-{safe_name}/{unique_name}"

    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(blob_path)
    blob.upload_from_string(content, content_type=file.content_type or "image/jpeg")

    gcs_path = f"gs://{GCS_BUCKET_NAME}/{blob_path}"
    client.profile_picture = gcs_path
    db.commit()
    db.refresh(client)

    return {
        "message": "Profile picture uploaded successfully",
        "client_id": client_id,
        # ✅ Use this URL directly in <img src="...">
        "profile_picture_url": f"/documents/clients/{client_id}/profile-picture/view",
        "size_mb": round(size_mb, 2),
    }


# ─────────────────────────────────────────
# GET PROFILE PICTURE  (metadata)
# ─────────────────────────────────────────
@documents_router.get("/clients/{client_id}/profile-picture")
def get_profile_picture(
    client_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if not client.profile_picture:
        raise HTTPException(status_code=404, detail="No profile picture found")

    return {
        "client_id": client_id,
        # ✅ Point your <img src> at this URL — it streams the actual image bytes
        "profile_picture_url": f"/documents/clients/{client_id}/profile-picture/view",
        "gcs_path": client.profile_picture,
    }

# ─────────────────────────────────────────
# VIEW / STREAM PROFILE PICTURE
# Use this directly as <img src="BASE_URL/documents/clients/7/profile-picture/view">
# ─────────────────────────────────────────
@documents_router.get("/clients/{client_id}/profile-picture/view")
def view_profile_picture(
    client_id: int,
    db: Session = Depends(get_db),
):
    """
    Streams latest profile image (no caching).
    Always returns fresh image from GCS.
    """

    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if not client.profile_picture:
        raise HTTPException(status_code=404, detail="No profile picture found")

    try:
        blob = gcs_blob_from_path(client.profile_picture)

        if not blob.exists():
            raise HTTPException(status_code=404, detail="Image not found in storage")

        blob.reload()
        content_type = blob.content_type or "image/jpeg"

        buf = io.BytesIO()
        blob.download_to_file(buf)
        buf.seek(0)

        return StreamingResponse(
            buf,
            media_type=content_type,
            headers={
                # 🚫 Disable caching completely
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",

                # ✅ Display in browser
                "Content-Disposition": "inline",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load image: {e}")
# ─────────────────────────────────────────
# DELETE PROFILE PICTURE
# ─────────────────────────────────────────
@documents_router.delete("/clients/{client_id}/profile-picture")
def delete_profile_picture(
    client_id: int,
    db: Session = Depends(get_db),
    admin=Depends(admin_only),
):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if not client.profile_picture:
        raise HTTPException(status_code=404, detail="No profile picture to delete")

    delete_from_gcs(client.profile_picture)
    client.profile_picture = None
    db.commit()

    return {"message": "Profile picture deleted successfully", "client_id": client_id}

#------for employess documents upload APIS-----


#-----------------------add employee document--------
@documents_router.post("/employees/{employee_id}/upload-documents")
async def upload_employee_documents(
    employee_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    admin=Depends(admin_only),
):
    user = db.query(User).filter(User.employee_id == employee_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Employee not found")

    safe_name = f"{user.first_name or ''}-{user.last_name or ''}".strip().replace(" ", "-").lower()
    folder_name = f"documents/employees/{user.employee_id}-{safe_name}"

    uploaded_paths = []
    failed_files = []

    for file in files:
        try:
            validate_file(file)

            content = await file.read()
            size_mb = len(content) / (1024 * 1024)

            if size_mb > MAX_FILE_SIZE_MB:
                failed_files.append({"filename": file.filename, "error": "File too large"})
                continue

            ext = os.path.splitext(file.filename)[-1].lower()
            unique_name = f"{uuid.uuid4().hex}{ext}"
            blob_path = f"{folder_name}/{unique_name}"

            gcs_path = upload_to_gcs(content, blob_path, file.content_type)

            uploaded_paths.append({
                "filename": unique_name,
                "path": gcs_path
            })

        except Exception as e:
            failed_files.append({"filename": file.filename, "error": str(e)})

    if uploaded_paths:
        existing = user.documents.split(",") if user.documents else []
        user.documents = ",".join(existing + [f["path"] for f in uploaded_paths])
        db.commit()

    return {"uploaded": uploaded_paths, "failed": failed_files}
#-------------------get employee document---------------
@documents_router.get("/employees/{employee_id}/documents")
def get_employee_documents(employee_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.employee_id == employee_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Employee not found")

    if not user.documents:
        return {"documents": []}

    paths = [p.strip() for p in user.documents.split(",") if p.strip()]

    return {
        "documents": [{"filename": filename_from_path(p), "gcs_path": p} for p in paths]
    }
#-----------------------------view employee document----------

@documents_router.get("/employees/{employee_id}/view-document")
def view_employee_document(
    employee_id: str,
    gcs_path: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    user_obj = db.query(User).filter(User.employee_id == employee_id).first()

    if not user_obj:
        raise HTTPException(status_code=404, detail="Employee not found")

    if not gcs_path.startswith("gs://"):
        raise HTTPException(status_code=400, detail="Invalid gcs_path")

    try:
        bucket_name, blob_name = parse_gcs_path(gcs_path)

        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        if not blob.exists():
            raise HTTPException(status_code=404, detail="File not found")

        blob.reload()

        fname = filename_from_path(gcs_path)
        ext = fname.split(".")[-1].lower()

        content_type = VIEWABLE_INLINE.get(
            ext,
            blob.content_type or "application/octet-stream"
        )

        from fastapi.responses import StreamingResponse

        return StreamingResponse(
            blob.open("rb"),
            media_type=content_type,
            headers={
                "Content-Disposition": f'inline; filename="{fname}"',
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
#---------------------------------delete employee document-----------
@documents_router.delete("/employees/{employee_id}/documents")
def delete_employee_document(
    employee_id: str,
    gcs_path: str,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.employee_id == employee_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Employee not found")

    existing = user.documents.split(",") if user.documents else []

    if gcs_path not in existing:
        raise HTTPException(status_code=404, detail="Document not found")

    delete_from_gcs(gcs_path)

    user.documents = ",".join([p for p in existing if p != gcs_path])
    db.commit()

    return {"message": "Deleted successfully"}

#--------------download document-----------------------
@documents_router.get("/employees/{employee_id}/download-document")
def download_employee_document(
    employee_id: str,
    gcs_path: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    user_obj = db.query(User).filter(User.employee_id == employee_id).first()

    if not user_obj:
        raise HTTPException(status_code=404, detail="Employee not found")

    if not gcs_path.startswith("gs://"):
        raise HTTPException(status_code=400, detail="Invalid gcs_path")

    try:
        bucket_name, blob_name = parse_gcs_path(gcs_path)

        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        if not blob.exists():
            raise HTTPException(status_code=404, detail="File not found")

        blob.reload()

        fname = filename_from_path(gcs_path)
        content_type = blob.content_type or "application/octet-stream"

        from fastapi.responses import StreamingResponse

        return StreamingResponse(
            blob.open("rb"),
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{fname}"',
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
#---------------upload profile photo for employee--------   
@documents_router.put("/employees/{employee_id}/upload-profile-pic")
async def upload_employee_profile_pic(
    employee_id: str,
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.employee_id == employee_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Employee not found")

    ext = os.path.splitext(photo.filename)[-1].lower()

    if ext not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise HTTPException(status_code=400, detail="Invalid image format")

    content = await photo.read()

    file_name = f"profile_{uuid.uuid4().hex}{ext}"
    blob_path = f"employees/profile/{user.employee_id}/{file_name}"

    gcs_path = upload_to_gcs(content, blob_path, photo.content_type)

    user.profile_pic = gcs_path
    db.commit()

    return {"profile_pic": gcs_path}
#---------------------get employee profile pic-------------

@documents_router.get("/employees/{employee_id}/profile-pic")
def get_employee_profile_pic(
    employee_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    user_obj = db.query(User).filter(User.employee_id == employee_id).first()

    if not user_obj:
        raise HTTPException(status_code=404, detail="Employee not found")

    if not user_obj.profile_pic:
        raise HTTPException(status_code=404, detail="No profile picture found")

    try:
        bucket_name, blob_name = parse_gcs_path(user_obj.profile_pic)

        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        if not blob.exists():
            raise HTTPException(status_code=404, detail="File not found in GCS")

        blob.reload()

        content_type = blob.content_type or "image/jpeg"

        from fastapi.responses import StreamingResponse

        return StreamingResponse(
            blob.open("rb"),
            media_type=content_type,
            headers={
                "Content-Disposition": "inline",
                "Cache-Control": "no-cache",
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#-----------------delete profile pic----------------------

@documents_router.delete("/employees/{employee_id}/profile-pic")
def delete_employee_profile_pic(employee_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.employee_id == employee_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Employee not found")

    if not user.profile_pic:
        raise HTTPException(status_code=404, detail="No profile picture found")

    delete_from_gcs(user.profile_pic)

    deleted_file = filename_from_path(user.profile_pic)

    user.profile_pic = None
    db.commit()

    return {"message": "Deleted", "deleted_file": deleted_file}'''

#-----------------goggle drive documents APIS----------------
import os
import uuid
import io
from typing import List

from fastapi import FastAPI, Depends, File, HTTPException, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from database import get_db
from models import Client

documents_router = APIRouter(prefix="/documents", tags=["Documents"])

# ================================
# GOOGLE DRIVE CONFIG
# ================================
SCOPES = ["https://www.googleapis.com/auth/drive"]
TOKEN_FILE = "token.json"

def get_drive_service():
    if not os.path.exists(TOKEN_FILE):
        raise HTTPException(401, "token.json missing in server")

    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return build("drive", "v3", credentials=creds)
# ================================
# SETTINGS
# ================================
FOLDER_ID = "1EyEiUGtJoqCt3BxTExAlpteWXWs6z0TJ"

ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg", ".xlsx", ".csv", ".txt"}
MAX_FILE_SIZE_MB = 10

ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
MAX_PROFILE_PIC_SIZE_MB = 5   # ✅ ADD THIS

# ================================
# HELPERS
# ================================
def validate_file(file: UploadFile):
    ext = os.path.splitext(file.filename)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Unsupported file type")
        
def upload_to_drive(file: UploadFile, filename: str):
    service = get_drive_service()

    file.file.seek(0)
    stream = io.BytesIO(file.file.read())

    metadata = {"name": filename, "parents": [FOLDER_ID]}
    media = MediaIoBaseUpload(stream, mimetype=file.content_type, resumable=True)

    uploaded = service.files().create(
        body=metadata,
        media_body=media,
        fields="id"
    ).execute()

    return uploaded.get("id")


def make_public(file_id: str):
    service = get_drive_service()

    service.permissions().create(
        fileId=file_id,
        body={"type": "anyone", "role": "reader"}
    ).execute()

    return f"https://drive.google.com/uc?id={file_id}"


def delete_from_drive(file_id: str):
    service = get_drive_service()
    service.files().delete(fileId=file_id).execute()


# ================================
# UPLOAD DOCUMENTS
# ================================

@documents_router.post("/clients/{client_id}/upload-documents")
async def upload_documents(
    client_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):

    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(404, "Client not found")

    uploaded = []

    for file in files:

        # ✔ read once safely
        content = await file.read()
        size_mb = len(content) / (1024 * 1024)

        if size_mb > MAX_FILE_SIZE_MB:
            raise HTTPException(400, f"{file.filename} too large")

        original_name = file.filename
        ext = os.path.splitext(original_name)[1]
        stored_name = f"{uuid.uuid4().hex}{ext}"

        # reset stream
        file.file.seek(0)

        # upload
        file_id = upload_to_drive(file, stored_name)

        # make public (IMPORTANT)
        try:
            make_public(file_id)
        except Exception as e:
            print("Permission error:", e)

        uploaded.append({
            "file_id": file_id,
            "original_name": original_name,
            "stored_name": stored_name,
            "view_url": f"https://drive.google.com/file/d/{file_id}/view",
            "download_url": f"https://drive.google.com/uc?export=download&id={file_id}"
        })

    
    import json

    try:
        existing_list = json.loads(client.documents) if client.documents else []
    except:
        existing_list = []

    existing_list.extend(uploaded)
    client.documents = json.dumps(existing_list)

    db.commit()

    return {"uploaded": uploaded}
# ================================
# GET DOCUMENTS
# ================================

@documents_router.get("/clients/{client_id}/documents")
def get_documents(client_id: int, db: Session = Depends(get_db)):

    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(404, "Client not found")

    if not client.documents:
        return {"documents": []}

    import json

    try:
        documents = json.loads(client.documents)
    except:
        documents = []

    return {
        "documents": [
            {
                "file_id": d["file_id"],
                "original_name": d.get("original_name"),
                "stored_name": d.get("stored_name"),
                "url": d.get("url")
            }
            for d in documents
        ]
    }

@documents_router.get("/files/view")
def view_file(file_id: str):

    if not file_id:
        raise HTTPException(400, "file_id required")

    view_url = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"

    return {
        "file_id": file_id,
        "view_url": view_url
    }
    
@documents_router.get("/files/download")
def download_file(file_id: str):

    if not file_id:
        raise HTTPException(400, "file_id required")

    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"

    return {
        "file_id": file_id,
        "download_url": download_url
    }

@documents_router.delete("/clients/{client_id}/documents")
def delete_document(
    client_id: int,
    file_id: str,
    db: Session = Depends(get_db)
):

    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(404, "Client not found")

    import json

    # ✔ parse JSON safely
    try:
        documents = json.loads(client.documents or "[]")
    except:
        documents = []

    updated_docs = []
    found = False

    for doc in documents:
        if doc.get("file_id") == file_id:
            found = True
            try:
                delete_from_drive(file_id)
            except Exception as e:
                print("Drive delete error:", e)
        else:
            updated_docs.append(doc)

    if not found:
        raise HTTPException(404, "File not found")

    # ✔ save back to DB
    client.documents = json.dumps(updated_docs)
    db.commit()

    return {"message": "Deleted successfully"}


# ================================
# PROFILE PIC
# ================================
@documents_router.post("/clients/{client_id}/profile-picture")
async def upload_profile(
    client_id: int,
    file: UploadFile,
    db: Session = Depends(get_db)
):

    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(404, "Client not found")

    ext = os.path.splitext(file.filename)[-1].lower()

    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(400, "Invalid image type")

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)

    if size_mb > MAX_PROFILE_PIC_SIZE_MB:
        raise HTTPException(400, "Image too large")

    file.file.seek(0)

    original_name = file.filename
    stored_name = f"profile_{uuid.uuid4().hex}_{original_name}"

    file_id = upload_to_drive(file, stored_name)
    url = make_public(file_id)

    # remove old profile if exists
    if client.profile_picture:
        try:
            delete_from_drive(client.profile_picture)
        except:
            pass

    client.profile_picture = file_id
    db.commit()

    return {
        "file_id": file_id,
        "original_name": original_name,
        "url": url
    }

@documents_router.get("/clients/{client_id}/profile-picture")
def get_profile(client_id: int, db: Session = Depends(get_db)):

    client = db.query(Client).filter(Client.id == client_id).first()

    if not client or not client.profile_picture:
        raise HTTPException(404, "Profile picture not found")

    return {
        "file_id": client.profile_picture,
        "url": f"https://drive.google.com/uc?id={client.profile_picture}"
    }

from fastapi.responses import StreamingResponse
import requests
from io import BytesIO

@documents_router.get("/clients/{client_id}/profile-picture-view")
def get_profile_picture(client_id: int, db: Session = Depends(get_db)):

    client = db.query(Client).filter(Client.id == client_id).first()

    if not client or not client.profile_picture:
        raise HTTPException(404, "Profile picture not found")

    url = f"https://drive.google.com/uc?id={client.profile_picture}"

    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(404, "Image not accessible")

    return StreamingResponse(
        BytesIO(response.content),
        media_type="image/jpeg"
    )
@documents_router.delete("/clients/{client_id}/profile-picture")
def delete_profile_picture(client_id: int, db: Session = Depends(get_db)):

    client = db.query(Client).filter(Client.id == client_id).first()

    if not client or not client.profile_picture:
        raise HTTPException(404, "Profile picture not found")

    delete_from_drive(client.profile_picture)

    client.profile_picture = None
    db.commit()

    return {"message": "Deleted"}

#--------------Employee documents APIS--------------------------
@documents_router.post("/employees/{employee_id}/upload-documents")
async def upload_documents(
    employee_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(User.employee_id == employee_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    uploaded = []

    for file in files:
        content = await file.read()
        size_mb = len(content) / (1024 * 1024)

        if size_mb > MAX_FILE_SIZE_MB:
            raise HTTPException(400, "File too large")

        original_name = file.filename
        ext = os.path.splitext(original_name)[1]
        stored_name = f"{uuid.uuid4().hex}{ext}"

        file.file.seek(0)

        file_id = upload_to_drive(file, stored_name)

        # IMPORTANT: make file public
        try:
            make_public(file_id)
        except Exception as e:
            print("Permission error:", e)

        uploaded.append({
            "file_id": file_id,
            "original_name": original_name,
            "stored_name": stored_name,
            "view_url": f"https://drive.google.com/file/d/{file_id}/view",
            "download_url": f"https://drive.google.com/uc?export=download&id={file_id}"
        })

    # ================================
    # SAFE JSON HANDLING (FIX FOR YOUR ERROR)
    # ================================
    import json

    try:
        existing = json.loads(user.documents) if user.documents else []
        if not isinstance(existing, list):
            existing = []
    except Exception:
        existing = []

    existing.extend(uploaded)
    user.documents = json.dumps(existing)

    db.commit()

    return {
        "message": "Uploaded successfully",
        "uploaded": uploaded
    }

@documents_router.get("/employees/{employee_id}/documents")
def get_documents(employee_id: str, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.employee_id == employee_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    import json
    try:
        docs = json.loads(user.documents or "[]")
    except:
        docs = []

    return {"documents": docs}

'''@documents_router.get("/documents/view")
def view_document(file_id: str):
    return RedirectResponse(
        f"https://drive.google.com/file/d/{file_id}/view"
    )

@documents_router.get("/documents/download")
def download_document(file_id: str):
    return RedirectResponse(
        f"https://drive.google.com/uc?export=download&id={file_id}"
    )'''

@documents_router.delete("/employees/{employee_id}/documents")
def delete_document(employee_id: str, file_id: str, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.employee_id == employee_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    import json
    docs = json.loads(user.documents or "[]")

    new_docs = [d for d in docs if d["file_id"] != file_id]

    if len(docs) == len(new_docs):
        raise HTTPException(404, "File not found")

    try:
        delete_from_drive(file_id)
    except:
        pass

    user.documents = json.dumps(new_docs)
    db.commit()

    return {"message": "Deleted successfully"}

@documents_router.post("/employees/{employee_id}/profile-picture")
async def upload_profile(employee_id: str, file: UploadFile, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.employee_id == employee_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)

    if size_mb > MAX_PROFILE_PIC_SIZE_MB:
        raise HTTPException(400, "Too large")

    file.file.seek(0)

    stored_name = f"profile_{uuid.uuid4().hex}{os.path.splitext(file.filename)[1]}"

    file_id = upload_to_drive(file, stored_name)

    make_public(file_id)

    user.profile_pic = file_id   # ✅ FIXED FIELD
    db.commit()

    return {
        "file_id": file_id,
        "url": f"https://drive.google.com/uc?export=view&id={file_id}"
    }

@documents_router.get("/employees/{employee_id}/profile-picture")
def get_profile(employee_id: str, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.employee_id == employee_id).first()

    if not user or not user.profile_pic:
        raise HTTPException(404, "Not found")

    return {
        "file_id": user.profile_pic,
        "url": f"https://drive.google.com/uc?export=view&id={user.profile_pic}"
    }

@documents_router.get("/employees/{employee_id}/profile-picture-view")
def get_profile_picture(employee_id:str, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.employee_id == employee_id).first()
    if not user or not user.profile_pic:
        raise HTTPException(404, "Profile picture not found")

    url = f"https://drive.google.com/uc?export=view&id={user.profile_pic}"

    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(404, "Image not accessible")

    return StreamingResponse(
        BytesIO(response.content),
        media_type="image/jpeg"
    )

@documents_router.delete("/employees/{employee_id}/profile-picture")
def delete_profile(employee_id: str, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.employee_id == employee_id).first()

    if not user or not user.profile_pic:
        raise HTTPException(404, "Not found")

    try:
        delete_from_drive(user.profile_pic)
    except Exception as e:
        print("Drive delete error:", e)

    user.profile_pic = None   # ✅ FIXED FIELD
    db.commit()

    return {"message": "Deleted"}
# ------------------ CREATE APP ------------------
app.include_router(auth_router)
app.include_router(router, prefix="/clients", tags=["Clients"])
app.include_router(application_router)
app.include_router(Credential_router)
app.include_router(reports_router)
app.include_router(auth_router)
app.include_router(timesheet_router)
app.include_router(calendar_router)
app.include_router(documents_router)
# ------------------ CREATE TABLES ------------------
Base.metadata.create_all(bind=engine)


# ------------------ CREATE USER ------------------
import re

def generate_employee_id(db: Session):

    last_user = db.query(User).filter(
        User.employee_id.like("MSS%")
    ).order_by(User.employee_id.desc()).first()

    if not last_user:
        return "MSS001"

    # Extract only digits
    numbers = re.findall(r'\d+', last_user.employee_id)

    if not numbers:
        return "MSS001"

    last_number = int(numbers[0])
    new_number = last_number + 1

    return f"MSS{new_number:03d}"
    



#--------------create user-------------------
from datetime import datetime, date
@app.post("/admin/users", response_model=UserResponse)
def create_user(
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form("user"),
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    mobile: Optional[str] = Form(None),
    designation: Optional[str] = Form(None),

    reporting_to: Optional[str] = Form(None),  
    HR: Optional[str] = Form(None),            

    aadhaar_number: Optional[str] = Form(None),
    start_date: Optional[date] = Form(None),
    end_date: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    

    db: Session = Depends(get_db),
    admin=Depends(admin_only)
):
    # ✅ Email check
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # ✅ Generate employee ID
    employee_id = generate_employee_id(db)

    # ✅ Helper function to extract ID
    def extract_emp_id(value: Optional[str]):
        if value and " - " in value:
            return value.split(" - ")[0].strip()
        return value.strip() if value else None

    # ✅ Clean values
    reporting_to_id = extract_emp_id(reporting_to)
    hr_id = extract_emp_id(HR)

    # ✅ Validate reporting manager
    if reporting_to_id:
        manager = db.query(User).filter(User.employee_id == reporting_to_id).first()
        if not manager:
            raise HTTPException(status_code=400, detail="Reporting manager not found")

    # ✅ Validate HR
    if hr_id:
        hr = db.query(User).filter(User.employee_id == hr_id).first()
        if not hr:
            raise HTTPException(status_code=400, detail="HR not found")

    # ✅ Aadhaar validation
    if aadhaar_number:
        if not aadhaar_number.isdigit() or len(aadhaar_number) != 12:
            raise HTTPException(
                status_code=400,
                detail="Aadhaar must be exactly 12 digits"
            )

    # ✅ End date handling
    parsed_end_date = None
    is_active = True

    if end_date:
        if end_date.lower() == "currently working":
            parsed_end_date = None
            is_active = True
        else:
            try:
                parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                is_active = False
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="end_date must be YYYY-MM-DD or 'currently working'"
                )

    if start_date and parsed_end_date and parsed_end_date < start_date:
        raise HTTPException(
            status_code=400,
            detail="End date cannot be before start date"
        )

    # ✅ Hash password
    hashed_password = hash_password(password)

    # ✅ Create user
    new_user = User(
        employee_id=employee_id,
        email=email,
        password_hash=hashed_password,
        role=role,
        first_name=first_name,
        last_name=last_name,
        mobile=mobile,
        designation=designation,

        reporting_to=reporting_to_id, 
        HR=hr_id,                      

        aadhaar_number=aadhaar_number,
        start_date=start_date,
        end_date=parsed_end_date,
        location=location,
        notes=notes,
    
        is_active=is_active
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # ✅ Optional: return names also
    return {
        **new_user.__dict__,
        "reporting_to_name": f"{manager.first_name} {manager.last_name}" if reporting_to_id else None,
        "hr_name": f"{hr.first_name} {hr.last_name}" if hr_id else None
    }
#-----------------update user--------------------------------------------------
@app.put("/admin/users/{employee_id}", response_model=UserResponse)
def update_user(
    employee_id: str,   
    email: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    role: Optional[str] = Form(None),
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    mobile: Optional[str] = Form(None),
    designation: Optional[str] = Form(None),

    reporting_to: Optional[str] = Form(None),  
    HR: Optional[str] = Form(None),

    aadhaar_number: Optional[str] = Form(None),
    start_date: Optional[date] = Form(None),
    end_date: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),

    db: Session = Depends(get_db),
    admin=Depends(admin_only)
):
    try:
        
        user = db.query(User).filter(User.employee_id == employee_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        
        def extract_emp_id(value: Optional[str]):
            if value and " - " in value:
                return value.split(" - ")[0].strip()
            return value.strip() if value else None

        reporting_to_id = extract_emp_id(reporting_to)
        hr_id = extract_emp_id(HR)

        # ✅ Validate reporting manager
        manager = None
        if reporting_to_id:
            manager = db.query(User).filter(User.employee_id == reporting_to_id).first()
            if not manager:
                raise HTTPException(status_code=400, detail="Reporting manager not found")

        # ✅ Validate HR
        hr = None
        if hr_id:
            hr = db.query(User).filter(User.employee_id == hr_id).first()
            if not hr:
                raise HTTPException(status_code=400, detail="HR not found")

        # ✅ Aadhaar validation
        if aadhaar_number:
            if not aadhaar_number.isdigit() or len(aadhaar_number) != 12:
                raise HTTPException(
                    status_code=400,
                    detail="Aadhaar must be exactly 12 digits"
                )

        # ✅ End date handling
        parsed_end_date = user.end_date
        is_active = user.is_active

        if end_date is not None:
            if end_date.lower() == "currently working":
                parsed_end_date = None
                is_active = True
            else:
                try:
                    parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                    is_active = False
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail="end_date must be YYYY-MM-DD or 'currently working'"
                    )

        if start_date and parsed_end_date and parsed_end_date < start_date:
            raise HTTPException(
                status_code=400,
                detail="End date cannot be before start date"
            )

        # ✅ Update fields
        if email is not None:
            user.email = email
        if password is not None:
            user.password_hash = hash_password(password)
        if role is not None:
            user.role = role
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if mobile is not None:
            user.mobile = mobile
        if designation is not None:
            user.designation = designation
        if reporting_to is not None:
            user.reporting_to = reporting_to_id
        if HR is not None:
            user.HR = hr_id
        if aadhaar_number is not None:
            user.aadhaar_number = aadhaar_number
        if start_date is not None:
            user.start_date = start_date
        if end_date is not None:
            user.end_date = parsed_end_date
            user.is_active = is_active
        if location is not None:
            user.location = location
        if notes is not None:
            user.notes = notes

        db.commit()
        db.refresh(user)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    # ✅ Always fetch names from DB (better than using request values)
    reporting_to_name = None
    if user.reporting_to:
        mgr = db.query(User).filter(User.employee_id == user.reporting_to).first()
        if mgr:
            reporting_to_name = f"{mgr.first_name} {mgr.last_name}"

    hr_name = None
    if user.HR:
        hr_user = db.query(User).filter(User.employee_id == user.HR).first()
        if hr_user:
            hr_name = f"{hr_user.first_name} {hr_user.last_name}"

    return {
        **user.__dict__,
        "reporting_to_name": reporting_to_name,
        "hr_name": hr_name
    }


# ------------------ GET USERS ------------------
@app.get("/admin/users", response_model=list[UserResponse])
def get_users(
    db: Session = Depends(get_db),
    admin=Depends(admin_only)
):
    return db.query(User).all()


#------------------get by employee id---------------------

@app.get("/admin/users/{employee_id}", response_model=UserResponse)
def get_user_by_employee_id(
    employee_id: str,
    db: Session = Depends(get_db),
):
    # ✅ Fetch user
    user = db.query(User).filter(
        User.employee_id == employee_id
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # ✅ Get reporting manager name
    reporting_to_name = None
    if user.reporting_to:
        manager = db.query(User).filter(
            User.employee_id == user.reporting_to
        ).first()
        if manager:
            reporting_to_name = f"{manager.first_name} {manager.last_name}"

    # ✅ Get HR name
    hr_name = None
    if user.HR:
        hr = db.query(User).filter(
            User.employee_id == user.HR
        ).first()
        if hr:
            hr_name = f"{hr.first_name} {hr.last_name}"

    # ✅ Return full response
    return {
        **user.__dict__,
        "reporting_to_name": reporting_to_name,
        "hr_name": hr_name
        
    }
# ------------------ DELETE USER ------------------

@app.delete("/admin/users/{employee_id}")
def delete_user(
    employee_id: str,
    db: Session = Depends(get_db),
    admin=Depends(admin_only)
):
    try:

        user = db.query(User).filter(
            User.employee_id == employee_id
        ).first()

        if not user:
            return {
                "success": False,
                "message": "User not found"
            }

        '''if user.role and user.role.lower() in ["admin", "super admin"]:
            return {
                "success": False,
                "message": "Admin users cannot be deleted"
            }'''

        logged_in_role = admin.get("role", "").lower()
        target_role = user.role.lower() if user.role else ""
        if target_role == "super admin":
            return {
                "success": False,
                "message": "Super Admin cannot be deleted"
            }
        if (
            logged_in_role == "admin"
            and target_role == "admin"

        ):

            return {
                "success": False,
                "message": "Admin cannot delete another admin"
            }

        # ✅ Remove reporting references
        db.query(User).filter(
            User.reporting_to == employee_id
        ).update({
            "reporting_to": None
        })

        # ✅ Remove HR references
        db.query(User).filter(
            User.HR == employee_id
        ).update({
            "HR": None
        })

        # ✅ Remove client mapping
        db.query(Client).filter(
            Client.employee_id == employee_id
        ).update({
            "employee_id": None
        })

        # ✅ Delete user's timesheets
        db.query(Timesheet).filter(
            Timesheet.user_id == user.id
        ).delete()

        # ✅ Delete user's draft timesheets
        db.query(DraftTimesheet).filter(
            DraftTimesheet.user_id == user.id
        ).delete()

        # ✅ Delete user's leave records
        db.query(Leave).filter(
            Leave.user_id == user.id
        ).delete()

        # ✅ Delete user's reports
        db.query(Reports).filter(
            Reports.user_id == user.id
        ).delete()

        # ✅ Finally delete user
        db.delete(user)

        db.commit()

        return {
            "success": True,
            "message": "User deleted successfully"
        }

    except Exception as e:

        db.rollback()

        return {
            "success": False,
            "message": f"Something went wrong: {str(e)}"
        }

#-----------get users table-----------------

from sqlalchemy.orm import aliased
from sqlalchemy import or_



from sqlalchemy.orm import aliased

@app.get("/admin/users-table")
def get_all_users(
    db: Session = Depends(get_db),
    admin=Depends(admin_only)
):

    # 🔹 Alias for manager table
    Manager = aliased(User)

    # 🔹 Base query
    query = db.query(
        User,
        Manager.first_name.label("manager_first_name"),
        Manager.last_name.label("manager_last_name")

    ).outerjoin(

        Manager,
        User.reporting_to == Manager.employee_id

    )

    # 🔹 SUPER ADMIN
    # Show everyone except own account
    if admin["role"] == "super admin":

        query = query.filter(
            User.email != admin["email"]
        )

    # 🔹 ADMIN
    # Show everyone except own account
    elif admin["role"] == "admin":

        query = query.filter(
            User.id != admin["id"]
        )

    # 🔹 NORMAL USER
    else:

        query = query.filter(
            User.reporting_to == admin["employee_id"],
            User.id != admin["id"]
        )

    users = query.order_by(
        User.updated_at.desc(),
        User.created_at.desc()
    ).all()

    result = []

    for user, manager_first_name, manager_last_name in users:

        # 🔹 Reporting manager name
        reporting_name = None

        if manager_first_name or manager_last_name:

            reporting_name = (
                f"{manager_first_name or ''} "
                f"{manager_last_name or ''}"
            ).strip()

        # 🔹 Employees reporting to current user
        reporting_users = db.query(User).filter(
            User.reporting_to == user.employee_id
        ).all()

        reporting_employees = [

            {
                "employee_id": emp.employee_id,
                "name": (
                    f"{emp.first_name or ''} "
                    f"{emp.last_name or ''}"
                ).strip(),
                "role": emp.role
            }

            for emp in reporting_users
        ]

        result.append({

            "employee_id": user.employee_id,

            "name": (
                f"{user.first_name or ''} "
                f"{user.last_name or ''}"
            ).strip(),

            "mobile": user.mobile,
            "email": user.email,
            "role": user.role,

            # 🔹 Reporting manager employee ID
            "reporting_to_employee_id": user.reporting_to,

            # 🔹 Reporting manager name
            "reporting_to": reporting_name,

            # 🔹 Employees under this employee
            "reporting_employees": reporting_employees,

            "created_at": user.created_at,
            "updated_at": user.updated_at
        })

    return result


    
from sqlalchemy import func

@app.get("/employee-ids", response_model=list[str])
def get_employee_ids(db: Session = Depends(get_db)):

    employees = (
        db.query(
            User.employee_id,
            User.first_name,
            User.last_name
        )
        .distinct()
        .order_by(User.employee_id.asc())
        .all()
    )

    return [
        f"{emp.employee_id} - {emp.first_name} {emp.last_name}"
        for emp in employees
        if emp.employee_id
    ]

import requests
from fastapi import Query

@app.get("/technologies")
def get_technologies(search: str = Query(None)):

    if not search:
        return []

    url = f"https://api.stackexchange.com/2.3/tags?inname={search}&site=stackoverflow&pagesize=50"

    response = requests.get(url)

    data = response.json()

    technologies = [
        item["name"]
        for item in data.get("items", [])
    ]

    return technologies
