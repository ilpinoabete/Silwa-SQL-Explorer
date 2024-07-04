import os
import logging
import globals
import socketio
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from logging.handlers import RotatingFileHandler
from fastapi.middleware.cors import CORSMiddleware
from apiRequests import make_sql_request, get_screenshot_help
from helpers import get_cursor, send_response, start_history, delete_history, get_user_history

# Set up the logging
logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s %(name)s %(levelname)s: %(message)s',
                    handlers=[
                        RotatingFileHandler("app.log", maxBytes=1000000, backupCount=3),
                        logging.StreamHandler()
                    ])

logger = logging.getLogger(__name__)

# Create the FastAPI app
app = FastAPI()

# Initialize the global variables
globals.init()

# Add CORS middleware
load_dotenv()

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins=eval(os.getenv("ALLOWED_HOSTS")))
app = socketio.ASGIApp(sio, app)
client_environments = {}

@sio.event
async def connect(sid, environ):
    start_history(environ['REMOTE_ADDR'])
    client_environments[sid] = environ
    
    
@sio.event
async def disconnect(sid):
    if client_environments[sid]:
        delete_history(environ['REMOTE_ADDR'])
        del client_environments[sid]


@sio.on("SqlExplorer")
async def SqlExplorer(sid, data):
    try:
        cursor = get_cursor(data["uid"], data["db"])
        data["user"] = get_user_history(client_environments.get(sid)["REMOTE_ADDR"])
        
        if cursor:
            await make_sql_request(data, cursor, sio)
        else:
            raise Exception("Authentication error")
            
    except Exception as exp:
        await send_response([str(exp), data["query"], type], sio, error=True)


@sio.on("ScreenshotHelper")
async def ScreenshotHelper(sid, data):
    try:
        data["user"] = get_user_history(client_environments.get(sid)["REMOTE_ADDR"])
        await get_screenshot_help(data, sio)

    except Exception as exp:
        await send_response([str(exp), data["query"], type], sio, error=True)

