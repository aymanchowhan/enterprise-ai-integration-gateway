import os
from dotenv import load_dotenv
from google import genai

load_dotenv()  # reads your .env file

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="Say hello in one short sentence."
)

print(response.text)