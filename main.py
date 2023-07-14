import os
import requests
import streamlit as st
from auth import user_login
from dotenv import load_dotenv
from helpers import make_usr_message, message_reload, ApiMsg_Docs, ApiMsg_SQL

load_dotenv()

#default page settings
st.set_page_config(
    page_title="Silwa anc ChatGPT integration",
    page_icon="🤖",
    layout="centered",
    menu_items={
        'About': 'https://github.com/LinkShake/python_stesi.git',
    }
)

def sidebar():
    global search_method

    with st.sidebar:
        search_method = st.selectbox("Seleziona metodo di ricerca", ["SQL", "Docs"])

        if search_method == "Docs":
                st.divider()

                st.session_state.useAllIndexes = st.checkbox("Usa tutti gli indici", value=False)

                if not st.session_state.useAllIndexes:

                    if len(st.session_state.indexes) == 0:
                        data = requests.get(f"http://localhost:4000/sql/{st.session_state.logged}").json()["data"]

                        for index in data:
                            st.session_state.indexes.append(index["IndexId"])
                            
                    st.session_state.index = st.selectbox("Seleziona indice", st.session_state.indexes)


        



#main page
def index():
        #inizializzazione della cronologia dei messaggi
        if 'messages' not in st.session_state: 
            st.session_state.messages = []

        if 'chat' not in st.session_state:
            st.session_state.chat = []
        
        if 'indexes' not in st.session_state:
            st.session_state.indexes = []
        
        if 'index' not in st.session_state:
            st.session_state.index = ""

        if 'useAllIndexes' not in st.session_state:
            st.session_state.useAllIndexes = False

        st.markdown("<h1 style='text-align: center;'>ChatGPT integration for silwa</h1>", unsafe_allow_html=True)
        
        sidebar()
        message_reload(search_method)

        prompt = st.chat_input("Here goes your question")

        if prompt and search_method == "SQL":
            make_usr_message(prompt)

            col1, center_col, col2 = st.columns(3)

            with center_col:
                with st.spinner("Getting response"):
                    #chiamata a chatgpt per risposta
                    response = str(requests.get(f"http://localhost:8000/api/SILWA/{prompt.replace(' ', '%20')}?id={st.session_state.logged}").text)

                    #aggiunta del messaggio alla history
                    st.session_state.messages.append({"role":"User", "content":prompt})

            #creazione del messaggio di risposta
            ApiMsg_SQL(prompt, response)

        if prompt and search_method == "Docs":
            make_usr_message(False)
            make_usr_message(prompt)

            col1, center_col, col2 = st.columns(3)

            with center_col:
                with st.spinner("Getting response"):
                    #chiamata a chatgpt per risposta

                    response =requests.post(f"http://localhost:5000/askChatGPT", 
                                            json={"query":prompt, "possibleIndexes": st.session_state.indexes, "index":st.session_state.index, "useAllIndexes":st.session_state.useAllIndexes}
                                            )

                    #aggiunta del messaggio alla history
                    st.session_state.chat.append({"role":"User", "content":prompt})

            #creazione del messaggio di risposta
            if response.status_code == 200:
                st.session_state.chat.append({"role":"API", "content":response.json()["data"]})
                ApiMsg_Docs(response.json()["data"])

            else:
                with st.chat_message('API', avatar="🤖"):
                    errMsg = "Si è verificato un errore nella richiesta"

                    st.session_state.chat.append({"role":"API", "content":errMsg})
                    st.write(errMsg)
        
#login page
def auth(login = True):

    if login:

        st.markdown("<h1 style='text-align: center;'>Please login to silwa api</h1>", unsafe_allow_html=True)
        st.divider()

        email = st.text_input(label = "Email")
        password = st.text_input(label="Password", type="password")

        if st.button(label="Login", use_container_width=True):
            if email and password:
                st.session_state.logged = (user_login(email, password))
            else:
                st.error("Email or password can't be void")

if "logged" not in st.session_state:
    id = os.getenv("ID")

    if id != "":
        st.session_state.logged = id
    else:
        st.session_state.logged = False

if st.session_state.logged:
    index()
else:
    auth()


