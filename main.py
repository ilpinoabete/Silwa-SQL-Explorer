from dotenv import load_dotenv
load_dotenv()
import os
import requests
import streamlit as st
from auth import user_login, user_logout
from helpers import make_usr_message, message_reload, ApiMsg_Docs, ApiMsg_SQL

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

#main page
def index():
        #inizializzazione della cronologia dei messaggi
        if 'messages' not in st.session_state: 
            st.session_state.messages = []

        if 'chat' not in st.session_state:
            st.session_state.chat = []

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
                    indexes = []
                    index = ""
                    useAllIndexes = False

                    response =requests.post(f"http://192.168.1.46:5000/askChatGPT", 
                                            data={"query":prompt, "possibleIndexes": indexes, "index":index, "useAllIndexes":useAllIndexes}
                                            )

                    #aggiunta del messaggio alla history
                    st.session_state.chat.append({"role":"User", "content":prompt})

            #creazione del messaggio di risposta
            if response.status_code == 200:
                st.session_state.chat.append({"role":"API", "content":response.json()["data"]})
                ApiMsg_Docs(prompt, response.json()["data"])

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
    print(f"ID: {id}")

    if id != "":
        st.session_state.logged = id
    else:
        st.session_state.logged = False

if st.session_state.logged:
    index()
else:
    auth()


