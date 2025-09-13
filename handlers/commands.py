import os
from dotenv import load_dotenv
from google import genai

load_dotenv() 

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI key not found")

client = genai.Client(api_key=api_key)

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash", contents="Explain how AI works in a few words"
)

print(response)