from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from pydantic import BaseModel, Field
from markdown import markdown

import re
from datetime import timedelta, datetime

app = FastAPI()
@app.get("/")
async def root():
    file_content = open("../README.md", "r").read()
    return HTMLResponse(markdown(file_content))

def get_sunset_time():
    # Placeholder function to simulate getting sunset time
    
    return "18:30:00"

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
    preferences_dict = preferences.model_dump()
    start_time = datetime.strptime(preferences_dict["user_light"], "%H:%M:%S")
    print("Start time:", start_time.time())
    print("Light duration:", preferences_dict["light_duration"])
    
    duration = parse_time(preferences_dict["light_duration"])

    preferences_dict["light_time_off"] = (start_time + duration).time()
    print("Light time off:", preferences_dict["light_time_off"])
    return preferences

#on startup
@app.on_event("startup")
async def startup_event():
    await update_settings(Settings(user_temp=30, user_light="18:30:00", light_duration="4h"))