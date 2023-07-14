import streamlit as st
import pandas as pd
import requests
import csv

#Logging delle eccezioni
def log_exception(process, error):
    with open("Exceptions.csv", "a", newline='') as file:
        writer = csv.writer(file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow([process, error])
        writer.writerow([" "])

def make_usr_message(content):
    if str(content) != "False" and str(content) != "":
        with st.chat_message('user', avatar="🧑‍💻"):
            st.write(content)

#conversioni di stringhe del tipo "[]" in array
def eval_array(array):
    for element in array:
        if type(element) == str:
            element = eval(element)
    return array

def ApiMsg_Docs(content):
    with st.chat_message('API', avatar="🤖"):
        st.write(content)


def ApiMsg_SQL(query, data, content = "Nessun dato recuperato", first_time = True):
    with st.chat_message('API', avatar="🤖"):
        #conversione di stringhe di dati in array
        if type(data) == str:
            data= eval(data)
        data = eval_array(data)
        
        #controllo che la query a SQL abbia fornito dei dati
        if data[1] != []:
            data[1] = eval_array(data[1])

            #creazione del dataframe da visualizzare
            df = response_to_dataframe(data[0], data[1])

            #aggiunta del messaggio alla history (viene eseguito solo una volta)
            if first_time:
                with st.spinner("Analyzing response"):
                    content = str(requests.get(f"http://localhost:8000/api/CommentResponse/{query}?data={df}&id={st.session_state.logged}").text) #chiamata a chatgpt per data
                    
                    content = content.replace('\\n', ' ')
                    content = content.replace('\\t', ' ')
                    content = content.replace('\\r', ' ')
                    content = content.replace('\\', ' ')

                    st.session_state.messages.append({"role":"API", "query":query, "dataframe":data, "content": content})
        elif first_time:
            st.session_state.messages.append({"role":"API", "query":query, "dataframe":data, "content": content})
 
        #visualizzazione del messaggio e dei dati         
        st.write(content)

        if data[1] != []:
            st.table(df)
            st.download_button("Scarica i dati in formato CSV", df.to_csv(index=False), f"{query.replace(' ', '_')}.csv", "text/csv", use_container_width=True)

#a ogni refresh tutti i messaggi devono essere visualizzati nuovamente            
def message_reload(type):
    if type == "SQL":
        for message in st.session_state.messages:
            if message["role"] == "User":
                make_usr_message(message["content"])
            else:
                ApiMsg_SQL(message["query"], message["dataframe"], message["content"], first_time=False)
    else:
        for message in st.session_state.chat:
            if message["role"] == "User":
                make_usr_message(message["content"])
            else:
                ApiMsg_Docs(message["content"])

def response_to_dataframe(out_columns, data):
    try:

        #eliminazione di eventuali colonne duplicate che genererebbero un errore nella creazione del dataframe
        if out_columns != [] and data != []:
            unique_columns = []
            index = 0

            for element in out_columns:
                if element not in unique_columns:
                    unique_columns.append(element)
                else:
                    for row in data:
                        del row[index]
                index +=1

            return pd.DataFrame(data=data, columns=unique_columns)
        else:
            return pd.DataFrame()
        
    except Exception as exception:
        log_exception("Response to DataFrame ", exception)
