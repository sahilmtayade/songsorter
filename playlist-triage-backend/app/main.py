from fastapi import FastAPI

from app.routers import auth, triage

app = FastAPI()

app.include_router(auth.router)
app.include_router(triage.router)


@app.get("/")
def root():
    return {"message": "Welcome to Playlist Triage API"}
