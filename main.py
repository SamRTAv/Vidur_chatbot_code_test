

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

# from langchain.memory import ConversationBufferMemory
from perplexity import Perplexity
from groq import Groq
from input_to_llm import extract_chats, extract_goalfocus
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


PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
client = Perplexity(api_key=PERPLEXITY_API_KEY)
collection = get_mongo_collection()

print("Initializing knowledge base...")
qa_chains, retriever = initialize_rag() # Uncomment if you enable RAG later
print("Knowledge base ready!")

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
        
        # rag_response = get_rag_response(user_input,qa_chains)
        # print(rag_response)
     
        ncon = 3
        chat_history_str = extract_chats(collection, userid, ncon) 
        
        # prev_goalandfocus = extract_goalfocus(collection, userid)

    #     context_goal = f'''
    #    Ohk, so you are an expert in navigating paths through human conversations. So, let's say if someone is telling you about how they are feeling, what they did
    #     what other people did to them, what are their problems, what are their goals and aspirations in life and all that stuff.
    #     Now based on all the above information, you need to figure that as a teacher/Guru (which you are for the person) 
    #     what should be the topic (or the broad thing that is going on currently as a part of discussion - it could discussion about office, or marriage or house problems or anything) you've to figure this out from based on previous converstaion history.
    #     At the same time, you have to ask/suggest/recommend further to the person as well right. So for that you have to define a goal (that is basically what should be the exact next step in this conversation - should you be asking a quuestion or should be recommending something or maybe just chatting normally). again this also you've to decide. But goal has to be something which defines the next step
    #     whereas topic is something which is broad and overall defines what is going on in the converstaion.
    #     Your response format should be like this:
    #     "Topic":" <topic> ",
    #     "Goal":" <goal> "

    #     Don't output anything else other than this format.
    #     Here is the conversation history of past {ncon} conversations: {chat_history_str}
    #     also, here;s the current user question: {user_input}
    #     You can also look upon what was the topic and goal defined just previously to get better idea.
    #     previous topic and goal : {prev_goalandfocus}
    #     Try updating goal on each instance but topic can remain same if the converstaion is still revolving around the same thing. Because obviusly you've to dig deeper with the user, you can't be doing the same thign in the goal
    #     ALso, if the user isn't talking anymore about the previous topic, you can change the topic as well. Thats why i am providin gyou the previous focus and goal
    #     '''

    #     goal_response = llm.invoke(context_goal)
        
    
        # try:
    
        #     clean_content = goal_response.content.replace("```json", "").replace("```", "").strip()
        #     if not clean_content.startswith("{"):
        #         json_string_to_parse = "{" + clean_content + "}"
        #     else:
        #         json_string_to_parse = clean_content
                
        #     parsed_json = json.loads(json_string_to_parse)
        # except json.JSONDecodeError:
        #     parsed_json = {"Topic": "General", "Goal": "Continue conversation"}


        # goalandfocus = parsed_json
        
        classification = classify_input(user_input)
        if "conversational" in classification or "intrinsic" in classification:
            context_response = withrag_context_response.format(username=username,user_input=user_input,rag_response="NULL",mode=mode,chat_history_str=chat_history_str,ncon=ncon)
        else:
            rag_response = get_rag_response(user_input,qa_chains,retriever)
            print(rag_response)
            context_response = withrag_context_response.format(username=username,user_input=user_input,rag_response=rag_response,mode=mode,chat_history_str=chat_history_str,ncon=ncon)
        
        response = llm.invoke(context_response)
        ai_response_text = response.content
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

        search_query = f'''Suggest some stories,podacsts, videos, blogs 
        This is your list of user history {chat_history_str} and based on his current question {user_input} and also the current response as generated by another LLM: {ai_response_text}. Now based on this you need to figure if even it is necessary to give any resources. 
        If really necessary and find high quality, very good resources otherwise just output a very very good quote of the day in the format
        "Quote of the day: <quote>" 
        If you're suggesting videos then output should be something like=> Here are some useful resources for you:  
        If you're giving a quote, output format should be => Here's a quote for you: <Quote>
        '''

        # print("before perplex")
        # search = client.search.create(
        #     query=search_query,
        #     max_results=2
        # )
        # print("after perplex")

        # resources_list = []
        # for result in search.results:
        #     resources_list.append(ResourceItem(title=result.title, url=result.url))

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




