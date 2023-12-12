from dotenv import load_dotenv
import os
import openai

load_dotenv()

pinecone_api_key = os.getenv("PINECONE_API_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")
