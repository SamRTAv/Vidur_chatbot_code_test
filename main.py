

# import os
# import json
# import uvicorn
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from typing import List, Optional, Dict, Any
# from datetime import datetime
# import asyncio
# import os
# from nemoguardrails import LLMRails, RailsConfig

# # from langchain.memory import ConversationBufferMemory
# from perplexity import Perplexity
# from groq import Groq
# from input_to_llm import extract_chats, extract_goalfocus
# from utils import (
#     # load_user_data,
#     initialize_rag,
#     get_rag_response,
#     llm,
#     get_mongo_collection,
#     classify_input
# )

# from prompts import withrag_context_response

# os.environ["NVIDIA_API_KEY"] = "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"
# from configure import USER_DATA_PATH, llm_prompt

# app = FastAPI(title="Sattva AI API")

# class ChatRequest(BaseModel):
#     user_id: str
#     username: str
#     message: str
#     mode: str

# class ResourceItem(BaseModel):
#     title: str
#     url: str

# class ChatResponse(BaseModel):
#     response: str
#     topic: str
#     goal: str
#     flagged: str
#     resources: List[ResourceItem]


# PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
# client = Perplexity(api_key=PERPLEXITY_API_KEY)
# collection = get_mongo_collection()

# print("Initializing knowledge base...")
# qa_chains, retriever = initialize_rag() # Uncomment if you enable RAG later
# print("Knowledge base ready!")

# @app.get("/")
# def health_check():
#     return {"status": "active", "service": "Sattva AI"}


# @app.post("/cron_test")
# async def cron_test():
#     return "Hello Cron Tester"


# @app.post("/chat", response_model=ChatResponse)
# async def chat_endpoint(request: ChatRequest):
#     try:
#         username = request.username
#         userid = request.user_id
#         user_input = request.message
#         mode = request.mode
#         config = RailsConfig.from_path("./config")
#         rails = LLMRails(config)
#         input_check = await rails.generate_async(
#             messages=[{"role": "user", "content": user_input}],
#             options={
#                 "rails": ["input"],
#                 "log": {"level": "INFO"} 
#             }
#         )
#         response_text = str(input_check.response)
#         # print(response_text)

#         if "[[GUARDRAIL_BLOCK_TRIGGERED]]" in response_text:
#             print("[GUARD] Input Blocked!")
            
#             return ChatResponse(
#                     response="I am sorry but I cannot answer that request.",
#                     topic="blocked",
#                     goal="blocked",
#                     flagged ="unsafe and should be immediately alerted",
#                     resources=[]
#             )
        
#         # rag_response = get_rag_response(user_input,qa_chains)
#         # print(rag_response)
     
#         ncon = 3
#         chat_history_str = extract_chats(collection, userid, ncon) 
        
        
#         classification = classify_input(user_input)
#         if "conversational" in classification or "intrinsic" in classification:
#             context_response = withrag_context_response.format(username=username,user_input=user_input,rag_response="NULL",mode=mode,chat_history_str=chat_history_str,ncon=ncon)
#         else:
#             rag_response = get_rag_response(user_input,qa_chains,retriever)
#             print(rag_response)
#             context_response = withrag_context_response.format(username=username,user_input=user_input,rag_response=rag_response,mode=mode,chat_history_str=chat_history_str,ncon=ncon)
        
#         response = llm.invoke(context_response)
#         ai_response_text = response.content
#         input_check = await rails.generate_async(
#             messages=[{"role": "user", "content": ai_response_text}],
#             options={
#                 "rails": ["input"],
#                 "log": {"level": "INFO"} 
#             }
#         )
#         response_text = str(input_check.response)
#         if "[[GUARDRAIL_BLOCK_TRIGGERED]]" in response_text:
#             print("[GUARD] Input Blocked!")

#             return ChatResponse(
#                     response="I am sorry but I cannot answer that request.",
#                     topic="blocked",
#                     goal="blocked",
#                     flagged ="unsafe and should be immediately alerted",
#                     resources=[]
#             )

#         if collection is not None:
#             chat_document = {
#                 "user_id": userid,
#                 "username": username,
#                 "timestamp": datetime.now(),
#                 "conversation": {
#                     "human": user_input,
#                     "ai": ai_response_text
#                 },
#                 # "meta": {
#                 #     "Topic": parsed_json.get("Topic", "Unknown"), 
#                 #     "Goal": parsed_json.get("Goal", "Unknown")
#                 # }
#             }
            
#             try:
#                 collection.insert_one(chat_document)
#                 print("Saved to DB")
#             except Exception as e:
#                 print(f"Failed to save to DB: {e}")

#         search_query = f'''Suggest some stories,podacsts, videos, blogs 
#         This is your list of user history {chat_history_str} and based on his current question {user_input} and also the current response as generated by another LLM: {ai_response_text}. Now based on this you need to figure if even it is necessary to give any resources. 
#         If really necessary and find high quality, very good resources otherwise just output a very very good quote of the day in the format
#         "Quote of the day: <quote>" 
#         If you're suggesting videos then output should be something like=> Here are some useful resources for you:  
#         If you're giving a quote, output format should be => Here's a quote for you: <Quote>
#         '''

#         # print("before perplex")
#         # search = client.search.create(
#         #     query=search_query,
#         #     max_results=2
#         # )
#         # print("after perplex")

#         # resources_list = []
#         # for result in search.results:
#         #     resources_list.append(ResourceItem(title=result.title, url=result.url))

#         if "[[GUARDRAIL_FLAGGING]]" in response_text:
#             print("[GUARD] Input FLAGGED!")
#             return ChatResponse(
#                 response=ai_response_text,
#                 topic="Unknown",
#                 goal="Unknown",
#                 # topic=parsed_json.get("Topic", "Unknown"),
#                 # goal=parsed_json.get("Goal", "Unknown"),
#                 flagged="safe but should be alerted",
#                 resources=[]
#             )
        
#         elif "[[GUARDRAIL_NORMAL]]" in response_text:
#             print("[GUARD] Input NORMAL!")
#             return ChatResponse(
#                 response=ai_response_text,
#                 topic="Unknown",
#                 goal="Unknown",
#                 # topic=parsed_json.get("Topic", "Unknown"),
#                 # goal=parsed_json.get("Goal", "Unknown"),
#                 flagged="safe and normal text",
#                 resources=[]
#             )

#         else:
#             return ChatResponse(
#                 response=ai_response_text,
#                 topic="Unknown",
#                 goal="Unknown",
#                 # topic=parsed_json.get("Topic", "Unknown"),
#                 # goal=parsed_json.get("Goal", "Unknown"),
#                 flagged="fallback",
#                 resources=[]
#             )
            
#     except Exception as e:
#         print(f"Error processing request: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)





import os
import json
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import os
from nemoguardrails import LLMRails, RailsConfig
# from __future__ import annotations

import argparse
import json
import os
import sys
from typing import TYPE_CHECKING

from wellbeing.core_tools import load_user_data
from wellbeing.prompt     import SYSTEM_PROMPT
from wellbeing.registry   import TOOLS, dispatch_tool
from wellbeing.stats      import _compute_composite_score, _get_value
if TYPE_CHECKING:
    from groq import Groq  # type-only import; never executed at runtime

# from langchain.memory import ConversationBufferMemory
from perplexity import Perplexity
from groq import Groq
from input_to_llm import extract_chats, extract_dossier
from utils import (
    # load_user_data,
    initialize_rag,
    get_rag_response,
    llm,
    get_mongo_collection,
    classify_input
)

from prompts import withrag_context_response

os.environ["NVIDIA_API_KEY"] = "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"
from configure import USER_DATA_PATH, llm_prompt

app = FastAPI(title="Sattva AI API")

class ChatRequest(BaseModel):
    user_id: str
    username: str
    message: str
    mode: str

class ResourceItem(BaseModel):
    title: str
    url: str

class ChatResponse(BaseModel):
    response: str
    topic: str
    goal: str
    flagged: str
    resources: List[ResourceItem]


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)
collection = get_mongo_collection()

print("Initializing knowledge base...")
qa_chains, retriever = initialize_rag() # Uncomment if you enable RAG later
print("Knowledge base ready!")


def print_banner(user_data: dict):
    name   = user_data["personal_memory"]["name"]
    frames = user_data["wellbeing_frames"]
    weeks  = len(frames)
    latest = frames[-1] if frames else {}

    composite = _compute_composite_score(latest) if latest else None
    happy     = _get_value(latest, "emotions.happy_positive")   if latest else None
    anxious   = _get_value(latest, "emotions.anxious_worried")  if latest else None
    work      = _get_value(latest, "stresses.work_academic")    if latest else None

    print("\n" + "═" * 70)
    print("   🧠  Mental Health Counselor — Analytics-Enhanced (Groq)")
    print("═" * 70)
    print(f"   User: {name}, {user_data['personal_memory'].get('age', '?')}y")
    print(f"   Data: {weeks} weeks tracked")
    if composite is not None:
        print(f"   Wellbeing score (latest): {composite}/100")
    if happy is not None:
        print(f"   Happy/positive: {happy}/5    Anxious/worried: {anxious}/5    Work stress: {work}/5")
    print("═" * 70)
    print("   Available tools: 5 core + 12 analytics")
    print("   Tool calls shown with 🔧 (use --quiet to hide)")
    print("   Type 'quit' to exit.\n")



@app.get("/")
def health_check():
    return {"status": "active", "service": "Sattva AI"}


@app.post("/cron_test")
async def cron_test():
    return "Hello Cron Tester"


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        username = request.username
        userid = request.user_id
        user_input = request.message
        mode = request.mode
        config = RailsConfig.from_path("./config")
        rails = LLMRails(config)
        input_check = await rails.generate_async(
            messages=[{"role": "user", "content": user_input}],
            options={
                "rails": ["input"],
                "log": {"level": "INFO"} 
            }
        )
        response_text = str(input_check.response)
        # print(response_text)

        if "[[GUARDRAIL_BLOCK_TRIGGERED]]" in response_text:
            print("[GUARD] Input Blocked!")
            
            return ChatResponse(
                    response="I am sorry but I cannot answer that request.",
                    topic="blocked",
                    goal="blocked",
                    flagged ="unsafe and should be immediately alerted",
                    resources=[]
            )
        #Call Mongo Db and get the userwellbeing dossier - input = userwellbeingdossier
        user_data = extract_dossier(userid)
        # user_data = json.load(userwellbeingdossier)


     
        ncon = 3
        chat_history_str = extract_chats(collection, userid, ncon) 
        
        
        classification = classify_input(user_input)
        if "conversational" in classification or "intrinsic" in classification:
            llm_decision = "NULL"
        else:
            llm_decision = get_rag_response(user_input,qa_chains,retriever)
            if(llm_decision == None):
                llm_decision = "NULL"
            print(llm_decision)
            # context_response = withrag_context_response.format(username=username,user_input=user_input,rag_response=rag_response,mode=mode,chat_history_str=chat_history_str,ncon=ncon)
        

        messages = [{"role": "system", "content": SYSTEM_PROMPT.replace("{rag_response}", llm_decision)},
                    {"role": "user", "content": user_input}
                    ]

        while True:
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                max_tokens=1024,
            )
            choice = response.choices[0]
            msg    = choice.message

            msg_dict = {"role": "assistant", "content": msg.content or ""}
            if msg.tool_calls:
                msg_dict["tool_calls"] = [
                    {
                        "id":       tc.id,
                        "type":     "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in msg.tool_calls
                ]
            messages.append(msg_dict)

            if not msg.tool_calls:
                ai_response_text =  msg.content or ""
                break
            else:
                for tc in msg.tool_calls:
                    fn_name = tc.function.name
                    try:
                        fn_args = json.loads(tc.function.arguments or "{}")
                    except json.JSONDecodeError:
                        fn_args = {}
                    verbose = True
                    if verbose:
                        args_str = ", ".join(f"{k}={v!r}" for k, v in fn_args.items()) if fn_args else ""
                        print(f"  🔧 {fn_name}({args_str})")

                    result_str = dispatch_tool(fn_name, fn_args, user_data)
                    messages.append({
                        "role":          "tool",
                        "tool_call_id":  tc.id,
                        "content":       result_str,
                    })

        # ai_response_text = response.choices[0].message.content
        # response = llm.invoke(context_response)
        # ai_response_text = response.content
        input_check = await rails.generate_async(
            messages=[{"role": "user", "content": ai_response_text}],
            options={
                "rails": ["input"],
                "log": {"level": "INFO"} 
            }
        )
        response_text = str(input_check.response)
        if "[[GUARDRAIL_BLOCK_TRIGGERED]]" in response_text:
            print("[GUARD] Input Blocked!")

            return ChatResponse(
                    response="I am sorry but I cannot answer that request.",
                    topic="blocked",
                    goal="blocked",
                    flagged ="unsafe and should be immediately alerted",
                    resources=[]
            )

        if collection is not None:
            chat_document = {
                "user_id": userid,
                "username": username,
                "timestamp": datetime.now(),
                "conversation": {
                    "human": user_input,
                    "ai": ai_response_text
                },
                # "meta": {
                #     "Topic": parsed_json.get("Topic", "Unknown"), 
                #     "Goal": parsed_json.get("Goal", "Unknown")
                # }
            }
            
            try:
                collection.insert_one(chat_document)
                print("Saved to DB")
            except Exception as e:
                print(f"Failed to save to DB: {e}")



        if "[[GUARDRAIL_FLAGGING]]" in response_text:
            print("[GUARD] Input FLAGGED!")
            return ChatResponse(
                response=ai_response_text,
                topic="Unknown",
                goal="Unknown",
                # topic=parsed_json.get("Topic", "Unknown"),
                # goal=parsed_json.get("Goal", "Unknown"),
                flagged="safe but should be alerted",
                resources=[]
            )
        
        elif "[[GUARDRAIL_NORMAL]]" in response_text:
            print("[GUARD] Input NORMAL!")
            return ChatResponse(
                response=ai_response_text,
                topic="Unknown",
                goal="Unknown",
                # topic=parsed_json.get("Topic", "Unknown"),
                # goal=parsed_json.get("Goal", "Unknown"),
                flagged="safe and normal text",
                resources=[]
            )

        else:
            return ChatResponse(
                response=ai_response_text,
                topic="Unknown",
                goal="Unknown",
                # topic=parsed_json.get("Topic", "Unknown"),
                # goal=parsed_json.get("Goal", "Unknown"),
                flagged="fallback",
                resources=[]
            )
            
    except Exception as e:
        print(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


