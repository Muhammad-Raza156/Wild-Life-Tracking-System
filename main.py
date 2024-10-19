import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from datetime import date, time
from pydantic import BaseModel

app=FastAPI()


#in memory database 
sighting_list=[]

class Item(BaseModel):
    species: str
    location: str
    date: date
    time: time


@app.get("/")
async def read_root():
    return {"message1":"Welcome to the wild life tracking system",
            "message2":"Add a new sighting",
            "message3":"View all sightings",
            "message4":"Search sightings by species"}

# Create an item
@app.post("/sightings/", response_model=Item)
async def create_sighting(item: Item):
    sighting_list.append(item)
    return item
    
@app.get("/view-sightings")
async def view_sightings():
    if sighting_list:
        return sighting_list
    else:
        return {"message": "No sighting record found in database"}

@app.get("/search-by-specie")
async def search_by_species(species: str):
    result = [sighting for sighting in sighting_list if sighting.species == species]
    if result:
        return result
    else:
        raise HTTPException(404, f"no recorded sighting for {species}")
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001, reload=True)