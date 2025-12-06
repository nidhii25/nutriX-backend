from fastapi import FastAPI
from app.routes import users, onboarding, plans
from fastapi.middleware.cors import CORSMiddleware
from app.database.base import Base
from app.database.connection import engine
app = FastAPI(title="AI Nutrition Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# register routers
app.include_router(onboarding.router, prefix="/onboarding")
app.include_router(plans.router, prefix="/plans")
app.include_router(users.router, prefix="/users")

@app.on_event("startup")
async def on_startup() -> None:
    # Ensure database tables exist before handling requests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
def root():
    return {"message": "Backend alive"}
