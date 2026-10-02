from google import genai
from google.genai import types
import json

def test():
    try:
        # Load settings
        with open("/Users/divyanshu/.jarvis_system/settings.json") as f:
            settings = json.load(f)
        api_key = settings.get('api_keys', {}).get('gemini')
        if not api_key: return "No API key"

        client = genai.Client(api_key=api_key)
        
        hist = [{'role': 'user', 'parts': [{'text': 'Hello'}]}]
        api_contents = list(hist)
        
        # mock image part
        img_part = types.Part.from_bytes(data=b'fake image bytes', mime_type='image/png')
        api_contents[-1] = {'role': 'user', 'parts': ['Hello', img_part]}
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=api_contents
        )
        print("Success:", response.text)
    except Exception as e:
        import traceback
        traceback.print_exc()

test()
