from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

from starlette.responses import StreamingResponse
from EasyPrBot import EasyPrBot_Filters


app = FastAPI()

origins = [
    "https://localhost",
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:3000/"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)

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
    easyprbot_filter = EasyPrBot_Filters()
    _ = easyprbot_filter.get_categories()

    min_price, max_price = item.adPrice
    min_auditory_arrival, max_auditory_arrival = item.audienceArrival
    min_price_per_follower, max_price_per_follower = item.subPrice

    query = {'page_num': '1',
         'min_price': str(min_price),
         'max_price': str(max_price),
         'bloger_categories': item.categories,
         'max_auditory_arrival': str(max_auditory_arrival),
         'min_auditory_arrival': str(min_auditory_arrival),
         'min_price_per_follower': str(min_price_per_follower),
         'max_price_per_follower': str(max_price_per_follower),
         'ad_type': item.adFormat}

    chosen_blogers = easyprbot_filter.get_all_pages(query, item.filename)

    response = StreamingResponse(chosen_blogers, media_type="application/octet-stream")
    # response.headers["Content-Disposition"] = "attachment;filename=my_pod.xlsx"
    return response

@app.post("/analyzeBlogers/")
async def analyzeBlogers(item: Analyzer):
    return item