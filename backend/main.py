from fastapi import FastAPI

app = FastAPI()

@app.get('/')
def read_root():
    return {"msg: amu app server is running"}