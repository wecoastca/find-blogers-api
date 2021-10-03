from fastapi.params import Form
from LabelUpBot import LabelUpBot
from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

from starlette.responses import StreamingResponse
from EasyPrBot import EasyPrBot_Filters


app = FastAPI()

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

    return StreamingResponse(chosen_blogers, media_type="application/octet-stream")


@app.post("/analyzeBlogers/")
async def analyzeBlogers(file: UploadFile = Form(...), numFirstBloger: int = Form(...), numLastBloger: int = Form(...), apiHash: str = Form(...), apiId: str = Form(...), phone: str = Form(...)):
    labelup_bot = LabelUpBot(file, numFirstBloger,
     numLastBloger, apiHash, apiId, phone)
    blogers_dict = labelup_bot.LU_get_short_data(file)
    response = labelup_bot.get_LU_full_info(blogers_dict)
    return StreamingResponse(response, media_type="application/octet-stream")
