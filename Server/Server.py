from fastapi import FastAPI
from quantum_RNG import quantum_random_number_generator

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
