from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from app.routers import auth, users, resumes, skills, recommendations

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Career Coach API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5180"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(resumes.router)
app.include_router(skills.router)
app.include_router(recommendations.router)

@app.get("/")
def root():
    return {"message": "AI Career Coach API is running"}