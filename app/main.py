from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.plans import router as plans_router
from app.api.upload import router as upload_router

app = FastAPI(title="FREITIR API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "FREITIR backend is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(upload_router)
app.include_router(plans_router)