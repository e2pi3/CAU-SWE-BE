from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "CAU-SWE-BE API"}