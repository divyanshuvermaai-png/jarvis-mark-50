from google import genai
from google.genai import types
import json

def test():
    try:
        with open("/Users/divyanshu/.jarvis_system/settings.json") as f:
            settings = json.load(f)
        api_key = settings.get('api_keys', {}).get('gemini')
        if not api_key: return "No API key"

        client = genai.Client(api_key=api_key)
        
        hist = [{'role': 'user', 'parts': [{'text': 'Hello'}]}]
        
        api_contents = []
        for msg in hist:
            parts = []
            for p in msg['parts']:
                if 'text' in p:
                    parts.append(p['text'])
            api_contents.append(types.Content(role=msg['role'], parts=parts))
        
        # Add image to last msg
        img_part = types.Part.from_bytes(data=b'fake', mime_type='image/png')
        api_contents[-1].parts.append(img_part)
        
        print("Types ok?", api_contents)
    except Exception as e:
        import traceback
        traceback.print_exc()

test()
