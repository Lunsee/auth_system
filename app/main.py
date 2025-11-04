from fastapi import FastAPI, Depends, HTTPException, status, Form, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
#from sqlalchemy.testing.pickleable import User
from starlette import status
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from app.db.database import engine, Base
from app import auth, users, admin
import logging
from dotenv import load_dotenv
import os
from pydantic import BaseModel
from app.dependencies import oauth2_scheme
from fastapi.middleware.cors import CORSMiddleware
from app.db.initial_data import init_db
from app.db.database import reset_database


# logger conf
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # format
    handlers=[
        logging.FileHandler('app.log'),  # app.log
        logging.StreamHandler()
    ]
)



app = FastAPI()


# настройка инфраструктуры
#templates = Jinja2Templates(directory="app/templates")
#app.mount("/static", StaticFiles(directory="static"), name="static")

#templates_path = os.path.abspath("templates")
#print(f"Absolute path to templates: {templates_path}")


app.include_router(auth.router, prefix="/auth", tags=["Auth"]) #auth endpoints
app.include_router(users.router, prefix="/users", tags=["users"]) #users endpoints
app.include_router(admin.router, prefix="/admin", tags=["admin"]) #users endpoints

#Base.metadata.create_all(bind=engine) #create all TABLES in db

logger = logging.getLogger(__name__)
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env") # env url
print(f".env path: {dotenv_path}")


load_dotenv(dotenv_path) # Load .env file

if os.path.exists(dotenv_path):
    logger.info(".env file successfully found.")
else:
    logger.warning(".env file not found or failed to load.")

@app.on_event("startup")
async def startup_event():
    print("🚀 Starting System API...")
    reset_database()
    init_db()
    print("✅ Database initialized!")
