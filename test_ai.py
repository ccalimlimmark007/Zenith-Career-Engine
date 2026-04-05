import os
from dotenv import load_dotenv
from google.genai import Client

load_dotenv()
client = Client(api_key=os.getenv("GEMINI_API_KEY"))

try:
    response = client.models.generate_content(
        model='gemini-2.5-flash-lite', 
        contents="System check: Are you online?"
    )
    print("AI Response:", response.text)
except Exception as e:
    print("Error:", e)