# Introduction

Il progetto in questione va ad integrare l’api di ChatGPT con Cognitive Search e i database SQL dei magazzini, per poter realizzare una chatbot in cui l’utente è in grado di porre all’AI delle domande riguardanti gli oggetti presenti nei database in questione. In questo modo l’utente è in grado di ricevere una risposta, ricca e dettagliata, in linguaggio naturale, senza che esso debba avere i privilegi necessari per eseguire una query e conoscere la struttura dei database.

# Descrizione API:

Questo branch della repo è composto da due distinte api:

- askChatGPT: l'api che si occupa di generare una query per azure cognitive search, i cui dati vengono integrati nel prompt iniziale per la richiesta ad openai
- silwa: l'api che si occupa di generare una query per SQL con la quale vengono ottenuti i dati da aggiungere al prompt della richiesta a openai

Attualmente askChatGPT non è disponibile.

Entrambe le API sono state sviluppate in python attraverso la libreria [fastapi](https://fastapi.tiangolo.com/)

# Getting Started

## Le librerie utilizzate sono:

- [fastapi](https://fastapi.tiangolo.com/) (usata per creare le api utili per comunicare con il frontend)
- [pandas](https://pandas.pydata.org/) (per generare i DataFrame utili ad effettuare le query a ChatGPT)
- [openai](https://github.com/openai/openai-python) (necessaria per comunicare con i server di OpenAI)
- [python-dotenv](https://pypi.org/project/python-dotenv/) (usata per leggere le variabili d'ambiente)
- [pypyodbc](https://github.com/pypyodbc/pypyodbc) (utile per la connessione ai server SQL)
- [socketio](https://socket.io/) (per lo streaming dei dati al frontend)

Possono essere installate attraverso `pip` eseguendo il comando:  
`pip install -r requirements.txt`

## Variabili d'ambiente

Per funzionare correttamente il backend necessita delle credenziali di accesso al database SQL, di una lista di host approvati per le chiamate API, della porta che verrà usata dal socket per streammare i chunk delle eventuali risposte stream delle API di OpenAi e della key di accesso a queste ultime; queste variabili devono essere aggiunte nel file `.env` il cui contenuto deve essere:

```python
DRIVER_NAME="{SQL Server Native Client 11.0}"
SERVER_NAME = ""    #nome del server contenente il database con le informazioni degli utenti
DB_NAME = ""        #nome del database con le informazioni degli utenti
UID = ""            #username con cui effettuare l'accesso
PASS = ""           #password con cui effettuare l'accesso


#Allowed hosts for the frontend to connect to the backend
ALLOWED_HOSTS = []


OPENAI_API_KEY = ""     #API key di openai
```

## Come eseguire il backend:

È sufficiente lanciare il comando `uvicorn main:app --host 0.0.0.0 --port 8000` all'interno della cartella del backend

## Logging

È possibile trovare i log di esecuzione dell'app nel file app.log, si può inoltre modificare il livello di logging modificando l'attributo `level` della funzione `logging.basicConfig` nel main.py
