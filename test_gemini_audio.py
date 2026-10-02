import os
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

with open('test_audio.py', 'wb') as f:
    f.write(b'dummy')

response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=[
        types.Part.from_bytes(data=b'dummy', mime_type='audio/webm'),
        "Transcribe this exactly."
    ]
)
print("Syntax OK")
