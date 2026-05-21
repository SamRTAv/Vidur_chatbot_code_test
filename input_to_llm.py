import json
import os
from pymongo import MongoClient
# file_name = 'chat_history.jsonl'
# collection = ""



def extract_dossier(user_id):
    CONNECTION_STRING = os.getenv("CONNECTION_STRING")
    DB_NAME = os.getenv("DB_NAME")
    COLLECTION_NAME = "userwellbeingdossiers"
    try:
        # Connect with certifi to avoid SSL errors
        client = MongoClient(CONNECTION_STRING)
        db = client[DB_NAME]
        collection =  db[COLLECTION_NAME]
    except Exception as e:
        print(f"Error connecting to Mongo: {e}")
        return None
    
    if collection is None:
        return "collection not found"
    
    cursor = collection.find({"user_id": user_id}).sort("updated_at", -1).limit(1)

    last_doc = list(cursor)
    if not last_doc:
        return "dossier not found"

    return last_doc[0]


def extract_chats(collection,user_id,limit):
    
    if collection is None:
        return "No database connection."
    
    cursor = collection.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)

    recent_chats = list(cursor)[::-1]

    if not recent_chats:
        return "No previous conversation history."


    formatted_history = ""
    for doc in recent_chats:
        human_msg = doc['conversation']['human']
        ai_msg = doc['conversation']['ai']
        formatted_history += f"Human: {human_msg}\nAI: {ai_msg}\n\n"

    return formatted_history

    # with open(file_name, 'r') as f:
    #     all_data_string = f.read()

    # all_conversations = []
    # decoder = json.JSONDecoder()
    # position = 0


    # while position < len(all_data_string.strip()):
    #     # Skip any whitespace
    #     all_data_string = all_data_string[position:].lstrip()
    #     if not all_data_string:
    #         break # Reached end of file

    #     # Decode one object and find where it ends
    #     try:
    #         obj, position = decoder.raw_decode(all_data_string)
    #         all_conversations.append(obj)
    #     except json.JSONDecodeError:
    #         # Handle case where file might end with bad data
    #         break 


    # last_three_convos = all_conversations[-3:]
    # return last_three_convos

def extract_goalfocus(collection,user_id):
 
    # if collection is None:
    #     return {"topic": "General Life", "goal": "Understand the user"}

    # Find the single most recent document
    last_doc = collection.find_one(
        {"user_id": user_id},
        sort=[("timestamp", -1)]
    )

    if last_doc and "meta" in last_doc:
        return last_doc["meta"]
    
    # Default if no history exists yet
    return {"topic": "General Life", "goal": "Understand the user"}


    #    # Read the entire file into one string
    # with open(file_name, 'r') as f:
    #     all_data_string = f.read()

    # all_conversations = []
    # decoder = json.JSONDecoder()
    # position = 0

    # # We must use a loop because the file contains
    # # multiple JSON objects back-to-back.
    # while position < len(all_data_string.strip()):
    #     # Skip any whitespace
    #     all_data_string = all_data_string[position:].lstrip()
    #     if not all_data_string:
    #         break # Reached end of file

    #     # Decode one object and find where it ends
    #     try:
    #         obj, position = decoder.raw_decode(all_data_string)
    #         all_conversations.append(obj)
    #     except json.JSONDecodeError:
    #         # Handle case where file might end with bad data
    #         break 

    # # --- Now we can get the last three ---

    # # Get the last three conversations
    # last_three_convos = all_conversations[-1:]
    # return last_three_convos








