from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.analytics import router as analytics_router
from app.api.carriers import router as carriers_router
from app.api.execution import router as execution_router
from app.api.intelligence import router as intelligence_router
from app.api.plans import router as plans_router
from app.api.simulator import router as simulator_router
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
app.include_router(execution_router)
app.include_router(carriers_router)
app.include_router(analytics_router)
app.include_router(intelligence_router)
app.include_router(simulator_router)
