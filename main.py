from fastapi import FastAPI
from helpers import check_login
from apiRequests import  make_sql_request, comment_response
from fastapi.middleware.cors import CORSMiddleware

# Create the FastAPI app
app = FastAPI()

# Add CORS middleware
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:5500"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the main endpoint
@app.get("/api/hello")
def get_response():
    return("Hello")

@app.get("/api/SILWA/{query}")
def get_response(query :str, id :str):

    if check_login(id):
        try:
            return make_sql_request(query)

        except Exception as exp:
            return{ 'Error' : str(exp)}
    else:
        return "Error: Login id not valid"

@app.get("/api/CommentResponse/{query}")
def get_response(query :str, data, id :str):
    if check_login(id):
        try:
            return comment_response(query, str(data))

        except Exception as exp:
            return{ 'Error' : str(exp)}
    else:
        return "Error: Login id not valid"
