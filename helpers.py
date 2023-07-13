import os
import csv
import pandas as pd
import pypyodbc as db
from dotenv import load_dotenv


#logs of the queries and the comments

def log_query(query, request, complete_query):
    with open("QueryLogs.csv", "a", newline='') as file:
        writer = csv.writer(file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow([query, request, complete_query])
        writer.writerow([" "])

def comment_query(query, response, data_frame):
    with open("CommentLogs.csv", "a", newline='') as file:
        writer = csv.writer(file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow([query, response, data_frame])
        writer.writerow([" "])

#functions that parse the response of the openai api using the tag <tag> and </tag> and removing the \n \t \r and \	

def parse_response(response, init_subStr = "<tag>", end_subStr = "</tag>"):
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
    response = response.replace('\\n', ' ')
    response = response.replace('\\t', ' ')
    response = response.replace('\\r', ' ')
    response = response.replace('\\', ' ')
    return response

#create the connection to the database

def create_conn():
    load_dotenv()

    SERVER_NAME = os.getenv('SERVER_NAME')
    DB_NAME = os.getenv('DB_NAME')
    USERNAME = os.getenv('UID')
    PASSWORD = os.getenv('PASS')

    conn_string = "Driver={ODBC Driver 18 for SQL Server};Server=" + SERVER_NAME + ";Database="+ DB_NAME +";Trusted_Connection=yes;TrustServerCertificate=yes;"

    return db.connect(conn_string)

#function that returns the tables, the columns and their datatypes of the database

def get_datatype(table_name):
    load_dotenv()
    connection = create_conn()
    cursor = connection.cursor()

    cursor.execute(f"""SELECT COLUMN_NAME, COLUMN_DEFAULT, DATA_TYPE
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = '{table_name}';
    """)
    types = cursor.fetchall()
    columns = ['COLUMN_NAME', 'COLUMN_DEFAULT', 'DATA_TYPE']

    return pd.DataFrame(types, columns=columns)

#check if the login id is in the users dictionary

def check_login(login_id):
    load_dotenv()
    users = eval(os.getenv('USERS'))

    for user in users:
        if user["Id"] == login_id:
            return True

    return False

