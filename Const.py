from __future__ import absolute_import
from helpers import get_datatype

#tables used in the query generation

SQL_TYPES = f"""
items_info: \n{get_datatype('items_info')}\n
Info_UDC: \n{get_datatype('Info_UDC')}\n
Ubicazioni: \n{get_datatype('Ubicazioni')}\n
Items_UDC: \n{get_datatype('Items_UDC')}
"""

#the request for the openai request

SQL_REQUEST = f"SQL tables and their properties:\n{SQL_TYPES}\nGiven the following prompt:\n"
SQL_SINTAX = "\nFind the columns that match the request in the tables defined before, and make a SQL query to retrieve the row that contain such data.\nNote that 'frequenza' is a char that indicate the frequency with the items are requied and can assume the values 'A', 'B' or 'C' so it cannot be converted to int.\nThe query MUST start and end with <tag> and CAN'T contain the function 'LIMIT' use 'TOP' or other one instead. Please don't use <tag> anywhere else in your response. It's also important that between the <tag> tags and the response there isn't any characters or space"
