# Descrizione API:

Questo branch della repo è composto da due distinte api:

- askChatGPT: l'api che si occupava di generare una query per azure cognitive search, i cui dati venivano integrati nel prompt iniziale per la richiesta ad openai. Il suo sviluppo è stato abbandonato in favore della creazione dell'api silwa più veloce e affidabile.
-  silwa: l'api che si occupa di generare una query per SQL con la quale vengono ottenuti i dati da aggiungere al prompt della richiesta a openai

Entrambe le API sono state sviluppate in python attraverso la libreria [fastapi](https://fastapi.tiangolo.com/) mentre il front end è stato realizzato grazie alla libreria [streamlit](https://docs.streamlit.io/)

# Cosa contiene il .env

* DRIVER_NAME={ODBC Driver 18 for SQL Server}
* SERVER_NAME (nome del server SQL in cui fare le query)
* DB_NAME (nome del database SQL)
* UID (SQL username)
* PASS (SQL password)

* USERS = [
{"Name":username1, "Id":Identificativo_univoco1},
{"Name":username2, "Id":Identificativo_univoco2}
]

  (Per ora la gestione degli utenti non è automatizzata per cui per crearne di nuovi è necessario modificare direttamente il .env)
  
* OPENAI_KEY (openai api key)

# Vantaggi e svantaggi delle API:

## askChatGPT (depracated)
* Vantaggi: 
    * Riesce a selezionare i dati più intelligentemente, grazie all'utilizzo di cognitive search
    * Non è limitata solo alle tabelle relazionali di SQL ma le informazioni posso essere ricercate anche in blob come documenti PDF.
    * Si può selezionare quale modello utilizzare per elaborare le informazioni e si possono cambiare la temperatura e il numero di massimo token utilizzati nella risposta
* Svantaggi:
    * Il tempo di attesa per una risposta è lungo
    * Non possono essere messi in relazione dati provenienti da indici distinti
    * Le query devono essere specifiche affinché la query per cognitive search fornisca i dati corretti
    * Se vengono effettuate query che necessitano di una grande quantità di dati la richiesta ad openai potrebbe non andare a buon fine perché viene superato il numero massimo di token per richiesta

## silwa
* Vantaggi: 
    * Il tempo di attesa per la risposta è breve
    * Le query possono essere meno specifiche
    * Si possono fare query che utilizzano dati provenienti da più tabelle
* Svantaggi:
    * Se vengono effettuate query che necessitano di una grande quantità di dati il tempo di attesa per la risposta si potrebbe dilatare notevolmente.
    * Dopo ogni query viene restituita l'intera riga che contiene i dati richiesti

# Esempi di query con l'api silwa

## Prompt:

Dammi le informazioni sull'oggetto con id 432

## Response: 

| nome_articolo                         | codice_articolo | id_articolo | data_consegna            | frequenza |
| ------------------------------------- | --------------- | ----------- | ------------------------ | --------- |
| SACCHETTI KRAFT BIANCO 22X50 CF500    | .B7903564100    | 432         | 2022-09-16T10:28:36.277Z | C         |

## Prompt:

Che oggetti sono presenti nell'UDC 40?

## Response:

| nome_articolo                    | codice_articolo | id_articolo | data_consegna            | frequenza | id_udc | giacenza_articolo | codice_udc | creazione_udc            |
| -------------------------------- | --------------- | ----------- | ------------------------ | --------- | ------ | ----------------- | ---------- | ------------------------ |
| PANNELLO FIANCO UT25 L1600       | L0943030        | 91259       | 2022-09-30T09:31:48.353Z | C         | 40     | 24.0000           | 40         | 2022-10-17T13:36:51.367Z |

## Prompt:

Qual'è la giacenza dell'elemento nell'UDC 40?
## Response:

| giacenza_articolo |
| ----------------- |
|      24.0000      |

## Prompt:

Qual'è la posizione dell'elemento con id 432?

## Response:

| id_ubicazione | nome_ubicazione |     x     |     y     |   z   | scaffale | colonna | livello |
| ------------- | --------------- | --------- | --------- | ----- | -------- | ------- | ------- |
|     432       |  MF-001.16.01   |   17353   |   47469   |  934  |  MF001   |   16    |   01    |

## Prompt:

Quali sono gli archi dell'elemento 503?

## Response:

| edge_id | id_articolo1 | id_articolo2 | edge_length |
|---------|--------------|--------------|-------------|
| 189     | 502          | 503          | 1076        |
| 190     | 503          | 504          | 5621        |

## Prompt:

Quali sono i 10 UDC più vecchi?

## Response:

| id_udc | codice_udc | creazione_udc            |
|--------|------------|--------------------------|
| 40     | 220000040  | 2022-10-17T13:36:51.367Z |
| 45     | 220000045  | 2022-10-17T13:38:02Z     |
| 41     | 220000041  | 2022-10-17T13:38:02.203Z |
| 42     | 220000042  | 2022-10-17T13:38:02.210Z |
| 43     | 220000043  | 2022-10-17T13:38:02.220Z |
| 44     | 220000044  | 2022-10-17T13:38:02.227Z |
| 46     | 220000046  | 2022-10-17T14:24:12.623Z |
| 47     | 220000047  | 2022-10-17T14:24:12.633Z |
| 49     | 220000049  | 2022-10-17T14:24:12.650Z |
| 50     | 220000050  | 2022-10-17T14:24:12.657Z |


Nel caso di quest'ultima request la query che è stata utilizzata per ottenere i dati da SQL è:
```
SELECT TOP 10 * FROM Info_UDC ORDER BY Creazione_UDC ASC
```
Ed è stata ottenuta fornendo a GPT3 la seguente richiesta:
```
SQL tables and their properties:

position_info_table: 
       COLUMN_NAME COLUMN_DEFAULT DATA_TYPE
0    Id_Ubicazione           None       int
1  Nome_Ubicazione           None  nvarchar
2                X           None       int
3                Y           None       int
4                Z           None       int
5         Scaffale           None  nvarchar
6          Colonna           None  nvarchar
7          Livello           None  nvarchar

edges_table: 
    COLUMN_NAME COLUMN_DEFAULT DATA_TYPE
0       Edge_Id           None       int
1  Id_Articolo1           None       int
2  Id_Articolo2           None       int
3   Edge_Length           None       int

items_info: 
       COLUMN_NAME COLUMN_DEFAULT DATA_TYPE
0    Nome_Articolo           None  nvarchar
1  Codice_Articolo           None  nvarchar
2      Id_Articolo           None       int
3    Data_Consegna           None  datetime
4        Frequenza           None  nvarchar
5    Id_Ubicazione           None       int

Info_UDC: 
     COLUMN_NAME COLUMN_DEFAULT DATA_TYPE
0         Id_UDC           None       int
1     Codice_UDC           None  nvarchar
2  Creazione_UDC           None  datetime

Items_UDC: 
         COLUMN_NAME COLUMN_DEFAULT DATA_TYPE
0             Id_UDC           None       int
1        Id_Articolo           None       int
2  Giacenza_Articolo           None   decimal

Given the following prompt:
Quali sono i 10 UDC più vecchi
Find the columns that match the request in the tables defined before, and make a SQL query to retrieve the row that contain such data.
Note that 'frequenza' is a char that indicate the frequency with the items are requied and can assume the values 'A', 'B' or 'C' so it cannot be converted to int.
The query MUST start and end with <tag> and CAN'T contain the function 'LIMIT' use 'TOP' or other one instead. Please don't use <tag> anywhere else in your response. It's also important that between the <tag> tags and the response there isn't any characters or space
```
&nbsp;
La query è formata da tre parti:
* Informazioni sulle tabelle e sui loro datatype
* La richiesta di creazione di una query SQL che risponda al prompt
* Le regole sulla sintassi che devono essere rispettate affinché il parsing avvenga correttamente
Le informazioni sulle tabelle vengono ottenute direttamente dal database SQL attraverso la funzione:
&nbsp;
```python
def get_datatype(table_name):
    #connessione con il database SQL
    load_dotenv()
    connection = create_conn()
    cursor = connection.cursor()

    #esecuzione della query
    cursor.execute(f"""SELECT COLUMN_NAME, ORDINAL_POSITION, COLUMN_DEFAULT, DATA_TYPE
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = '{table_name}';
    """)

    #creazione di un dataframe con i dati appena ottenuti
    types = cursor.fetchall()
    columns = ['COLUMN_NAME', 'ORDINAL_POSITION', 'COLUMN_DEFAULT', 'DATA_TYPE']

    return pd.DataFrame(types, columns=columns)
```
La scelta di restituire un dataframe ha evitato di dover dare manualmente all'IA le informazioni sulle informazioni che sono state fornite con la query.
&nbsp;
Viene poi fatto il parsing della query attraverso la funzione `parse_response()` in cui vengono tagliate le parti non comprese tra i tag e vengono rimossi caratteri '\', '\n', '\r' e '\t' che potrebbero causare errori nella richiesta al database.
I dati ottenuti da SQL vengono poi convertiti in un dataframe per poi essere visualizzati come tabelle nel frontend
