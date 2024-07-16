def init():
    global previous_msgs
    global SQL_SINTAX

    SQL_SINTAX = """
        columns match request tables defined SQL SERVER query retrieve rows data databases you.
        instructions create query:
        * If possible use AS keyword to rename columns with an italian word that better describes the data they contain.
        * isn't secified number rows retrive, TOP 50 avoid RateLimitError.
        * Insert query markdown sql code block ```sql ```.
        * query executed database, correct don't modify adding informations; query executed create query repeating code.
        * ESSENTIAL QUERY WORKS answer question, query direct answer, process complex; case add comment query expalining answer.
        * NOT ALLOWED UNION AND INTERSECT. Use JOIN absolutely correct way.
        * remember TOP cannot be used in the same query or sub-query as a OFFSET
        output T-SQL query compatible SQL SERVER 17s.
        If possible give me just the query, it's not necessary to make a message with the query.
    """
    previous_msgs = []
