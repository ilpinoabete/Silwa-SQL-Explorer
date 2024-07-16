import logging

import globals
import pandas as pd
from helpers import (
    append_previous_msgs,
    get_db_info,
    parse_response,
    sanitize_query,
    send_response,
)
from openai import OpenAI, RateLimitError

# Set up the logging
logger = logging.getLogger(__name__)

# Credentials for OpenAI API
client = OpenAI()


def get_sql_query(data, db_info, cursor):
    """
    Function that creates the SQL query startung from the data provided in the request and the database informations.

    :param data: The data provided in the request
    :param db_info: The database informations retrived by the function get_db_info
    :param cursor: The cursor to the database retrived by the function get_cursor
    :return: The SQL query

    """

    global previous_msgs

    model = data["model"]
    query_utente = data["query"]

    user_msgs = data["user"]["sql_search"]

    query = (
        f"SQL database's tables informations:\n{db_info}\nfollowing prompt:\n"
        + query_utente
        + globals.SQL_SINTAX
    )
    try:
        # Create the chat completion with the OpenAI APIs
        response = str(
            client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            """
                        
                        This is the message history, use it to get the context of the conversation and to avoid repeating the same errors, the user may refer to previous messages, pay attention to the user's questions to understand, if necessary, which message he is referring to.
                        If it's not specified, it refers to the last message you sent to it.
                        Note that the columns name may be different from the ones in the database so please refer to the database's information i gave you. Note that the user may change his questions so use these data only if the topic of the conversation is the same"""
                            if user_msgs != []
                            else ""
                        ),
                    },
                    {
                        "role": "system",
                        "content": (str(user_msgs) if user_msgs != [] else ""),
                    },
                    {"role": "system", "content": query},
                ],
                temperature=0.1,
            )
        )

        # Return the sanitized and parsed query
        return sanitize_query(parse_response(response))

    except Exception as exc:
        # if and error occurs, log it and return an empty string for the make_sql_request function to handle the error
        logger.error(f"Error generating SQL query: {exc.args[0]}", exc_info=True)
        raise Exception(f"Errore nella generazione della query:\n{exc.args[0]}")


async def comment_response(sql_data, query_sql, data, client_socket, db_info):
    """
    Function that uses OpenAI API to create a user friendly comment to the SQL query response starting from starting from the sql query and the data retrived from the database.
    It sends the response stream to the client_socket and returns the response as a string for it to be added in the messages history.

    :param sql_data: The data retrived from the SQL query
    :param query_sql: The SQL query used to retrive the data
    :param data: The data provided in the request
    :param client_socket: The client socket to send the response
    :param db_info: The database informations retrived by the function get_db_info
    :return: The response as a string

    """

    global previous_msgs

    query_utente = data["query"]
    variant = data["type"]
    sid = data["sid"]
    model = data["model"]
    user_msgs = data["user"]["sql_search"]

    response = ""
    first_chunk = True

    try:
        if client_socket:
            # Create the chat completion with the OpenAI APIs
            stream = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"""
                            
                            Questo è lo storico dei messaggi, tienilo in considerazione per la tua rsiposta nel caso l'argomento della conversazione sia lo stesso.
                            L'utente potrebbe fare riferimento a messaggi precendenti, presta attenzione alle domande dell utente per capire, eventualmente, a che messaggio si riferisce; se non è specificato si riferisce all'ultimo messaggio che gli hai inviato.
                            Tieni presente che l'utente potrebbe fare riferimento alla tabelle presenti nello storico dei messaggi.
                            Ecco la cronologia dei messaggi: {user_msgs}"""
                            if user_msgs != []
                            else ""
                        ),
                    },
                    {
                        "role": "system",
                        "content": f"""
                                                    utente posto domanda {query_utente} eseguita query ottenere dati rispondere: {query_sql}.
                                                    utilizza i dati per dare una risposta all'utente come se fossi un assistente.
                                                    non inserire riferimenti alla query effettuata o al database.
                                                    NON INSERIRE I DATI sottoforma di tabella o lista, l'utente li può già vedere, cerca di dare una risposta alla domanda.
                                                    """,
                    },
                    {
                        "role": "system",
                        "content": str(sql_data),
                    },
                ],
                temperature=0.5,
                stream=True,
            )

            # Send each chunk of the response stream to the client
            for chunk in stream:
                response += str(chunk.choices[0].delta.content)
                await send_response(
                    [
                        chunk.choices[0].delta.content,
                        query_utente,
                        variant,
                        (
                            pd.DataFrame(sql_data).to_html()
                            if (first_chunk and chunk.choices[0].delta.content != "")
                            else ""
                        ),
                    ],
                    sid,
                    client_socket,
                    "SqlExplorerResponse",
                )

                first_chunk = (
                    False
                    if first_chunk and chunk.choices[0].delta.content != ""
                    else True
                )

            # Send the final response to the client
            await send_response(
                ["DONE", query_utente, variant, ""],
                sid,
                client_socket,
                "SqlExplorerResponse",
            )

            # Return the response for it to be added in the messages history
            return response

        else:
            raise Exception("Server Timeout error")

    except RateLimitError:
        # If the rate limit is reached, log the error and send an error message to the client
        logger.error("Rate limit error", exc_info=True)
        raise Exception("Ci sono troppi dati a riguardo, puoi essere più specifico?")

    except Exception as exc:
        # Log the general error and send and raise an error
        logger.error(f"Error generating comment response: {exc.args[0]}", exc_info=True)
        raise Exception(f"Errore nella generazione della risposta: {exc.args[0]}")


async def make_sql_request(data, api_cursor, sio):
    """
    This is the enpoint of the SqlExplorer event. It receives the data from the client_socket and uses the OpenAI API to generate a SQL query and execute it on the database.
    It also calls the comment_response function to generate a user friendly comment to the SQL query response and adds it to the message history.

    :param data: The data provided in the request
    :param api_cursor: The cursor to the database retrived by the function get_cursor
    :param sio: The client socket to send the response

    """

    # Initialize used variables
    query_utente = data["query"]
    variant = data["type"]
    user = data["user"]
    sid = data["sid"]

    cursor = api_cursor
    client_socket = sio

    try:

        db_info = str(get_db_info(cursor))

        # Sanity check
        if query_utente == "":
            send_response("Empty query", sid, sio)
            raise Exception("Empty query")

        # Get the SQL query
        query_sql = get_sql_query(data, db_info, cursor)

        # Execute the query and create a JSON with its results if it's not empty
        try:
            results = cursor.execute(query_sql).fetchall()
        except Exception as exc:
            raise Exception(
                f"C'è stato un errore nell'esecuzione della query: {exc.args[0]}"
            )

        if results == []:
            raise Exception("Nessun risultato trovato")

        columns = [column[0] for column in cursor.description]
        query_data = {column: [] for column in columns}

        for row in results:
            for column, value in zip(columns, row):
                query_data[column].append(value)

        # Create the response and append the request to the messages history
        await comment_response(query_data, query_sql, data, client_socket, db_info)

        history_data = {
            "user": user,
            "query_utente": query_utente,
            "query_sql": query_sql,
            "table": query_data,
        }

        append_previous_msgs(history_data)

    except Exception as exc:
        # Log the error and send the error message to the client
        logger.error(
            f"Error executing SQL request for query: {query_utente}", exc_info=True
        )
        raise Exception(exc.args[0])
