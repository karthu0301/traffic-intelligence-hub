import os
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def query_llm(question: str, metadata: dict = None):
    system_prompt = (
        "You are an AI assistant that helps developers debug issues with a license plate "
        "detection and character recognition pipeline. Provide clear explanations and "
        "possible causes of errors based on metadata."
    )

    if metadata:
        detection_summary = f"Filename: {metadata.get('filename')}\n"
        if 'detections' in metadata and metadata['detections']:
            detection_summary += f"Detected plates: {len(metadata['detections'])}\n"
            for i, d in enumerate(metadata['detections']):
                detection_summary += f"- Plate {i+1}: {d.get('plate_string','N/A')} (conf: {d.get('plate_confidence','?')})\n"
        else:
            detection_summary += "No plates detected.\n"
    else:
        detection_summary = "No metadata provided."

    user_prompt = (
        f"Question: {question}\n\n"
        f"Metadata:\n{detection_summary}\n\n"
        f"Please explain what might be happening and suggest improvements."
    )

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.5,
        max_tokens=400
    )
    return response.choices[0].message['content']

