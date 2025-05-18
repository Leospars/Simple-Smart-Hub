from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from pydantic import BaseModel, Field
from markdown import markdown

app = FastAPI()
@app.get("/")
async def root():
    file_content = open("../README.md", "r").read()
    return HTMLResponse(markdown(file_content))
