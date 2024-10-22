import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, status, Query
from datetime import date, time
from pydantic import BaseModel
from database import database, Sighting

from typing import List, Optional
app=FastAPI()


#in memory database 
sighting_list=[]

class Item(BaseModel):
    species: str
    location: str
    date: date
    time: time


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/")
async def read_root():
    return {"message1":"Welcome to the wild life tracking system",
            "message2":"Add a new sighting",
            "message3":"View all sightings",
            "message4":"Search sightings by species"}

# Create a new sighting and store it in the database
@app.post("/sightings/", response_model=Item, status_code=status.HTTP_201_CREATED)
async def create_sighting(item: Item):
    query = Sighting.__table__.insert().values(
        species=item.species.title(),
        location=item.location,
        date=item.date,
        time=item.time
    )
    await database.execute(query)
    return item
    
@app.get("/view-sightings", response_model=List[Item])

async def view_sightings(limit: int = Query(2, description="Limit the number of sightings to return"), 
                         offset: int = Query(0, description="Skip a number of records before returning results")):
    """
    Paginate through the sightings.
    limit: number of records to return
    offset: number of records to skip
    """
    query = Sighting.__table__.select().limit(limit).offset(offset)
    results = await database.fetch_all(query)
    
    if results:
        return [dict(result) for result in results]
    else:
        return {"message": "No sighting record found in the database"}

# Search sightings by species
@app.get("/search-by-species")
async def search_by_species(species: str):
    query = Sighting.__table__.select().where(Sighting.species == species.title())
    results = await database.fetch_all(query)
    if results:
        return [dict(result) for result in results]
    else:
        raise HTTPException(404, f"No recorded sighting for {species}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001, reload=True)