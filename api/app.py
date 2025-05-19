from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from pydantic import BaseModel, Field
from markdown import markdown
from uuid import uuid4
import requests 

import re
from datetime import timedelta, datetime

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # on startup
    await update_settings(Settings(user_temp=30, user_light="sunset", light_duration="4h"))
    yield
    # on shutdown
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)
@app.get("/")
async def root():
    file_content = open("../README.md", "r").read()
    return HTMLResponse(markdown(file_content))

def get_sunset_time() -> datetime:
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
        return sunset_time
    else: 
        raise HTTPException(status_code=500, detail="Failed to get IP")

class Settings(BaseModel):
    user_temp: int
    user_light: str = Field(default_factory=get_sunset_time)
    light_duration: str

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

@app.put("/settings")
async def update_settings(preferences: Settings):
    preferences_dict = {"_id": uuid4()}
    preferences_dict.update(preferences.model_dump())
    user_light = get_sunset_time().strftime("%H:%M:%S") if preferences_dict["user_light"] == "sunset" \
        else preferences_dict["user_light"]
    start_time = datetime.strptime(user_light, "%H:%M:%S")

    print("Start time:", start_time.time())
    print("Light duration:", preferences_dict["light_duration"])
    
    duration = parse_time(preferences_dict["light_duration"])

    preferences_dict["light_time_off"] = (start_time + duration).time()
    print("Light time off:", preferences_dict["light_time_off"])
   
    return preferences_dict

