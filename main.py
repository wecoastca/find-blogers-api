from fastapi import FastAPI, UploadFile
from pydantic import BaseModel
from typing import List

app = FastAPI()

class Filter(BaseModel):
    categories: List[str]   
    audienceArrival: List[int]
    adPrice: List[int]
    subPrice: List[int]
    adFormat: int
    filename: str

class Analyzer(BaseModel):
    file: UploadFile
    blogersInterval: List[int]
    apiHash: int
    apiId: int
    phone: str

@app.post("/getBlogers/")
async def getBlogers(item: Filter):
    return item

@app.post("/analyzeBlogers/")
async def analyzeBlogers(item: Analyzer):
    return item