from google import genai
from google.genai import types

try:
    p = types.Part.from_text("Hello")
    print(p)
    c = types.Content(role="user", parts=[p])
    print(c)
except Exception as e:
    import traceback
    traceback.print_exc()

