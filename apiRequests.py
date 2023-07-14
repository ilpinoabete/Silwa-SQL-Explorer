#from __future__ import absolute_import 
import os
import json
import openai
from dotenv import load_dotenv
from helpers import parse_response,  create_conn, log_query, comment_query
from Const import SQL_REQUEST, SQL_SINTAX, SINTAX

#credentials for openai api
openai.api_key = os.getenv('OPENAI_KEY')

#function that creates the sql query with openai api
def get_sql_query(api_query):
    query = SQL_REQUEST + api_query + SQL_SINTAX
    try:
        response = str(openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages=[
                    {"role": "system", "content": "You are an helpful assistant, answer the questions as shortly as possible"},
                    {"role": "user", "content": query}
                ],
                temperature = 0.1
            ))
        response = (parse_response(response))

        log_query(api_query, response, query)

        return response
    except Exception as exc:
        return (f"Error in get sql query: {str(exc)}")

#function that makes the sql request
def make_sql_request(query):

    try:
        sqlquery = get_sql_query(query)

        load_dotenv()
        connection = create_conn()
        cursor = connection.cursor()
        cursor.execute(sqlquery)

        rows = cursor.fetchall()
        column_names = [column[0] for column in cursor.description]

        #if the query is empty or the result is empty return empty list
        if sqlquery == '' or len(column_names) <= 0 or len(rows) <= 0:
            return [[], []]

        #if the query is not empty and the result is not empty return the result
        return [column_names, rows]
     
    except Exception as exc:
        return(f"Error in sql request: {str(exc)}\nThe query was: {sqlquery}")

#same funciton as before but the return is a json
def make_sql_request_json(query):
    try:
        sqlquery = get_sql_query(query)

        #if the query is empty return empty list
        if sqlquery == '':
            return []

        load_dotenv()
        connection = create_conn()
        cursor = connection.cursor()
        
        results = cursor.execute(sqlquery).fetchall()
        columns = [column[0] for column in cursor.description]
        data = {"data": []}

        #create a json with the result of the query
        for row in results:
            data["data"].append(dict(zip(columns, row)))
        
        json_data = json.dumps(data, indent=4, sort_keys=True, default=str)

        #if the query is not empty and the result is not empty return the result
        return json_data
     
    except Exception as exc:
        return(f"Error in sql request: {str(exc)}\nThe query was: {sqlquery}")



#function that use openai api to comment the data of the sql query
def comment_response(init_query, data_frame):

    query = f"Data questa domanda: {init_query} e questa risposta: {data_frame}, commentami in breve i dati ricevuti"

    try:
        response = openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages=[
                    {"role": "system", "content": "You are chat assistant"},
                    {"role": "user", "content": query}
                ],
                temperature = 0.1
            )
        response = str(response['choices'][0]['message']["content"])

        comment_query(query, response, data_frame)

        return response
    except Exception as exc:
        return (f"Error in comment: {str(exc)}")

#function that use openai api to get the context of the user query
def get_context(query):
    query = f"Data questa query: {query}\nSe la query è su dati provenienti da un magazzino rispondi 0, se invece sulla documentazione di un software rispondi 1\n{SINTAX}"

    try:
        response = openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages=[
                    {"role": "system", "content": "You are chat assistant"},
                    {"role": "user", "content": query}
                ],
                temperature = 1
            )
        response = str(response['choices'][0]['message']["content"])

        return response
    except Exception as exc:
        return (f"Error in comment: {str(exc)}")

print(get_context("Cos'è una missione"))