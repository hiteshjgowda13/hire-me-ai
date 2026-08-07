import os 
from dotenv import load_dotenv
from groq import Groq


load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    raise ValueError("API key missing ")

client = Groq()

model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")