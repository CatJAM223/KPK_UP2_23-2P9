import random
from fastapi import FastAPI

app = FastAPI()

@app.get('/users/info/me/')
async def decode_jwt():
    return random.randint(1,6)
