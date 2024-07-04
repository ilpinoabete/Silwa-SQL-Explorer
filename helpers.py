import re
import os
import globals
import logging
import socketio
import pandas as pd
import pypyodbc as db
from dotenv import load_dotenv

load_dotenv()

# Set up the logging
logger = logging.getLogger(__name__)


# Functions that parse the response of the OpenAI API using the tag <tag> and </tag> and removing the \n \t \r and \	
def parse_response(response, init_subStr="```sql", end_subStr="```"):
    # Replace the initial and final tags with a $ to find the start and end of the response
    response = response.replace(str(init_subStr), "$")
    response = response.replace(str(end_subStr), "$")
    start = 0
    end = 0

    for i in range(len(response)):
        if(response[i] == "$"):
            start = i + 1
            break
    
    j = len(response)-1
    while j > 0:
        if(response[j] == "$"):
            end = j
            break
        j -= 1

    response = str(response[start:end])

    # Replace unwanted characters with spaces
    response = response.replace('\\n', ' ')
    response = response.replace('\\t', ' ')
    response = response.replace('\\r', ' ')
    response = response.replace('\\', ' ')
    response = response.replace('<br>', ' ')
    return response


# Function that connects to the database
def connect_to_db(Driver, Server, Database, Uid, Pwd):
    try:
        connection = db.connect(f'Driver={Driver};Server={Server};Database={Database};UID={Uid};PWD={Pwd}')
        if connection is not None:
            return connection
        else:
            raise Exception("Error creating database connection")

    except Exception:
        logger.error("Error creating database connection", exc_info=True)


# Create the connection to the database
def get_cursor(Uid, Db):
    DRIVER_NAME = os.getenv('DRIVER_NAME')
    SERVER_NAME = os.getenv('SERVER_NAME')
    DB_NAME = os.getenv('DB_NAME')
    UID = os.getenv('UID')
    PWD = os.getenv('PASS')

    try:
    
        # Getting credentials to connect to the database that the user is allowed to access
        cursor = connect_to_db(DRIVER_NAME, SERVER_NAME, DB_NAME, UID, PWD).cursor()

        resposnse = cursor.execute(f"""
                                   
                                    DECLARE @DbsId INT
                                    SELECT @DbsId = (SELECT DbsId FROM AuthInfo WHERE Uid = '{Uid}')

                                    SELECT Server, Driver, Db, Usr, Pwd FROM DbsInfo WHERE DbsId=@DbsId  AND Db = '{Db}'

                                    """).fetchall()

        if resposnse == []:
            return False
        else:
            resposnse = resposnse[0]

            SERVER_NAME = resposnse[0]
            DRIVER_NAME = resposnse[1]
            DB_NAME = resposnse[2]
            UID = resposnse[3]
            PWD = resposnse[4]


            # Getting the connection to the database that the user is allowed to access
            connection = connect_to_db(DRIVER_NAME, SERVER_NAME, DB_NAME, UID, PWD)

            if connection is not None:
                return connection.cursor()
            else:
                raise Exception("Error creating database cursor")

    except Exception:
        logger.error("Error creating database cursor", exc_info=True)


# Function that returns the tables of the  that the user is allowed to access
def get_db_info(cursor):
    try:
        db_info = []

        # If the database has the infoTables table, get the info from there
        if (cursor.execute("select * from INFORMATION_SCHEMA.TABLES where TABLE_NAME = 'infoTables'").fetchall() != []):      
            tables = cursor.execute("SELECT * FROM infoTables").fetchall()
            for table in tables:
                info_table = cursor.execute(f"SELECT * FROM {table[0]}").fetchall()
                table_info = {}

                table_info["table_name"] = info_table[0][0]
                table_info["content"] = table[1]
                table_info["columns"] = []

                for column in info_table:
                    table_info["columns"].append({
                        "column_name": column[1],
                        "data_type": column[2],
                        "content_description": column[3],
                    })
                
                db_info.append(table_info)
        # else get the tables from the database and manually retrive the info
        else:
            tables = cursor.execute(f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE';").fetchall()

            for table in tables:
                db_info.append({
                    "table_name": table[0],
                    "columns" : get_table_info(table[0], cursor)
                    })
        
        return db_info
    except Exception:
        logger.error("Error getting the tables", exc_info=True)


# Function that returns the tables, the columns, and their datatypes of the database
def get_table_info(table_name, cursor):
    try:
        # Get the columns of the table
        cursor.execute(f"""
        SELECT COLUMN_NAME, COLUMN_DEFAULT, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = '{table_name}';
        """)
        types = cursor.fetchall()
        columns = ['COLUMN_NAME', 'COLUMN_DEFAULT', 'DATA_TYPE']
        
        if len(types) == 0:
            return "Table not found in the database"

        # Return the columns and their data types in JSON format
        return pd.DataFrame(types, columns=columns).to_json(indent=4, orient='records')
    except Exception:
        logger.error("Error getting the data types of the table", exc_info=True)


# Function that sends a response chunk to the frontend
async def send_response(response, client_socket, error=False):
    try:
        # If the response is not an error and it is not empty, send it to the frontend
        if not error:
                if response is not None or response != "":
                    await client_socket.emit("SqlExplorerResponse", response if type(response[1]) == str else "DONE")
                else:
                    client_socket.emit("SqlExplorerResponse", "DONE")
        # If the response is an error, send it to the frontend with the error flag
        else:
            await client_socket.emit("err", response)
    except Exception as exp:
            logger.error(f"Error sending response {exp}", exc_info=True)


# Function that sanitizes the queries
def sanitize_query(query):
    # Remove any potentially harmful characters from the query
    sanitized_query = re.sub(r'[;\'"] *--.*', '', str(query))

    # Check if the query contains dangerous keywords
    dangerous_sql_keywords = [
        "drop",
        "delete",
        "truncate",
        "alter",
        "update",
        "exec",
        "backup",
        "restore",
        "grant",
        "revoke"
    ]

    for keyword in dangerous_sql_keywords:
        if keyword in sanitized_query.lower():
            return False
    
    return sanitized_query


# Function that starts the history of the user once it connects
def start_history(conn_ip):
    # Check if the user already exists
    user = False
    for list_user in globals.previous_msgs:
        if list_user["ip"] == conn_ip:
            user = list_user
            break
    
    # If the user does not exist, create a new user
    if not user:
        globals.previous_msgs.append({
            "ip": conn_ip,
            "sql_search": [],
            "img_help": []
        })
    

# Function that deletes the history of the user one it disconnects
def delete_history(conn_ip):
    # Check if the user already exists
    user = False
    for list_user in globals.previous_msgs:
        if list_user["ip"] == conn_ip:
            previous_msgs.remove(list_user)
            break


# Function that retrieves the history of the user by its IP
def get_user_history(conn_ip):
    # Check if the user already exists
    user = None
    for list_user in globals.previous_msgs:
        if list_user["ip"] == conn_ip:
            user = list_user
            break
    
    return user


# Function that appends the previous messages to the user's history
def append_previous_msgs(data):
    user = data["user"]
    
    # Append the new message to the correct section of the user's history 

    if type(data["img"]) == bool and not data["img"]:
        data["user"]["sql_search"].append({
                "query_utente":  data["query_utente"],
                "query_sql": data["query_sql"],
                "response": data["response"]
            })
    else:
        user["img_help"].append({
                "query_utente":  data["query_utente"],
                "response": data["response"],
            })

    return True

