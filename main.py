import logging
import os
from logging.handlers import RotatingFileHandler

import globals
import socketio
from apiRequests import make_sql_request
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from helpers import (
    delete_history,
    get_cursor,
    get_user_history,
    send_response,
    start_history,
)

# Set up the logging
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s %(name)s %(levelname)s: %(message)s",
    handlers=[
        RotatingFileHandler("app.log", maxBytes=1000000, backupCount=3),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)

# Create the FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=eval(os.getenv("ALLOWED_HOSTS")),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the global variables
globals.init()

# Add CORS middleware
load_dotenv()

sio = socketio.AsyncServer(
    async_mode="asgi", cors_allowed_origins=eval(os.getenv("ALLOWED_HOSTS"))
)
app = socketio.ASGIApp(sio, app)
client_environments = {}


@sio.event
async def connect(sid, environ):
    start_history(environ["REMOTE_ADDR"])
    client_environments[sid] = environ


@sio.event
async def disconnect(sid):
    if client_environments[sid]:
        delete_history(client_environments.get(sid)["REMOTE_ADDR"])
        del client_environments[sid]


@sio.on("SqlExplorer")
async def SqlExplorer(sid, data):
    try:
        cursor = get_cursor(data["uid"], data["db"])
        data["user"] = get_user_history(client_environments.get(sid)["REMOTE_ADDR"])
        data["sid"] = sid

        if cursor:
            await make_sql_request(data, cursor, sio)
        else:
            raise Exception("Authentication error")

    except Exception as exc:
        await send_response([exc.args[0]], sid, sio)
