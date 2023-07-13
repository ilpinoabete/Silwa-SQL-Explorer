from dotenv import load_dotenv
load_dotenv()
import os
import requests
import streamlit as st
from auth import user_login, user_logout
from helpers import make_api_msg, make_usr_message, message_reload

#default page settings
st.set_page_config(
    page_title="Silwa anc ChatGPT integration",
    page_icon="🤖",
    layout="centered",
    menu_items={
        'About': 'https://github.com/LinkShake/python_stesi.git',
    }
)

#main page
def index():
        if 'messages' not in st.session_state: 
            st.session_state.messages = []

        st.markdown("<h1 style='text-align: center;'>ChatGPT integration for silwa</h1>", unsafe_allow_html=True)

        message_reload()

        prompt = st.chat_input("Here goes your question")

        if prompt:
            make_usr_message(prompt)

            col1, center_col, col2 = st.columns(3)

            with center_col:
                with st.spinner("Getting response"):
                    #chiamata a chatgpt per risposta
                    response = str(requests.get(f"http://localhost:8000/api/SILWA/{prompt.replace(' ', '%20')}?id={st.session_state.logged}").text)

                    #aggiunta del messaggio alla history
                    st.session_state.messages.append({"role":"User", "content":prompt})

            #creazione del messaggio di risposta
            make_api_msg(prompt, response)

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


