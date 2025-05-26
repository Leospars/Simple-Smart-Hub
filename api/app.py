import os
from contextlib import asynccontextmanager
from datetime import timedelta, datetime
from typing import Annotated
from bson import ObjectId 

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from markdown import markdown
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, BeforeValidator, Field
import requests
import re

from os import path
dir_path = path.dirname(path.abspath(__file__)) 

# Database
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017") # Default to local MongoDB
connection = AsyncIOMotorClient(MONGO_URI)
db = connection.get_database("simple-smart-hub")

# Tests
@asynccontextmanager
async def lifespan(app: FastAPI):
    # on startup
    await update_settings(Settings(user_temp=30, user_light="sunset", light_duration="4h"))
    yield
    # on shutdown
    print("Shutting down...")

# Allow CORS (Cross Origin Resource Sharing)
app = FastAPI(lifespan=lifespan)
origins = [ "https://simple-smart-hub-client.netlify.app" ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Functions
PyObjectId = Annotated[str, BeforeValidator(str)]
regex = re.compile(r'((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?')

def parse_time(time_str):
    parts = regex.match(time_str)
    if not parts:
        return
    parts = parts.groupdict()
    time_params = {}
    for name, param in parts.items():
        if param:
            time_params[name] = int(param)
    return timedelta(**time_params)

def get_sunset_time() -> str:
    # Placeholder function to simulate getting sunset time
    res = requests.get("https://api.ipify.org/?format=json")
    if(ip := res.json()["ip"]):
        res = requests.get(f"http://ip-api.com/json/{ip}")
        if(not ("lat" in res.json().keys())):
            raise HTTPException(status_code=500, detail="Failed to get location")
        lat, lon = res.json()["lat"], res.json()["lon"]
        print(f"Country: {res.json()['country']}, Lat: {lat}, Lon: {lon}")
        res = requests.get(f"https://api.sunrisesunset.io/json?lat={lat}&lng={lon}")
        
        if(res.status_code != 200):
            raise HTTPException(status_code=500, detail="Failed to get sunset time")
        sunset = res.json()["results"]["sunset"]
        try: 
            sunset_time = datetime.strptime(sunset, "%I:%M:%S %p")
        except Exception as e:
            raise HTTPException(status_code=500, detail="Sunset time format may have changed from 03:45:00 PM")
        print(f"Sunset time today - {datetime.now().date()}: {sunset_time.time()}")
        return sunset_time.strftime("%H:%M:%S")
    else: 
        raise HTTPException(status_code=500, detail="Failed to get IP")

# Routes
@app.get("/")
def root():
    file_content = open(path.join(dir_path, "..", "README.md"), "r").read()
    return HTMLResponse(markdown(file_content))

@app.get("/db-test")
async def db_test():
    name = db.name
    try:
        row = await db["settings"].find_one()        
    except Exception as e:
        print(f"Error with database: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")
    return {"mwah": f"{name}", "row": Settings(**row)}

# Routes for settings
class Settings(BaseModel):
    user_temp: int
    user_light: str = Field(default_factory=get_sunset_time)
    light_duration: str | None = Field(default=None)
    light_time_off: str | None = Field(default=None)

@app.get("/settings")
async def get_settings(_id: str | None):
    _id = None if not _id else _id # Accepts empty string '' as None
    if _id is None:
        pref = await db["settings"].find_one() # return first id for testing purposes
    else :
        try:
            _id = ObjectId(_id)
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid ID format")
        pref = await db["settings"].find_one({"_id": _id})
    if not pref:
        raise HTTPException(status_code=404, detail="Settings not found")
    
    pref['_id'] = str(pref['_id']) # Convert ObjectId to string
    return pref
        
@app.put("/settings")
async def update_settings(preferences: Settings):
    preferences_dict = {"id": None} # For future purposes get user id from user login
    preferences_dict.update(preferences.model_dump())
    user_light = get_sunset_time() if preferences_dict["user_light"] == "sunset" \
        else preferences_dict["user_light"]
    start_time = datetime.strptime(user_light, "%H:%M:%S")
    preferences_dict["user_light"] = str(start_time.time())
    print("preferences_dict: ", preferences_dict)
    
    duration = parse_time(preferences_dict["light_duration"])
    preferences_dict["light_time_off"] = str((start_time + duration).time())
    preferences_dict.pop("light_duration") # remove light_duration from the dict
    
    # update user settings
    try:
        await db["settings"].update_one({"id": preferences_dict["id"]}, {"$set": preferences_dict}, upsert=True)
        preferences_dict = await get_settings(preferences_dict["id"]) # return with auto generated id parameter
    except Exception as e:
        print(f"Error with database: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update and retrieve from the databse\n\n Error: {e}")
    
    preferences_dict.pop('id') # remove null id from the dict
    print(f"preferences: {(preferences_dict)}")
    return preferences_dict

# Routes for State
class State(BaseModel):
    id: PyObjectId | None = Field(default=None, alias="_id")
    temperature: float
    presence: bool
    datetime: str #"2023-02-23T18:22:28"

class StateCollection(BaseModel):
    states: list[State]    

@app.post("/state") # Carried out by the esp32 module
async def create_state(state_req: State):
    state_dict = state_req.model_dump()
    print(state_dict)
    if (not state_dict['id']):
        state_dict.pop("id") # remove the null id before insert

    try:
        inserted_state = await db["states"].insert_one(state_dict)
        state = await db["states"].find_one({"_id": inserted_state.inserted_id})
    except Exception as e:
        print(f"Error with database: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to insert data in database: {e}")
    return State(**state)

@app.get("/graph")
async def get_states(n: int = 10):
    print(f"Return graph size: {n}")
    try:
        state_collection = await db["states"].find().to_list(length=n)
        # print(f"{n} States collected: {state_collection}")
    except Exception as e:
        print(f"Error with database: {e}")
        HTTPException(status_code=500, detail=f"Failed to retrieve list from database{e}")
    return StateCollection(states=state_collection).states