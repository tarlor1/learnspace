from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI"}

@app.get("/posts/{id}")
def read_post(id: int):
    return {"post_id": id}
