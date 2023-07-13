import os
from dotenv import load_dotenv, set_key
from supabase import create_client
from gotrue.errors import AuthApiError

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
Client = create_client(url, key)

#credenziali di accesso id default
#email: str = "cristianotollot@gmail.com"
#password: str = "test1234"

def user_login(email, password):
    try:
        #login
        session = Client.auth.sign_in_with_password({ "email": email, "password": password })
        set_key(dotenv_path="./.env", key_to_set="ID", value_to_set=session.user.id)
        return session.user.id
    except AuthApiError:
        return False

def user_logout():
    try:
        Client.auth.sign_out()
        set_key(dotenv_path="./.env", key_to_set="ID", value_to_set="")
        return True

    except Exception:
        return False
