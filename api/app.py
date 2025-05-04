from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from markdown import markdown
from uuid import uuid4, UUID

app = FastAPI()
@app.get("/")
async def root():
    file_content = open("../README.md", "r").read()
    return HTMLResponse(markdown(file_content))

@app.get("/api")
async def get_all_fruits() :
    return JSONResponse({
        "message": "Successfully retrieved fruits",
        "fruits": "fruits_json"
    }, status_code=200)

print("API is running on http://localhost:8000")