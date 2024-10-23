import logging
import os
from fastapi import Response, FastAPI, HTTPException, status, Query,BackgroundTasks
from datetime import date, time
from pydantic import BaseModel, EmailStr
from database import database, Sighting
from typing import List, Optional
from fastapi_pagination import add_pagination, Page
from fastapi_pagination.ext.databases import paginate as database_paginate
from fastapi_mail import FastMail, MessageSchema,ConnectionConfig
from dotenv import load_dotenv


load_dotenv()

app=FastAPI()
add_pagination(app)

# Configure logging
logging.basicConfig(level=logging.DEBUG, filename='app.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


#in memory database 
sighting_list=[]

class Item(BaseModel):
    species: str
    location: str
    date: date
    time: time

class EmailSchema(BaseModel):
   email: List[EmailStr]


conf= ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT")),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS= True,
    MAIL_SSL_TLS= False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS = True
)


async def send_mail(subject: str, body: str,email: EmailSchema):
 
    recipients1=email.dict().get("email")
    message = MessageSchema(
        subject=subject,
        recipients=recipients1,  # List of recipients, as many as you can pass 
        body=body,
        subtype="html"
        )
 
    fm = FastMail(conf)
    await fm.send_message(message)
    logger.info(f"Email sent to {recipients1}")
 
    return {"message": "email has been sent"}

@app.on_event("startup")
async def startup():
    logger.info("Connecting to the database.")
    try:
        await database.connect()
        logger.info("Successfully connected to database.")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")


@app.on_event("shutdown")
async def shutdown():
    logger.info("Disconnecting from the database.")
    try:
        await database.disconnect()
        logger.info("Successfully disconnected from the database.")
    except Exception as e:
        logger.error(f"Failed to disconnect from database: {e}")

@app.get("/")
async def read_root():
    return {"message1":"Welcome to the wild life tracking system",
            "message2":"Add a new sighting",
            "message3":"View all sightings",
            "message4":"Search sightings by species"}

# Create a new sighting and store it in the database
@app.post("/sightings/", response_model=Item, status_code=status.HTTP_201_CREATED)
async def create_sighting(item: Item,email:EmailSchema, background_tasks: BackgroundTasks):
    logger.info(f"Attempting to create sighting: {item.species} at {item.location}")
    query = Sighting.__table__.insert().values(
        species=item.species.title(),
        location=item.location,
        date=item.date,
        time=item.time
    )

    try:
        await database.execute(query)
        logger.info(f"Sighting for {item.species} added successfully")
        email_subject="Sighting recorded"
        email_body=f"Sighting for {item.species} at loaction {item.location} on date {item.date} and time {item.time} added successfully"
        recipient_email= email
        background_tasks.add_task(send_mail, email_subject, email_body, recipient_email)
        return item
    except Exception as e:
        logger.error(f"Error adding sighting: {e}")
        raise HTTPException(status_code=500, detail="Failed to add sighting.")
    
@app.get("/view-sightings", response_model=Page[Item])

async def view_sightings():
    """
    View sightings with pagination support directly from the database.
    """
    logger.info("Fetching paginated sightings record from database ")
    query = Sighting.__table__.select()
    
    try:
        paginated_results= await database_paginate(database, query)
        logger.info("Successfully fetched sightings.")
        return paginated_results
    except Exception as e:
        logger.error(f"Error fetching sightings: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch sighting.")

# Search sightings by species
@app.get("/search-by-species")
async def search_by_species(species: Optional[str] = None, location: Optional[str] = None, date: Optional[date] = None, time: Optional[time] = None):
    if species:
        query = Sighting.__table__.select().where(Sighting.species == species.title())

    if location:
        query = Sighting.__table__.select().where(Sighting.location == location)

    if date:
        query = Sighting.__table__.select().where(Sighting.date == date)

    if time:
        query = Sighting.__table__.select().where(Sighting.time == time)
    try:
        results= await database.fetch_all(query)
        if not results:
            raise HTTPException(404, f"No recorded sighting")
        return [dict(result) for result in results]
    except Exception as e:
        logger.error(f"Error fetching sightings: {e}")
        raise HTTPException(status_code=500, detail="Failed to search sighting.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001, reload=True)