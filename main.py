from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
from EasyPrBot import EasyPrBot_Filters
import io
import pandas as pd


app = FastAPI()

origins = [
    "https://localhost",
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:3000/"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

    chosen_blogers = easyprbot_filter.get_all_pages(query, save = True, filename = item.filename)
    stream = io.StringIO()
    xlw = pd.ExcelWriter(stream, engine='openpyxl')
    print(stream, -1)
    chosen_blogers.to_excel(xlw, sheet_name=item.filename)
    print(0)
    xlw.save()
    # headers = {
    #     'Content-Disposition': 'attachment; filename="filename.xlsx"'
    # }
    print(1)
    # stream.seek(0)
    return StreamingResponse(stream.getvalue(),media_type='application/octet-stream')

@app.post("/analyzeBlogers/")
async def analyzeBlogers(item: Analyzer):
    return item