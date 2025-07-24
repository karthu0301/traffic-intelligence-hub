import os
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def query_llm(question: str, metadata: dict = None):
    system_prompt = "You are a helpful AI assistant for debugging plate detection failures in a traffic analysis tool."
    
    if metadata:
        user_prompt = (
            f"A user asked: \"{question}\"\n"
            f"Here is the image metadata:\n{metadata}\n"
            f"Based on this, provide a possible explanation for detection issues or areas for improvement."
        )
    else:
        user_prompt = question

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.5,
        max_tokens=500
    )
    return response.choices[0].message['content']
