import os
from contextlib import asynccontextmanager
from datetime import timedelta, datetime
from typing import Annotated

#from bson import ObjectId
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from markdown import markdown
#from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, BeforeValidator, Field
import requests
import re

from os import path
dir_path = path.dirname(path.abspath(__file__)) 

# Database

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017") # Default to local MongoDB
# connection = AsyncIOMotorClient(MONGO_URI)
# db = connection.get_database("simple-smart-hub")

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
PyObjectID = Annotated[str, BeforeValidator(str)]
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
        res = requests.get(f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}")
        
        if(res.status_code != 200):
            raise HTTPException(status_code=500, detail="Failed to get sunset time")
        sunset = res.json()["results"]["sunset"]
        try: 
            sunset_time = datetime.strptime(sunset, "%H:%M:%S %p")
        except Exception as e:
            raise HTTPException(status_code=500, detail="Sunset time format may have changed from 03:45:00 PM")
        print(f"Sunset time today - {datetime.now().date()}: {sunset_time.time()}")
        return sunset_time.strftime("%H:%M:%S")
    else: 
        raise HTTPException(status_code=500, detail="Failed to get IP")

# Routes
@app.get("/")
async def root():
    file_content = open(path.join(dir_path, "..", "README.md"), "r").read()
    return HTMLResponse(markdown(file_content))

@app.get("/test")
async def test():
    return {"message": "Your vercel app is up and running 👍"}

# Routes for settings
class Settings(BaseModel):
    user_temp: int
    user_light: str = Field(default_factory=get_sunset_time)
    light_duration: str

@app.put("/settings")
async def update_settings(preferences: Settings):
    # Random user ID, for future purposes get user id from login
    preferences_dict = {"_id": None} 
    preferences_dict.update(preferences.model_dump())
    user_light = get_sunset_time() if preferences_dict["user_light"] == "sunset" \
        else preferences_dict["user_light"]
    start_time = datetime.strptime(user_light, "%H:%M:%S")

    print("Start time:", start_time.time())
    print("Light duration:", preferences_dict["light_duration"])
    
    duration = parse_time(preferences_dict["light_duration"])

    preferences_dict["light_time_off"] = str((start_time + duration).time())
    print("Light time off:", preferences_dict["light_time_off"])

    # update user settings
    # await db["settings"].update_one({"_id": preferences_dict["_id"]}, {"$set": preferences_dict}, upsert=True)
    # preferences_dict = await db["settings"].find_one({"_id": preferences_dict["_id"]}) # return with auto generated id parameter
    return Settings(**preferences_dict)
'''
# Routes for State
class State(BaseModel):
    id: PyObjectID | None = Field(default=None, alias="_id")
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

    inserted_state = await db["states"].insert_one(state_dict)
    
    state = await db["states"].find_one({"_id": inserted_state.inserted_id})
    return State(**state)

@app.get("/graph")
async def get_states(n: int = 10):
    print(f"Return graph size: {n}")
    state_collection = await db["states"].find().to_list(length=n)
    return StateCollection(states=state_collection).states

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(
#         "app:app",
#         host="127.0.0.1",
#         port=8000,
#         reload=True,
#         reload_dirs=[dir],
#         reload_excludes=[
#             "*/.git/*",
#             "*/__pycache__/*",
#             "*.pyc",
#             "*/.pytest_cache/*",
#             "*/.vscode/*",
#             "*/.idea/*"
#         ],
#         reload_delay=1,
#         reload_includes=["*.py", "*.html", "*.css", "*.js"]
#     )
'''
