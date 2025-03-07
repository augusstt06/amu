from fastapi import FastAPI

from app.test import testt

app = FastAPI()

@app.get('/')
def read_root():
    return {"msg: amu app server is running"}

@app.get('/test')
async def test():
    return await testt("강남구", 3)

