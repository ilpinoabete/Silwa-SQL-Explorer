import json
import base64
import globals
import logging
from openai import OpenAI, RateLimitError
from helpers import parse_response, send_response, sanitize_query, get_db_info, append_previous_msgs


# Set up the logging
logger = logging.getLogger(__name__)

# Credentials for OpenAI API
client = OpenAI()


# Function that creates the SQL query with OpenAI API
def get_sql_query(query_utente, data, db_info, cursor):
    global previous_msgs
    
    uid = data["uid"]
    model = data["model"]

    db_info = str(get_db_info(cursor))
    user_msgs = data["user"]["sql_search"]

    query = f"SQL database's tables informations:\n{db_info}\nfollowing prompt:\n" + query_utente + globals.SQL_SINTAX
    try:
        # Create the chat completion with the OpenAI APIs
        response = str(client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant, answer the questions as shortly as possible"},
                {"role": "assistant", "content": f"{f'This is the message history, use it to get the context of the conversation and to avoid repeating the same errors: {user_msgs}' if user_msgs else ''}. Note that the user may change his questions so use these data only if the topic of the conversation is the same" },
                {"role": "user", "content": query}
            ],
            temperature=0.2
        ))
        
        # Return the sanitized and parsed query 
        return sanitize_query(parse_response(response))
    
    except Exception as exc:
        logger.error("Error generating SQL query", exc_info=True)
        return f"Error in get sql query: {str(exc)}"


# Function that uses OpenAI API to comment on the data of the SQL query
async def comment_response(comment_data, query_sql, data, client_socket, db_info):
    global previous_msgs

    query_utente = data["query"]
    variant = data["type"]
    uid = data["uid"]
    model=data["model"]

    user_msgs = data["user"]["sql_search"]

    response = ""

    try:
        if client_socket:
            # Create the chat completion with the OpenAI APIs
            stream = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a chat assistant"},
                    {"role": "assistant", "content": f"{f'Questo è lo storico dei messaggi, tienilo in considerazione per la tua rsiposta nel caso largomento della conversazione sia lo stesso: {user_msgs}' if user_msgs != [] else ''}" },
                    {"role": "user", "content": f"""
                                                    L'utente ha posto questa domanda {query_utente} ed è stata eseguita questa query per ottenere i dati per rispondere: {query_sql}, utilizza i dati che ti sto per fornire ed eventuali suggerimenti presenti nel commento della query SQL per rispondere in maniera più completa e corretta possibile alla domanda.
                                                    Se possibile mandami la risposta in piccoli chunk di markdown per formattare la risposta ed inserisci eventiuali dati provenienti dalla query SQL in una tabella.
                                                    Non inserire la query SQL o riferimenti ad essa nel commento.
                                                    Se hai bisogno di informazioni sulle varie tabelle del database, le trovi qui {db_info}.     
                                                    """},
                    {"role": "assistant", "content": f"Ecco i dati che ho ottenuto {comment_data}"},
                ],
                temperature=0.1,
                stream=True
            )

            # Send each chunk of the response stream to the client
            for chunk in stream:
                response += str(chunk.choices[0].delta.content)
                await send_response([chunk.choices[0].delta.content, query_utente, variant], client_socket, 'SqlExplorerResponse')
                
            await send_response("---------------------------\n" + response, client_socket, 'SqlExplorerResponse')

            # Return the response for it to be added in the messages history
            return response
            
        else:
            raise Exception("Server Timeout error")
        
    except RateLimitError:
        logger.error(f"Rate limit error")
        await send_response(["Ci sono troppi dati a riguardo, puoi essere più specifico?", query_utente, variant], client_socket)

    except Exception as exc:
        logger.error(f"Error generating comment response for query: {query_utente} with data: {comment_data}", exc_info=True)
        return f"Error in comment: {str(exc)}"


# Function that executes the SQL request
async def make_sql_request(data, api_cursor, sio):
    # Initialize used variables
    query_utente = data["query"]
    variant = data["type"]
    user = data["user"]
    cursor = api_cursor
    client_socket = sio
    db_info = str(get_db_info(cursor))
    
    # Sanity check
    if query_utente == "":
        send_response("Empty query", sio)
        raise Exception("Empty query")
    
    try:
        # Get the SQL query
        query_sql = get_sql_query(query_utente, data, db_info, cursor)

        # If the query is empty of if it contains the drop or create keywords, return an error message
        if query_sql == '':
            raise Exception("Empty query")
        
        elif not query_sql:
            raise Exception("The query contains dangerous or forbidden keywords")

        # Execute the query and create a JSON with its results
        results = cursor.execute(query_sql).fetchall()
        columns = [column[0] for column in cursor.description]
        query_data = {
            "data": []
            }

        for row in results:
            query_data["data"].append(dict(zip(columns, row)))

        json_data = json.dumps(query_data, indent=4, sort_keys=True, default=str)

        # Create the response and append the request to the messages history
        commented_response = await comment_response(json_data, query_sql, data, client_socket, db_info)

        history_data = {
            "user" : user,
            "query_utente" : query_utente,
            "query_sql" : query_sql,
            "response" : commented_response,
            "img" : False
        }

        append_previous_msgs(history_data)

        return commented_response

    except Exception as exc:
        logger.error(f"Error executing SQL request for query: {query_utente}", exc_info=True)
        append_previous_msgs(history_data)
        await comment_response([f"Error in SQL request: {str(exc)}\nThe query was: {query_sql}", query_utente, variant], client_socket, error=True)


# Function that uses OpenAI API to generate a screenshot helper
async def get_screenshot_help(data, client_socket):
    # Sanity check
    if data["query"] == "":
        send_response("Empty query", client_socket)
        raise Exception("Empty query")
    
    
    response = ""
    with open(data["img"], "rb") as img_file:
        b64_img = base64.b64encode(img_file.read()).decode("utf-8")


    # Create the chat completion with the OpenAI APIs
    stream = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{b64_img}",
                        "detail": "auto"
                    },
                },
                {
                    "type": "text",
                    "text": data["documentation"] + f"Con riferimento {'alla documentazione che ti ho appena fornito e' if data["documentation"] != '' else ''} alle foto che ti ho inviato, puoi creare una guida passo passo con precisi riferimenti all'interfaccia grafica del software che sto utilizzando per risolvere il problema dell'utente o rispondere alla sua domanda? Invia la risposta in piccoli chunk in markdown" + data["query"]
                },
            ],
        }
    ],
    temperature=data["temperature"],
    stream=True,
    )

    for chunk in stream:
        response += str(chunk.choices[0].delta.content)
        await send_response([chunk.choices[0].delta.content, data["query"], data["type"]], client_socket, 'ScreenshotHelperResponse')

    history_data = {
            "user" : data["user"],
            "query_utente" : data["query"],
            "query_sql" : "",
            "response" : response,
            "img" : data["img"]
        }
    
    append_previous_msgs(history_data)
    
    await send_response("---------------------------\n" + response, client_socket, 'ScreenshotHelperResponse')
        
    return response

