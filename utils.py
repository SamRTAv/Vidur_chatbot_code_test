
# # utils.py
# import os
# import json
# from langchain_groq import ChatGroq
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# # from langchain.schema import Document
# # from langchain.chains import RetrievalQA
# # from langchain_huggingface import HuggingFaceEmbeddings
# # from langchain_community.vectorstores import Chroma
# # from langchain.prompts import PromptTemplate

# from langchain_core.documents import Document
# from langchain_chroma import Chroma
# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_core.prompts import PromptTemplate
# # from langchain.chains import RetrievalQA
# from langchain_classic.chains import create_retrieval_chain
# from langchain_classic.chains.combine_documents import create_stuff_documents_chain
# from configure import USER_DATA_PATH, RAG_BASE_DIRECTORY, RAG_CATEGORIES
# import shutil
# from dotenv import load_dotenv
# from pymongo import MongoClient
# import certifi
# import re

# load_dotenv()


# def get_mongo_collection():
#     CONNECTION_STRING = os.getenv("CONNECTION_STRING")
#     DB_NAME = os.getenv("DB_NAME")
#     COLLECTION_NAME = os.getenv("COLLECTION_NAME")
#     try:
#         # Connect with certifi to avoid SSL errors
#         client = MongoClient(CONNECTION_STRING, tlsCAFile=certifi.where())
#         db = client[DB_NAME]
#         return db[COLLECTION_NAME]
#     except Exception as e:
#         print(f"Error connecting to Mongo: {e}")
#         return None
    

# def LLMChunking():
#     pass




# # LLM setup
# llm = ChatGroq(
#     api_key="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",
#     model="llama-3.3-70b-versatile",
#     temperature=0,
#     max_tokens=4000
# )

# # Text splitter
# text_splitter = RecursiveCharacterTextSplitter(
#     separators=["\n\n", "\n", ".", " ", ""],
#     chunk_size=500,
#     chunk_overlap=100,
#     length_function=len
# )
# # text_splitter = LLMChunking()

# # Embeddings
# embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
# # embeddings = None

# # Load user data
# def load_user_data():
#     try:
#         if os.path.exists(USER_DATA_PATH) and os.path.getsize(USER_DATA_PATH) > 0:
#             with open(USER_DATA_PATH, 'r') as f:
#                 return json.load(f)
#     except Exception:
#         pass
#     return {"users": {}, "user_info": {}}

# # Save user data
# def save_user_data(data):
#     with open(USER_DATA_PATH, 'w') as f:
#         json.dump(data, f, indent=2)

# # Initialize RAG with per-category vector stores and QA chains
# def initialize_rag():
#     """
#     Initialize RAG vector stores and chains using modern LangChain (LCEL).
#     Args:
#         llm: The initialized ChatGroq (or other) LLM object.
#         embeddings: The initialized HuggingFaceEmbeddings object.
#         text_splitter: The initialized RecursiveCharacterTextSplitter object.
#     """
#     vector_stores = {}
#     qa_chains = {}
    
#     # 1. Define Prompt Template (Modern LCEL Format)
#     # Note: Modern chains typically look for "context" and "input" variables.
#     base_prompt_template = """You are a {category} wellness expert. Provide helpful advice with specific actions:

# 1. Start with a brief empathetic response to the user's concern
# 2. Offer 1-3 actionable suggestions with brief explanations
# 3. End with an open-ended question to continue conversation

# Guidelines:
# - Keep responses conversational and supportive
# - Avoid clinical jargon
# - Focus on practical, implementable advice
# - Maintain hopeful and encouraging tone

# Context:
# {context}

# Question: {input}
# """
    
#     for category in RAG_CATEGORIES:
#         persist_dir = f"./chroma_db_{category}"
#         vector_store = None 

#         # --- 2. Check/Load Existing Vector Store ---
#         if os.path.exists(persist_dir):
#             print(f"Found existing vector store for {category}. Attempting to load...")
#             try:
#                 vector_store = Chroma(
#                     persist_directory=persist_dir,
#                     embedding_function=embeddings  # UPDATED: 'embedding_function', not 'embedding'
#                 )
#                 vector_stores[category] = vector_store
#             except Exception as e:
#                 print(f"Error loading existing store {persist_dir}: {e}")
#                 print("Will delete and attempt to re-build.")
#                 shutil.rmtree(persist_dir)
        
#         # --- 3. Create Vector Store if needed ---
#         if vector_store is None: 
#             print(f"No valid vector store for {category} found. Creating new one...")
            
#             dir_path = os.path.join(RAG_BASE_DIRECTORY, category)
#             docs = []
            
#             if os.path.exists(dir_path):
#                 for filename in os.listdir(dir_path):
#                     if filename.endswith('.txt'):
#                         file_path = os.path.join(dir_path, filename)
#                         try:
#                             with open(file_path, 'r', encoding='utf-8') as f:
#                                 text = f.read()
                            
#                             chunks = text_splitter.split_text(text)
#                             for chunk in chunks:
#                                 if chunk.strip():
#                                     metadata = {
#                                         "source": filename,
#                                         "category": category
#                                     }
#                                     docs.append(Document(
#                                         page_content=chunk.strip(),
#                                         metadata=metadata
#                                     ))
#                         except Exception as e:
#                             print(f"Error processing {file_path}: {e}")
            
#             if docs:
#                 # UPDATED: Use 'embedding_function' instead of 'embedding'
#                 # UPDATED: Removed .persist() call (Auto-persists in new version)
#                 vector_store = Chroma.from_documents(
#                     documents=docs,
#                     embedding=embeddings, 
#                     persist_directory=persist_dir
#                 )
#                 vector_stores[category] = vector_store
#                 print(f"Created new vector store for {category} with {len(docs)} documents.")
#             else:
#                 print(f"No documents found for {category}. Skipping QA chain setup.")
#                 continue 

#         # --- 4. Create QA Chain (LCEL Style) ---
#         if vector_store:
#             # A. Create the Prompt
#             # We inject the specific category into the template string immediately
#             category_specific_template = base_prompt_template.replace("{category}", category)
            
#             prompt = PromptTemplate(
#                 template=category_specific_template,
#                 input_variables=["context", "input"] # LCEL standard variables
#             )

#             # B. Create the Document Chain (LLM + Prompt)
#             question_answer_chain = create_stuff_documents_chain(llm, prompt)

#             # C. Create the Retrieval Chain (Retriever + Document Chain)
#             retriever = vector_store.as_retriever(search_kwargs={"k": 5})
#             rag_chain = create_retrieval_chain(retriever, question_answer_chain)

#             qa_chains[category] = rag_chain
#             print(f"Initialized {category} QA chain.")

#     return qa_chains



# # Classify question to category
# def classify_question_category(question):
#     prompt = f"""
#     Classify this question into one category: {', '.join(RAG_CATEGORIES)}
#     Question: {question}
#     Respond with only the category name.
#     """
#     response = llm.invoke(prompt)
#     # print(response)
#     return response.content.strip()

# # Get RAG response using category-specific QA chain
# def get_rag_response(question, qa_chains):
#     # Classify question
#     category = classify_question_category(question)
    
#     if category not in qa_chains:
#         # Fallback to first available chain
#         category = list(qa_chains.keys())[0]
    
#     # Get response
#     result = qa_chains[category].invoke({"input": question})
#     return result['answer']


# # Classify user input
# def classify_input(user_input):
#     prompt = f"""
#     Classify the following user input into one of these categories:
#     1. "question" - If the user is asking a factual question that could be answered with knowledge
#     2. "general" - If the user is just chatting or expressing feelings

#     User Input: {user_input}

#     Respond with only one word: either "question" or "general"
#     """
#     response = llm.invoke(prompt)
#     return response.content.strip().lower()



# def parse_weird_json(text_data):
#     fixed_json_string = re.sub(r'\]\s*\[', ', ', text_data.strip())
    
#     # Step B: Load it as standard JSON
#     try:
#         data_list = json.loads(fixed_json_string)
#         return data_list
#     except json.JSONDecodeError as e:
#         print(f"❌ JSON Parsing Error: {e}")
#         return []








# # utils.py
# import os
# import json
# from langchain_groq import ChatGroq
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# # from langchain.schema import Document
# # from langchain.chains import RetrievalQA
# # from langchain_huggingface import HuggingFaceEmbeddings
# # from langchain_community.vectorstores import Chroma
# # from langchain.prompts import PromptTemplate

# from langchain_core.documents import Document
# from langchain_chroma import Chroma
# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_core.prompts import PromptTemplate
# # from langchain.chains import RetrievalQA
# from langchain_classic.chains import create_retrieval_chain
# from langchain_classic.chains.combine_documents import create_stuff_documents_chain
# from configure import USER_DATA_PATH, RAG_BASE_DIRECTORY, RAG_CATEGORIES
# import shutil
# from dotenv import load_dotenv
# from pymongo import MongoClient
# import certifi
# import re

# load_dotenv()


# def get_mongo_collection():
#     CONNECTION_STRING = os.getenv("CONNECTION_STRING")
#     DB_NAME = os.getenv("DB_NAME")
#     COLLECTION_NAME = os.getenv("COLLECTION_NAME")
#     try:
#         # Connect with certifi to avoid SSL errors
#         client = MongoClient(CONNECTION_STRING, tlsCAFile=certifi.where())
#         db = client[DB_NAME]
#         return db[COLLECTION_NAME]
#     except Exception as e:
#         print(f"Error connecting to Mongo: {e}")
#         return None
    

# def LLMChunking():
#     pass




# # LLM setup
# llm = ChatGroq(
#     api_key=GROQ_API_KEY,
#     model="openai/gpt-oss-120b",
#     temperature=0.7,
#     max_tokens=500,
#     model_kwargs={
#         "top_p": 0.9,
#         "presence_penalty": 0.5,
#         "frequency_penalty": 0.4
#     }
# )


# # Text splitter
# text_splitter = RecursiveCharacterTextSplitter(
#     separators=["\n\n", "\n", ".", " ", ""],
#     chunk_size=500,
#     chunk_overlap=100,
#     length_function=len
# )
# # text_splitter = LLMChunking()

# # Embeddings
# embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
# # embeddings = None

# # Load user data
# def load_user_data():
#     try:
#         if os.path.exists(USER_DATA_PATH) and os.path.getsize(USER_DATA_PATH) > 0:
#             with open(USER_DATA_PATH, 'r') as f:
#                 return json.load(f)
#     except Exception:
#         pass
#     return {"users": {}, "user_info": {}}

# # Save user data
# def save_user_data(data):
#     with open(USER_DATA_PATH, 'w') as f:
#         json.dump(data, f, indent=2)

# # Initialize RAG with per-category vector stores and QA chains
# def initialize_rag():
#     """
#     Initialize RAG vector stores and chains using modern LangChain (LCEL).
#     Args:
#         llm: The initialized ChatGroq (or other) LLM object.
#         embeddings: The initialized HuggingFaceEmbeddings object.
#         text_splitter: The initialized RecursiveCharacterTextSplitter object.
#     """
#     vector_stores = {}
#     qa_chains = {}
#     retrievers = {}
    
#     # 1. Define Prompt Template (Modern LCEL Format)
#     # Note: Modern chains typically look for "context" and "input" variables.
#     base_prompt_template = """You are a {category} wellness expert. Provide helpful advice with specific actions:

# 1. Start with a brief empathetic response to the user's concern
# 2. Offer 1-3 actionable suggestions with brief explanations
# 3. End with an open-ended question to continue conversation

# Guidelines:
# - Keep responses conversational and supportive
# - Avoid clinical jargon
# - Focus on practical, implementable advice
# - Maintain hopeful and encouraging tone

# Context:
# {context}

# Question: {input}
# """
    
#     for category in RAG_CATEGORIES:
#         persist_dir = f"./chroma_db_{category}"
#         vector_store = None 

#         # --- 2. Check/Load Existing Vector Store ---
#         if os.path.exists(persist_dir):
#             print(f"Found existing vector store for {category}. Attempting to load...")
#             try:
#                 vector_store = Chroma(
#                     persist_directory=persist_dir,
#                     embedding_function=embeddings  # UPDATED: 'embedding_function', not 'embedding'
#                 )
#                 vector_stores[category] = vector_store
#             except Exception as e:
#                 print(f"Error loading existing store {persist_dir}: {e}")
#                 print("Will delete and attempt to re-build.")
#                 shutil.rmtree(persist_dir)
        
#         # --- 3. Create Vector Store if needed ---
#         if vector_store is None: 
#             print(f"No valid vector store for {category} found. Creating new one...")
            
#             dir_path = os.path.join(RAG_BASE_DIRECTORY, category)
#             docs = []
            
#             if os.path.exists(dir_path):
#                 for filename in os.listdir(dir_path):
#                     if filename.endswith('.txt'):
#                         file_path = os.path.join(dir_path, filename)
#                         try:
#                             with open(file_path, 'r', encoding='utf-8') as f:
#                                 text = f.read()
                            
#                             chunks = text_splitter.split_text(text)
#                             for chunk in chunks:
#                                 if chunk.strip():
#                                     metadata = {
#                                         "source": filename,
#                                         "category": category
#                                     }
#                                     docs.append(Document(
#                                         page_content=chunk.strip(),
#                                         metadata=metadata
#                                     ))
#                         except Exception as e:
#                             print(f"Error processing {file_path}: {e}")
            
#             if docs:
#                 # UPDATED: Use 'embedding_function' instead of 'embedding'
#                 # UPDATED: Removed .persist() call (Auto-persists in new version)
#                 vector_store = Chroma.from_documents(
#                     documents=docs,
#                     embedding=embeddings, 
#                     persist_directory=persist_dir
#                 )
#                 vector_stores[category] = vector_store
#                 print(f"Created new vector store for {category} with {len(docs)} documents.")
#             else:
#                 print(f"No documents found for {category}. Skipping QA chain setup.")
#                 continue 

#         # --- 4. Create QA Chain (LCEL Style) ---
#         if vector_store:
#             # A. Create the Prompt
#             # We inject the specific category into the template string immediately
#             category_specific_template = base_prompt_template.replace("{category}", category)
            
#             prompt = PromptTemplate(
#                 template=category_specific_template,
#                 input_variables=["context", "input"] # LCEL standard variables
#             )

#             # B. Create the Document Chain (LLM + Prompt)
#             question_answer_chain = create_stuff_documents_chain(llm, prompt)

#             # C. Create the Retrieval Chain (Retriever + Document Chain)
#             retriever = vector_store.as_retriever(search_kwargs={"k": 5})
#             rag_chain = create_retrieval_chain(retriever, question_answer_chain)

#             qa_chains[category] = rag_chain
#             retrievers[category] = retriever
#             print(f"Initialized {category} QA chain.")

#     return qa_chains, retrievers



# # Classify question to category
# def classify_question_category(question):
#     prompt = f"""
#     Classify this question into one category: {', '.join(RAG_CATEGORIES)}
#     Question: {question}
#     Respond with only the category name.
#     """
#     response = llm.invoke(prompt)
#     print(response)
#     return response.content.strip()

# # Get RAG response using category-specific QA chain
# # def get_rag_response(question, qa_chains):
# #     # Classify question
# #     category = classify_question_category(question)
    
# #     if category not in qa_chains:
# #         # Fallback to first available chain
# #         category = list(qa_chains.keys())[0]
    
# #     # Get response
# #     # result = qa_chains[category].invoke({"input": question})
# #     retriever = qa_chains[category].retriever
# #     docs = retriever.invoke(question)

# #     # return result['answer']
# #     return [doc.page_content for doc in docs]



# def get_rag_response(question, retrievers_dict):
#     category = classify_question_category(question)
    
#     if category not in retrievers_dict:
#         category = list(retrievers_dict.keys())[0]
    
#     docs = retrievers_dict[category].invoke(question)
    
#     return "\n\n".join([doc.page_content for doc in docs])

# # Classify user input
# def classify_input(user_input):
#     prompt = f"""
#     Classify the following user input into one of these categories:
#     1. "question" - If the user is asking a factual question that could be answered with knowledge
#     2. "general" - If the user is just chatting or expressing feelings

#     User Input: {user_input}

#     Respond with only one word: either "question" or "general"
#     """
#     response = llm.invoke(prompt)
#     return response.content.strip().lower()



# def parse_weird_json(text_data):
#     fixed_json_string = re.sub(r'\]\s*\[', ', ', text_data.strip())
    
#     # Step B: Load it as standard JSON
#     try:
#         data_list = json.loads(fixed_json_string)
#         return data_list
#     except json.JSONDecodeError as e:
#         print(f"❌ JSON Parsing Error: {e}")
#         return []












# # utils.py
# import os
# import json
# from langchain_groq import ChatGroq
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# # from langchain.schema import Document
# # from langchain.chains import RetrievalQA
# # from langchain_huggingface import HuggingFaceEmbeddings
# # from langchain_community.vectorstores import Chroma
# # from langchain.prompts import PromptTemplate

# from langchain_core.documents import Document
# from langchain_chroma import Chroma
# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_core.prompts import PromptTemplate
# # from langchain.chains import RetrievalQA
# from langchain_classic.chains import create_retrieval_chain
# from langchain_classic.chains.combine_documents import create_stuff_documents_chain
# from configure import USER_DATA_PATH, RAG_BASE_DIRECTORY, RAG_CATEGORIES
# import shutil
# from dotenv import load_dotenv
# from pymongo import MongoClient
# import certifi
# import re

# load_dotenv()


# def get_mongo_collection():
#     CONNECTION_STRING = os.getenv("CONNECTION_STRING")
#     DB_NAME = os.getenv("DB_NAME")
#     COLLECTION_NAME = os.getenv("COLLECTION_NAME")
#     try:
#         # Connect with certifi to avoid SSL errors
#         client = MongoClient(CONNECTION_STRING, tlsCAFile=certifi.where())
#         db = client[DB_NAME]
#         return db[COLLECTION_NAME]
#     except Exception as e:
#         print(f"Error connecting to Mongo: {e}")
#         return None
    

# def LLMChunking():
#     p




# # LLM setup
# llm = ChatGroq(
#     api_key=GROQ_API_KEY,
#     model="llama-3.3-70b-versatile",
#     temperature=0,
#     max_tokens=4000
# )

# # Text splitter
# text_splitter = RecursiveCharacterTextSplitter(
#     separators=["\n\n", "\n", ".", " ", ""],
#     chunk_size=500,
#     chunk_overlap=100,
#     length_function=len
# )
# # text_splitter = LLMChunking()

# # Embeddings
# embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
# # embeddings = None

# # Load user data
# def load_user_data():
#     try:
#         if os.path.exists(USER_DATA_PATH) and os.path.getsize(USER_DATA_PATH) > 0:
#             with open(USER_DATA_PATH, 'r') as f:
#                 return json.load(f)
#     except Exception:
#         pass
#     return {"users": {}, "user_info": {}}

# # Save user data
# def save_user_data(data):
#     with open(USER_DATA_PATH, 'w') as f:
#         json.dump(data, f, indent=2)

# # Initialize RAG with per-category vector stores and QA chains
# def initialize_rag():
#     """
#     Initialize RAG vector stores and chains using modern LangChain (LCEL).
#     Args:
#         llm: The initialized ChatGroq (or other) LLM object.
#         embeddings: The initialized HuggingFaceEmbeddings object.
#         text_splitter: The initialized RecursiveCharacterTextSplitter object.
#     """
#     vector_stores = {}
#     qa_chains = {}
    
#     # 1. Define Prompt Template (Modern LCEL Format)
#     # Note: Modern chains typically look for "context" and "input" variables.
#     base_prompt_template = """You are a {category} wellness expert. Provide helpful advice with specific actions:

# 1. Start with a brief empathetic response to the user's concern
# 2. Offer 1-3 actionable suggestions with brief explanations
# 3. End with an open-ended question to continue conversation

# Guidelines:
# - Keep responses conversational and supportive
# - Avoid clinical jargon
# - Focus on practical, implementable advice
# - Maintain hopeful and encouraging tone

# Context:
# {context}

# Question: {input}
# """
    
#     for category in RAG_CATEGORIES:
#         persist_dir = f"./chroma_db_{category}"
#         vector_store = None 

#         # --- 2. Check/Load Existing Vector Store ---
#         if os.path.exists(persist_dir):
#             print(f"Found existing vector store for {category}. Attempting to load...")
#             try:
#                 vector_store = Chroma(
#                     persist_directory=persist_dir,
#                     embedding_function=embeddings  # UPDATED: 'embedding_function', not 'embedding'
#                 )
#                 vector_stores[category] = vector_store
#             except Exception as e:
#                 print(f"Error loading existing store {persist_dir}: {e}")
#                 print("Will delete and attempt to re-build.")
#                 shutil.rmtree(persist_dir)
        
#         # --- 3. Create Vector Store if needed ---
#         if vector_store is None: 
#             print(f"No valid vector store for {category} found. Creating new one...")
            
#             dir_path = os.path.join(RAG_BASE_DIRECTORY, category)
#             docs = []
            
#             if os.path.exists(dir_path):
#                 for filename in os.listdir(dir_path):
#                     if filename.endswith('.txt'):
#                         file_path = os.path.join(dir_path, filename)
#                         try:
#                             with open(file_path, 'r', encoding='utf-8') as f:
#                                 text = f.read()
                            
#                             chunks = text_splitter.split_text(text)
#                             for chunk in chunks:
#                                 if chunk.strip():
#                                     metadata = {
#                                         "source": filename,
#                                         "category": category
#                                     }
#                                     docs.append(Document(
#                                         page_content=chunk.strip(),
#                                         metadata=metadata
#                                     ))
#                         except Exception as e:
#                             print(f"Error processing {file_path}: {e}")
            
#             if docs:
#                 # UPDATED: Use 'embedding_function' instead of 'embedding'
#                 # UPDATED: Removed .persist() call (Auto-persists in new version)
#                 vector_store = Chroma.from_documents(
#                     documents=docs,
#                     embedding=embeddings, 
#                     persist_directory=persist_dir
#                 )
#                 vector_stores[category] = vector_store
#                 print(f"Created new vector store for {category} with {len(docs)} documents.")
#             else:
#                 print(f"No documents found for {category}. Skipping QA chain setup.")
#                 continue 

#         # --- 4. Create QA Chain (LCEL Style) ---
#         if vector_store:
#             # A. Create the Prompt
#             # We inject the specific category into the template string immediately
#             category_specific_template = base_prompt_template.replace("{category}", category)
            
#             prompt = PromptTemplate(
#                 template=category_specific_template,
#                 input_variables=["context", "input"] # LCEL standard variables
#             )

#             # B. Create the Document Chain (LLM + Prompt)
#             question_answer_chain = create_stuff_documents_chain(llm, prompt)

#             # C. Create the Retrieval Chain (Retriever + Document Chain)
#             retriever = vector_store.as_retriever(search_kwargs={"k": 5})
#             rag_chain = create_retrieval_chain(retriever, question_answer_chain)

#             qa_chains[category] = rag_chain
#             print(f"Initialized {category} QA chain.")

#     return qa_chains



# # Classify question to category
# def classify_question_category(question):
#     prompt = f"""
#     Classify this question into one category: {', '.join(RAG_CATEGORIES)}
#     Question: {question}
#     Respond with only the category name.
#     """
#     response = llm.invoke(prompt)
#     print(response)
#     return response.content.strip()

# # Get RAG response using category-specific QA chain
# def get_rag_response(question, qa_chains):
#     # Classify question
#     category = classify_question_category(question)
    
#     if category not in qa_chains:
#         # Fallback to first available chain
#         category = list(qa_chains.keys())[0]
    
#     # Get response
#     result = qa_chains[category].invoke({"input": question})
#     return result['answer']


# # Classify user input
# def classify_input(user_input):
#     prompt = f"""
#     Classify the following user input into one of these categories:
#     1. "question" - If the user is asking a factual question that could be answered with knowledge
#     2. "general" - If the user is just chatting or expressing feelings

#     User Input: {user_input}

#     Respond with only one word: either "question" or "general"
#     """
#     response = llm.invoke(prompt)
#     return response.content.strip().lower()



# def parse_weird_json(text_data):
#     fixed_json_string = re.sub(r'\]\s*\[', ', ', text_data.strip())
    
#     # Step B: Load it as standard JSON
#     try:
#         data_list = json.loads(fixed_json_string)
#         return data_list
#     except json.JSONDecodeError as e:
#         print(f"❌ JSON Parsing Error: {e}")
#         return []







# utils.py
import os
import json
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain.schema import Document
# from langchain.chains import RetrievalQA
# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_community.vectorstores import Chroma
# from langchain.prompts import PromptTemplate

from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
# from langchain.chains import RetrievalQA
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_experimental.text_splitter import SemanticChunker
from configure import USER_DATA_PATH, RAG_BASE_DIRECTORY, RAG_CATEGORIES
import shutil
from dotenv import load_dotenv
from pymongo import MongoClient
import certifi
import re

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def get_mongo_collection():
    CONNECTION_STRING = os.getenv("CONNECTION_STRING")
    DB_NAME = os.getenv("DB_NAME")
    COLLECTION_NAME = os.getenv("COLLECTION_NAME")
    try:
        # Connect with certifi to avoid SSL errors
        client = MongoClient(CONNECTION_STRING, tlsCAFile=certifi.where())
        db = client[DB_NAME]
        return db[COLLECTION_NAME]
    except Exception as e:
        print(f"Error connecting to Mongo: {e}")
        return None
    

def LLMChunking():
    pass




# LLM setup
llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="openai/gpt-oss-120b",
    temperature=0.7,
    max_tokens=500,
    model_kwargs={
        "top_p": 0.9,
        "presence_penalty": 0.5,
        "frequency_penalty": 0.4
    }
)


llm2 = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.1-8b-instant",
    temperature=0.7,
    max_tokens=500,
    model_kwargs={
        "top_p": 0.9,
        "presence_penalty": 0.5,
        "frequency_penalty": 0.4
    }
)


# Text splitter
# text_splitter = RecursiveCharacterTextSplitter(
#     separators=["\n\n", "\n", ".", " ", ""],
#     chunk_size=500,
#     chunk_overlap=100,
#     length_function=len
# )
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
text_splitter = SemanticChunker(
    embeddings, 
    breakpoint_threshold_type="percentile" # Or "standard_deviation"
)
# text_splitter = LLMChunking()

# Embeddings
# embeddings = None

# Load user data
def load_user_data():
    try:
        if os.path.exists(USER_DATA_PATH) and os.path.getsize(USER_DATA_PATH) > 0:
            with open(USER_DATA_PATH, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {"users": {}, "user_info": {}}

# Save user data
def save_user_data(data):
    with open(USER_DATA_PATH, 'w') as f:
        json.dump(data, f, indent=2)

# Initialize RAG with per-category vector stores and QA chains
def initialize_rag():
    """
    Initialize RAG vector stores and chains using modern LangChain (LCEL).
    Args:
        llm: The initialized ChatGroq (or other) LLM object.
        embeddings: The initialized HuggingFaceEmbeddings object.
        text_splitter: The initialized RecursiveCharacterTextSplitter object.
    """
    vector_stores = {}
    qa_chains = {}
    retrievers = {}
    
    # 1. Define Prompt Template (Modern LCEL Format)
    # Note: Modern chains typically look for "context" and "input" variables.
    base_prompt_template = """You are a {category} wellness expert. You are being used as a key extractor from a set of documents that are being returned from rag (cosine similarity).
    Now based on the user input question, and the context (that is basically returned from the rag search), you need to further extract all those statements that properly answer the user query
    There's a much bigger LLM in the architecture after you that'll provide the final answer to the user.
    So your reponse must be such that when given to the bigger LLM, it can easily incorporate the response into the final answer ans the asnwer looks to the point, crisp but at the same time detailed enough.
        Context:
        {context}
        Input Question: {input}
"""
    
    for category in RAG_CATEGORIES:
        persist_dir = f"./chroma_db_{category}"
        vector_store = None 

        # --- 2. Check/Load Existing Vector Store ---
        if os.path.exists(persist_dir):
            print(f"Found existing vector store for {category}. Attempting to load...")
            try:
                vector_store = Chroma(
                    persist_directory=persist_dir,
                    embedding_function=embeddings  # UPDATED: 'embedding_function', not 'embedding'
                )
                vector_stores[category] = vector_store
            except Exception as e:
                print(f"Error loading existing store {persist_dir}: {e}")
                print("Will delete and attempt to re-build.")
                shutil.rmtree(persist_dir)
        
        # --- 3. Create Vector Store if needed ---
        if vector_store is None: 
            print(f"No valid vector store for {category} found. Creating new one...")
            
            dir_path = os.path.join(RAG_BASE_DIRECTORY, category)
            docs = []
            
            if os.path.exists(dir_path):
                for filename in os.listdir(dir_path):
                    if filename.endswith('.txt'):
                        file_path = os.path.join(dir_path, filename)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                text = f.read()
                            
                            chunks = text_splitter.split_text(text)
                            for chunk in chunks:
                                if chunk.strip():
                                    metadata = {
                                        "source": filename,
                                        "category": category
                                    }
                                    docs.append(Document(
                                        page_content=chunk.strip(),
                                        metadata=metadata
                                    ))
                        except Exception as e:
                            print(f"Error processing {file_path}: {e}")
            
            if docs:
                # UPDATED: Use 'embedding_function' instead of 'embedding'
                # UPDATED: Removed .persist() call (Auto-persists in new version)
                vector_store = Chroma.from_documents(
                    documents=docs,
                    embedding=embeddings, 
                    persist_directory=persist_dir
                )
                vector_stores[category] = vector_store
                print(f"Created new vector store for {category} with {len(docs)} documents.")
            else:
                print(f"No documents found for {category}. Skipping QA chain setup.")
                continue 

        # --- 4. Create QA Chain (LCEL Style) ---
        if vector_store:
            # A. Create the Prompt
            # We inject the specific category into the template string immediately
            category_specific_template = base_prompt_template.replace("{category}", category)
            
            prompt = PromptTemplate(
                template=category_specific_template,
                input_variables=["context", "input"] # LCEL standard variables
            )

            # B. Create the Document Chain (LLM + Prompt)
            question_answer_chain = create_stuff_documents_chain(llm, prompt)

            # C. Create the Retrieval Chain (Retriever + Document Chain)
            retriever = vector_store.as_retriever(search_type="similarity_score_threshold",search_kwargs={"score_threshold":0.6,"k": 5})
            rag_chain = create_retrieval_chain(retriever, question_answer_chain)

            qa_chains[category] = rag_chain
            retrievers[category] = retriever
            print(f"Initialized {category} QA chain.")

    return qa_chains, retrievers



# Classify question to category
def classify_question_category(question):
    prompt = f"""
    Classify this question into one category: {', '.join(RAG_CATEGORIES)}
    Question: {question}
    Respond with only the category name.
    """
    response = llm.invoke(prompt)
    print(response)
    return response.content.strip()

# # Get RAG response using category-specific QA chain
# def get_rag_response(question, qa_chains,retrievers_dict):
#     # Classify question
#     # category = classify_question_category(question)
#     RAG_CATEGORIES = ["Ayurveda", "Lifestyle", "psychology", "Yoga", "Mental_health"]
#     result = {}
#     for category in RAG_CATEGORIES:
#         docs = retrievers_dict[category].invoke(question)
#         result[category] = [doc.page_content for doc in docs]
    
#         # result[category] = qa_chains[category].invoke({"input": question})
#     # if category not in qa_chains:
#     #     # Fallback to first available chain
#     #     category = list(qa_chains.keys())[0]
#     # Get response
#     return result['answer']




def get_rag_response(question, qa_chains, retrievers_dict):
    RAG_CATEGORIES = ["Ayurveda", "Lifestyle", "psychology", "Yoga", "Mental_health"]
    
    all_retrieved_data = []
    for category in RAG_CATEGORIES:
        # Access the vector store directly from the retriever object
        vector_store = retrievers_dict[category].vectorstore
        docs_with_scores = vector_store.similarity_search_with_score(question, k=3)
        for doc, score in docs_with_scores:
            all_retrieved_data.append({
                "category": category,
                "score": score,
                "text": doc.page_content
            })

    # Note: ChromaDB returns Distance, not Similarity. Lower distance = better match.
    all_retrieved_data.sort(key=lambda x: x["score"], reverse=False)

    # Keep only the top 5 most relevant chunks globally to avoid overwhelming the LLM
    top_global_docs = all_retrieved_data[:5]

    combined_context = ""
    for item in top_global_docs:
        combined_context += f"--- Source: {item['category']} (Distance: {item['score']:.4f}) ---\n{item['text']}\n\n"

    final_answer = llm.invoke(
    f"""You are a wellness expert. You are being used as a key extractor from a set of documents that are being returned from rag (cosine similarity).
        Now based on the user input question, and the context (that is basically returned from the rag search), you need to further extract all those statements that properly answer the user query
        There's a much bigger LLM in the architecture after you that'll provide the final answer to the user.
        So your reponse must be such that when given to the bigger LLM, it can easily incorporate the response into the final answer and the answer looks to the point, crisp but at the same time detailed enough.
        You've extract, summarise and condense it well.
        Context:{combined_context}
        Input Question: {question}
    """
)
    return final_answer.content



# def get_rag_response(question, retrievers_dict):
#     category = classify_question_category(question)
    
#     if category not in retrievers_dict:
#         category = list(retrievers_dict.keys())[0]
    
#     docs = retrievers_dict[category].invoke(question)
    
#     return "\n\n".join([doc.page_content for doc in docs])

# Classify user input
def classify_input(user_input):
    prompt = f"""
You are a highly intelligent Query Routing AI for a wellness and health application. 
Your only job is to analyze the user's input and classify it into EXACTLY ONE of the following 8 categories.

### CATEGORY DEFINITIONS
1. Conversational: Simple greetings, pleasantries, follow-up acknowledgments, or clarifications.
2. Intrinsic: General knowledge questions or text-processing tasks (summarization, translation) that the LLM can answer using its base training without needing external documents.
3. External: Queries requiring factual medical, psychological, Ayurvedic, or lifestyle knowledge that must be retrieved from our external document database.
4. Personal: Queries explicitly asking about the user's past conversations, uploaded data, logs, or personal history.
5. Hybrid: Queries that require BOTH fetching the user's personal data AND fetching external wellness documents to form a complete answer.
6. Analytical: Deeply complex queries that require fetching personal data, fetching external documents, AND performing heavy cross-referencing, trend analysis, or complex reasoning.

### EXAMPLES
User: "Hi, good morning!"
Category: Conversational

User: "That makes sense, thank you."
Category: Conversational

User: "What is the capital of France?"
Category: Intrinsic

User: "Can you fix the grammar in this paragraph I just pasted?"
Category: Intrinsic

User: "What are the benefits of Ashwagandha according to Ayurveda?"
Category: External

User: "What are the best yoga poses for lower back pain?"
Category: External

User: "What did I say my sleep score was last Tuesday?"
Category: Personal

User: "Summarize my journal entries from last week."
Category: Personal
User: "Based on the diet plan I uploaded yesterday, what Ayurvedic herbs should I add to my meals?"
Category: Hybrid
User: "Looking at my mood tracker history for the last month and cross-referencing it with psychological research on seasonal affective disorder, what holistic lifestyle changes should I prioritize?"
Category: Analytical

### INSTRUCTIONS
Analyze the user's input below. 
Respond with ONLY ONE WORD: the exact name of the category. Do not add any punctuation, explanations, or formatting.

User Input: {user_input}
Category:
"""
    response = llm2.invoke(prompt)
    return response.content.strip().lower()



def parse_weird_json(text_data):
    fixed_json_string = re.sub(r'\]\s*\[', ', ', text_data.strip())
    
    # Step B: Load it as standard JSON
    try:
        data_list = json.loads(fixed_json_string)
        return data_list
    except json.JSONDecodeError as e:
        print(f"❌ JSON Parsing Error: {e}")
        return []




