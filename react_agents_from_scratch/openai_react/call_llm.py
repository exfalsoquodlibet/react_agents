import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

def get_llm_response(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an AI assistant for the UK Government helping users navigate official government guidance and services."},
            {"role": "user", "content": prompt}
        ],
        n=1,
        stop=None,
        temperature=0.5
    )
    return response.choices[0].message.content.strip()
