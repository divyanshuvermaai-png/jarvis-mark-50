import os
import sys

# ── 0. Virtual Environment Self-Bootstrap ──
# If executed with system python (e.g. `python3 main.py`), transparently re-exec
# inside the local .venv to guarantee all Apple MLX, PyObjC, and dependencies load cleanly.
_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
_VENV_PYTHON = os.path.join(_PROJECT_DIR, ".venv", "bin", "python")
if not getattr(sys, 'frozen', False) and os.path.exists(_VENV_PYTHON) and os.path.realpath(sys.executable) != os.path.realpath(_VENV_PYTHON):
    try:
        os.execv(_VENV_PYTHON, [_VENV_PYTHON] + sys.argv)
    except Exception:
        pass

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import subprocess, psutil, urllib.parse, re, json, time, pathlib, asyncio

# Security Kernel & Defense in Depth
from security import (
    security_kernel,
    TrustLevel,
    resolve_trust_level,
    kill_switch,
    SecurityState,
    inspect_input,
    normalize_input,
    FirewallVerdict,
    assemble_context,
    build_external_data_block,
    audit_chain
)

# Bulletproof static folder resolution
possible_paths = [
    os.path.abspath(os.path.dirname(__file__)),
    os.getcwd()
]
if getattr(sys, 'frozen', False):
    possible_paths.insert(0, os.path.dirname(sys.executable))
    if hasattr(sys, '_MEIPASS'):
        possible_paths.append(sys._MEIPASS)

frontend_folder = '.'
for p in possible_paths:
    if os.path.exists(os.path.join(p, 'index.html')):
        frontend_folder = p
        break

import mimetypes
mimetypes.add_type('application/wasm', '.wasm')
mimetypes.add_type('application/octet-stream', '.data')
mimetypes.add_type('application/octet-stream', '.tflite')
mimetypes.add_type('application/octet-stream', '.binarypb')

app = Flask(__name__, static_folder=frontend_folder, static_url_path='')
CORS(app)

@app.route('/')
def serve_index():
    return app.send_static_file('index.html')

@app.route('/vendor/<path:filename>')
def serve_vendor(filename):
    vendor_dir = os.path.join(frontend_folder, 'vendor')
    return send_from_directory(vendor_dir, filename)

# ── Persistent Storage Paths ──
CONFIG_DIR = os.path.expanduser('~/.jarvis_system')
os.makedirs(CONFIG_DIR, exist_ok=True)
SETTINGS_FILE = os.path.join(CONFIG_DIR, 'settings.json')
HISTORY_FILE = os.path.join(CONFIG_DIR, 'history.json')
SOUL_FILE = os.path.join(CONFIG_DIR, 'soul.md')
MEMORY_FILE = os.path.join(CONFIG_DIR, 'memory.md')
DEFAULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'defaults')

# ── Global State ──
ai_client = None
ai_config = {}

def load_settings():
    default_settings = {
        'provider': 'gemini', 
        'model': 'gemini-3.5-flash', 
        'api_keys': {
            'gemini': '',
            'openrouter': '',
            'groq': '',
            'nvidia': ''
        },
        'temperature': 0.7,
        'max_tokens': 1024,
        'system_prompt': "You are J.A.R.V.I.S. — Just A Rather Very Intelligent System — an ultra-advanced AI assistant built for your creator and boss, Divyanshu Verma, Founder & CEO of Divyanshu Industries. You are sophisticated, witty, and supremely capable. You address Divyanshu Verma as 'Sir' and maintain a tone of calm authority. Keep responses focused and useful."
    }
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f: 
            import json
            s = json.load(f)
            if 'api_key' in s and 'api_keys' not in s:
                s['api_keys'] = {
                    'gemini': s['api_key'],
                    'openrouter': s['api_key'],
                    'groq': '',
                    'nvidia': ''
                }
            for k, v in default_settings.items():
                if k not in s: s[k] = v
            return s
    return default_settings

def save_settings(data):
    with open(SETTINGS_FILE, 'w') as f: json.dump(data, f)
    init_ai()

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f: return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, 'w') as f: json.dump(history, f)

def load_soul():
    """Load personality from soul.md, create from defaults if missing."""
    if not os.path.exists(SOUL_FILE):
        default_soul = os.path.join(DEFAULTS_DIR, 'soul.md')
        if os.path.exists(default_soul):
            import shutil
            shutil.copy2(default_soul, SOUL_FILE)
        else:
            with open(SOUL_FILE, 'w') as f:
                f.write("You are J.A.R.V.I.S. — an ultra-advanced AI assistant. Sophisticated, witty, and supremely capable.")
    with open(SOUL_FILE, 'r') as f:
        return f.read().strip()

def save_soul(content):
    with open(SOUL_FILE, 'w') as f:
        f.write(content)

def load_memory():
    """Load persistent memory from memory.md, create from defaults if missing."""
    if not os.path.exists(MEMORY_FILE):
        default_mem = os.path.join(DEFAULTS_DIR, 'memory.md')
        if os.path.exists(default_mem):
            import shutil
            shutil.copy2(default_mem, MEMORY_FILE)
        else:
            with open(MEMORY_FILE, 'w') as f:
                f.write("- [System] J.A.R.V.I.S. Memory System Initialized.\\n")
    with open(MEMORY_FILE, 'r') as f:
        return f.read().strip()

def append_memory(entry):
    """Append a new memory entry."""
    with open(MEMORY_FILE, 'a') as f:
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        f.write(f"\\n- [{timestamp}] {entry}")

def save_memory(content):
    """Overwrite entire memory file."""
    with open(MEMORY_FILE, 'w') as f:
        f.write(content)

def init_ai():
    global ai_client, ai_config
    settings = load_settings()
    provider = settings.get('provider', 'gemini')
    api_keys = settings.get('api_keys', {})
    api_key = api_keys.get(provider, '').strip()
    model = settings.get('model', 'gemini-3.5-flash')
    
    if provider not in ('gemma', 'qwen', 'local', 'mlx') and not api_key:
        ai_client = None
        print("  ⚠️  No API key configured for cloud provider.")
        return

    try:
        if provider in ('gemma', 'qwen', 'local', 'mlx'):
            import gemma_local
            ai_client = "gemma"
            model = 'gemma-4-e2b-it-4bit'
        elif provider == 'gemini':
            from google import genai
            ai_client = genai.Client(api_key=api_key)
        elif provider == 'mlx':
            ai_client = "mlx"
        else:
            from openai import OpenAI
            base_url = None
            if provider == 'openrouter': base_url = 'https://openrouter.ai/api/v1'
            elif provider == 'groq': base_url = 'https://api.groq.com/openai/v1'
            elif provider == 'nvidia': base_url = 'https://integrate.api.nvidia.com/v1'
            
            if base_url:
                ai_client = OpenAI(api_key=api_key, base_url=base_url)
            else:
                ai_client = OpenAI(api_key=api_key) # Default OpenAI

        ai_config = {
            'provider': provider, 
            'model': model, 
            'history': load_history(),
            'temperature': float(settings.get('temperature', 0.7)),
            'max_tokens': int(settings.get('max_tokens', 1024)),
            'system_prompt': load_soul()
        }
        print(f"  ✅ AI initialized ({provider} -> {model})")
    except Exception as e:
        print(f"  ⚠️  AI init failed: {e}")
        ai_client = None

# Initialize on startup
init_ai()

# ── Continuous Screen Awareness Engine ──
try:
    from core.screen_awareness import screen_awareness
    screen_awareness.start()
    print("  👁️  Continuous Screen Awareness Engine active.")
except Exception as e:
    print(f"  ⚠️  Screen awareness start failed: {e}")

# ── Plugin System ──
from plugin_system import PluginLoader
plugin_loader = PluginLoader()
plugin_loader.discover_plugins({'ai_client': ai_client, 'ai_config': ai_config, 'config_dir': CONFIG_DIR})

APP_MAP = {
    'spotify': 'Spotify', 'whatsapp': 'WhatsApp', 'safari': 'Safari',
    'terminal': 'Terminal', 'mail': 'Mail', 'messages': 'Messages',
    'calendar': 'Calendar', 'notes': 'Notes', 'calculator': 'Calculator',
    'maps': 'Maps', 'photos': 'Photos', 'facetime': 'FaceTime', 'music': 'Music',
    'firefox': 'Firefox', 'firefox private window': 'Firefox', 'visual studio code': 'Visual Studio Code',
    'vscode': 'Visual Studio Code', 'canva': 'Canva',
    'keynote': 'Keynote', 'pages': 'Pages', 'numbers': 'Numbers',
    'weather': 'Weather', 'stocks': 'Stocks', 'journal': 'Journal',
    'reminders': 'Reminders', 'stickies': 'Stickies', 'image capture': 'Image Capture',
    'photo booth': 'Photo Booth', 'clock': 'Clock', 'siri': 'Siri'
}

def strip_cognitive_meta(text: str) -> str:
    """
    Purges any internal cognitive layers, agent planning tags, or chain-of-thought dumps
    from LLM text to ensure clean, authentic MCU J.A.R.V.I.S. speech for Divyanshu sir.
    """
    if not text or not isinstance(text, str):
        return text or ""

    # If the response contains J.A.R.V.I.S. Response marker, extract everything after it
    m_resp = re.search(r'\*\*J\.A\.R\.V\.I\.S\.\s+Response[^\n]*\*\*\s*(.+)', text, flags=re.DOTALL | re.IGNORECASE)
    if m_resp:
        text = m_resp.group(1)

    # Strip (Layer X: ...) or **(Layer X: ...)**
    text = re.sub(r'\*\*?\(Layer\s+\d+:[^\)]+\)\*\*?', '', text, flags=re.IGNORECASE)
    # Strip (AGENT X: ...) or **(AGENT X: ...)**
    text = re.sub(r'\*\*?\(AGENT\s+\d+:[^\)]+\)\*\*?', '', text, flags=re.IGNORECASE)
    # Strip internal cognitive steps: *Intent Detected:...*, *Context:...*, *Goal:...*, etc.
    text = re.sub(r'\*(?:Intent Detected|Context|Constraint|Approach \d+|Goal|Decision Logic|Tool Invocation|Validation Check):[^\*]*\*', '', text, flags=re.IGNORECASE)
    # Strip **Next Step:** or **✅ Next Step:**
    text = re.sub(r'\*\*[\u2705\s]*Next Step:\*\*.*$', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Strip horizontal dividing lines
    text = re.sub(r'^\s*---\s*$', '', text, flags=re.MULTILINE)
    # Strip markdown quotes wrapping entire speech
    text = text.strip()
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1].strip()
    elif text.startswith("'") and text.endswith("'"):
        text = text[1:-1].strip()
    # Normalize excess blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def parse_action_tags(text: str):
    """
    Finds and parses any [ACTION: action_name(...)] tags embedded in J.A.R.V.I.S. output.
    Returns a list of tuples: (action_dict, original_tag_str)
    """
    if not text or not isinstance(text, str):
        return []
    tags = []
    pattern = r'\[ACTION:\s*([a-zA-Z0-9_]+)(?:\((.*?)\))?\]'
    for m in re.finditer(pattern, text):
        act_name = m.group(1).lower().strip()
        args_raw = (m.group(2) or "").strip()
        params = {}
        if args_raw:
            try:
                import ast
                evaled = ast.literal_eval(f"({args_raw},)")
                if act_name in ('open_app', 'close_app'):
                    params = {'name': str(evaled[0])}
                elif act_name == 'desktop_focus':
                    params = {'app': str(evaled[0])}
                elif act_name == 'desktop_snap':
                    params = {'position': str(evaled[0])}
                elif act_name == 'desktop_type':
                    params = {'text': str(evaled[0])}
                elif act_name == 'desktop_key':
                    params = {'key': str(evaled[0])}
                elif act_name == 'whatsapp':
                    params = {'contact': str(evaled[0]), 'message': str(evaled[1]) if len(evaled) > 1 else ''}
                elif act_name == 'whatsapp_call':
                    video = False
                    if len(evaled) > 1:
                        video = bool(evaled[1])
                    elif 'video=true' in args_raw.lower():
                        video = True
                    params = {'contact': str(evaled[0]), 'video': video}
                elif act_name == 'instagram_dm':
                    params = {'recipient': str(evaled[0]), 'message': str(evaled[1]) if len(evaled) > 1 else ''}
                elif act_name == 'youtube_upload':
                    params = {'video_name': str(evaled[0])}
                elif act_name == 'web_search':
                    params = {'query': str(evaled[0])}
                else:
                    params = {'arg': str(evaled[0])}
            except Exception:
                parts = [p.strip().strip('"\'') for p in args_raw.split(',') if p.strip()]
                if act_name in ('open_app', 'close_app'):
                    params = {'name': parts[0] if parts else ''}
                elif act_name == 'desktop_focus':
                    params = {'app': parts[0] if parts else ''}
                elif act_name == 'desktop_snap':
                    params = {'position': parts[0] if parts else 'maximize'}
                elif act_name == 'desktop_type':
                    params = {'text': parts[0] if parts else ''}
                elif act_name == 'desktop_key':
                    params = {'key': parts[0] if parts else 'return'}
                elif act_name == 'whatsapp':
                    params = {'contact': parts[0] if parts else '', 'message': parts[1] if len(parts) > 1 else ''}
                elif act_name == 'whatsapp_call':
                    params = {'contact': parts[0] if parts else '', 'video': ('video' in args_raw.lower())}
                elif act_name == 'instagram_dm':
                    params = {'recipient': parts[0] if parts else '', 'message': parts[1] if len(parts) > 1 else ''}
                elif act_name == 'youtube_upload':
                    params = {'video_name': parts[0] if parts else ''}
                elif act_name == 'web_search':
                    params = {'query': parts[0] if parts else ''}
        else:
            if act_name == 'desktop_minimize':
                params = {}
            elif act_name == 'desktop_list_windows':
                params = {}
        tags.append(({'action': act_name, 'params': params}, m.group(0)))
    return tags

def ask_gemini(message, context=None, image_path=None):
    global ai_client, ai_config, local_vision_model, local_vision_processor
    if not ai_client: return {"error": "AI client is not initialized. Please configure your API key."}

    prompt = message
    if context:
        prompt = f"User said: \"{message}\"\nSystem action performed: {context}\nAcknowledge briefly in JARVIS style."

    try:
        hist = ai_config['history']
        provider = ai_config['provider']
        model = ai_config['model']
        temp = ai_config['temperature']
        mt = ai_config['max_tokens']
        # Context Isolation: Structured boundaries for system, memory, and sensors
        from datetime import datetime
        screen_perception = ""
        try:
            from core.screen_awareness import screen_awareness
            screen_perception = screen_awareness.get_perception_context()
        except Exception:
            pass

        dynamic_sensor = (
            f"- Current Time: {datetime.now().strftime('%I:%M %p')}\n"
            f"- Current Date: {datetime.now().strftime('%A, %B %d, %Y')}\n"
            f"- Operating System: macOS Apple Silicon\n"
            f"- User Name: Divyanshu sir\n"
            f"- Current Location Context: Jaipur, India"
        )
        if screen_perception:
            dynamic_sensor += f"\n[ACTIVE DISPLAY REAL-TIME SENSORS]\n{screen_perception}\n[END DISPLAY SENSORS]"

        memory_data = load_memory()
        
        sys_prompt = assemble_context(
            system_prompt=ai_config.get('system_prompt', ''),
            user_message=prompt,
            trust_level=TrustLevel.LOCAL_OWNER,
            external_data=context if context else None,
            external_source="system_context" if context else "",
            memory_content=memory_data,
            sensor_context=dynamic_sensor
        )

        # LOCAL VISION OVERRIDE (using local Gemma 4 E2B 4-bit on Apple Silicon MLX)
        if image_path and os.path.exists(image_path) and (provider in ('gemma', 'qwen', 'local', 'mlx') or ai_config.get('use_local_vision', True)):
            try:
                import gemma_local
                print("[JARVIS] Inferencing local Gemma 4 E2B vision model on Apple Silicon GPU...")
                res = gemma_local.infer_gemma(
                    prompt=prompt,
                    system_prompt=sys_prompt,
                    history=hist,
                    image_path=image_path,
                    max_tokens=mt,
                    temperature=temp
                )
                clean_res = strip_cognitive_meta(res)
                hist.append({'role': 'user', 'parts': [{'text': prompt + ' [Image Attached]'}]})
                hist.append({'role': 'model', 'parts': [{'text': clean_res}]})
                ai_config['history'] = hist
                save_history(hist)
                return {"response": clean_res}
            except Exception as e:
                print(f"[JARVIS] Local Gemma vision failed: {e}. Falling back to cloud...")

        if provider == 'gemini':
            from google.genai import types
            
            # Ensure history stores serializable dicts, not Part objects
            hist.append({'role': 'user', 'parts': [{'text': prompt}]})
            if len(hist) > 20: hist = hist[-20:]
            
            # Translate serializable dicts to strong types for the API call
            api_contents = []
            for msg in hist:
                msg_parts = []
                for p in msg['parts']:
                    if 'text' in p:
                        msg_parts.append(types.Part.from_text(text=p['text']))
                api_contents.append(types.Content(role=msg['role'], parts=msg_parts))
                
            if image_path and os.path.exists(image_path) and not ai_config.get('use_local_vision', True):
                with open(image_path, "rb") as f: 
                    img_part = types.Part.from_bytes(data=f.read(), mime_type="image/png")
                api_contents[-1].parts.append(img_part)
            
            try:
                response = ai_client.models.generate_content(
                    model=model, contents=api_contents,
                    config=types.GenerateContentConfig(
                        system_instruction=sys_prompt, 
                        max_output_tokens=mt,
                        temperature=temp
                    )
                )
            except Exception as gemini_err:
                err_text = str(gemini_err)
                if "503" in err_text or "404" in err_text or "UNAVAILABLE" in err_text or "NOT_FOUND" in err_text:
                    fallback_models = ['gemini-3.5-flash', 'gemini-3.5-flash-lite']
                    fallback_success = False
                    for fb_model in fallback_models:
                        if fb_model == model: continue
                        try:
                            print(f"[JARVIS] Model {model} unavailable ({err_text[:40]}), falling back to {fb_model}...")
                            response = ai_client.models.generate_content(
                                model=fb_model, contents=api_contents,
                                config=types.GenerateContentConfig(
                                    system_instruction=sys_prompt, 
                                    max_output_tokens=mt,
                                    temperature=temp
                                )
                            )
                            fallback_success = True
                            break
                        except Exception:
                            continue
                    if not fallback_success:
                        raise gemini_err
                else:
                    raise gemini_err

            clean_ret = strip_cognitive_meta(response.text)
            hist[-1]['parts'] = [{'text': message + (' [Image Attached]' if image_path else '')}]
            hist.append({'role': 'model', 'parts': [{'text': clean_ret}]})
            ret = clean_ret
            
        elif provider in ('gemma', 'qwen', 'local', 'mlx'):
            # Local Gemma 4 E2B 4-bit Provider (Offline, GPU MLX accelerated)
            import gemma_local
            print("[JARVIS] Inferencing local Gemma 4 E2B on Apple Silicon MLX...")
            res = gemma_local.infer_gemma(
                prompt=prompt,
                system_prompt=sys_prompt,
                history=hist,
                image_path=image_path if (image_path and os.path.exists(image_path)) else None,
                max_tokens=mt,
                temperature=temp
            )
            clean_res = strip_cognitive_meta(res)
            hist.append({'role': 'user', 'parts': [{'text': prompt + (' [Image Attached]' if image_path else '')}]})
            hist.append({'role': 'model', 'parts': [{'text': clean_res}]})
            ret = clean_res
            
        else:
            # OpenAI compatible endpoints
            oai_hist = [{"role": "system", "content": sys_prompt}]
            for msg in hist:
                role = "assistant" if msg['role'] == "model" else "user"
                oai_hist.append({"role": role, "content": msg['parts'][0]['text']})
                
            content_arr = [{"type": "text", "text": prompt}]
            if image_path and os.path.exists(image_path):
                import base64
                with open(image_path, "rb") as f:
                    base64_image = base64.b64encode(f.read()).decode('utf-8')
                content_arr.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                })
            
            oai_hist.append({"role": "user", "content": content_arr})
            
            if len(oai_hist) > 21: oai_hist = [oai_hist[0]] + oai_hist[-20:]
            
            response = ai_client.chat.completions.create(
                model=model,
                messages=oai_hist,
                max_tokens=mt,
                temperature=temp
            )
            clean_oai = strip_cognitive_meta(response.choices[0].message.content)
            
            hist.append({'role': 'user', 'parts': [{'text': prompt}]})
            hist.append({'role': 'model', 'parts': [{'text': clean_oai}]})
            ret = clean_oai

        # Auto-memory: check if the user shared important personal info
        auto_mem_triggers = ['my name is', 'i live in', 'i work at', 'remember that', 'don\'t forget', 'keep in mind', 'note that', 'i like', 'i hate', 'my favorite', 'my birthday']
        msg_lower = message.lower()
        if any(trigger in msg_lower for trigger in auto_mem_triggers):
            # Memory poisoning defense: only append if content is completely safe
            mem_fw = inspect_input(message)
            if mem_fw.verdict == FirewallVerdict.SAFE:
                append_memory(f"[User said] {message}")
            else:
                print(f"[SECURITY] Memory write rejected due to suspicious content: {mem_fw.signals}")

        ai_config['history'] = hist
        save_history(hist)

        try:
            from interfaces.telemetry import telemetry_engine
            telemetry_engine.record_inference(
                provider=provider,
                prompt_tokens=max(1, len(prompt) // 4),
                completion_tokens=max(1, len(ret) // 4)
            )
        except Exception:
            pass

        return {"response": strip_cognitive_meta(ret)}
        
    except Exception as e:
        err_str = str(e)
        print(f"  AI error: {err_str}", flush=True)
        
        # Smart Hybrid Router: Seamless fallback to local Gemma 4 E2B on Apple Silicon GPU!
        if provider not in ('gemma', 'qwen', 'local', 'mlx'):
            try:
                import gemma_local
                print("[JARVIS HYBRID ROUTER] Cloud core error encountered. Seamlessly failing over to Local Gemma 4 E2B on Apple Silicon MLX GPU...")
                fallback_res = gemma_local.infer_gemma(
                    prompt=prompt,
                    system_prompt=sys_prompt,
                    history=hist,
                    image_path=image_path if (image_path and os.path.exists(image_path)) else None,
                    max_tokens=mt,
                    temperature=temp
                )
                clean_fb = strip_cognitive_meta(fallback_res)
                hist.append({'role': 'user', 'parts': [{'text': prompt + (' [Image Attached]' if image_path else '')}]})
                hist.append({'role': 'model', 'parts': [{'text': clean_fb}]})
                ai_config['history'] = hist
                save_history(hist)
                return {"response": clean_fb}
            except Exception as fb_err:
                print(f"[JARVIS HYBRID ROUTER] Local fallback error: {fb_err}")

        # Format the error for Jarvis
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
            jarvis_msg = "Sir, we have exhausted our API quota for this specific AI core. I recommend switching to an alternative provider in the settings panel."
        elif "401" in err_str or "API_KEY_INVALID" in err_str:
            jarvis_msg = "Sir, the API key for this core appears to be invalid or missing. Please update it in the configuration matrix."
        else:
            jarvis_msg = "Sir, I am unable to connect to the central AI matrix at this time. We may be offline."
            
        return {"error": jarvis_msg}

def get_morning_briefing():
    """Synthesize an authentic cinema-grade Paul Bettany morning briefing."""
    from datetime import datetime
    import subprocess
    import json
    
    now = datetime.now()
    hour = now.hour
    if hour < 12:
        greeting = "Good morning, Divyanshu sir."
    elif hour < 17:
        greeting = "Good afternoon, Divyanshu sir."
    else:
        greeting = "Good evening, Divyanshu sir."
        
    batt_str = "Battery status nominal."
    try:
        batt_res = subprocess.run(['pmset', '-g', 'batt'], capture_output=True, text=True, timeout=4)
        m = re.search(r'(\d+)%', batt_res.stdout)
        pct = m.group(1) if m else "98"
        is_ac = 'ac power' in batt_res.stdout.lower() or 'charging' in batt_res.stdout.lower()
        batt_str = f"MacBook battery is at {pct}%{' and connected to AC power' if is_ac else ' on battery reserve'}."
    except Exception:
        pass

    weather_str = "Clear skies reported in Jaipur."
    try:
        import urllib.request
        req = urllib.request.Request('https://wttr.in/Jaipur?format=j1', headers={'User-Agent': 'JarvisAI/5.0'})
        with urllib.request.urlopen(req, timeout=4) as resp:
            wdata = json.loads(resp.read().decode('utf-8'))
            cur = wdata.get('current_condition', [{}])[0]
            temp = cur.get('temp_C', '28')
            desc = cur.get('weatherDesc', [{}])[0].get('value', 'Clear')
            weather_str = f"Currently in Jaipur, it is {temp} degrees Celsius with {desc.lower()} conditions."
    except Exception:
        pass

    app_str = ""
    try:
        from desktop_controller import WindowController
        front = WindowController.get_frontmost_app()
        if front.get('success') and front.get('data'):
            app_str = f"Your primary active interface is {front['data']}."
    except Exception:
        pass

    prompt = f"""You are J.A.R.V.I.S. Deliver an authentic, sophisticated, and witty morning briefing to your creator and boss, Divyanshu Verma, Founder & CEO of Divyanshu Industries.
Context:
- Greeting: {greeting}
- Local Time: {now.strftime('%I:%M %p, %A, %B %d')}
- Environment: {weather_str}
- Hardware: {batt_str}
- Active app: {app_str}

Respond in 2-3 concise sentences in your signature dry British tone. Address him as sir, confirm systems operational, and ask how you may assist."""

    ai_resp = ask_gemini(prompt)
    briefing_text = ai_resp.get('response', str(ai_resp)) if isinstance(ai_resp, dict) else str(ai_resp)
    return briefing_text

def parse_commands(msg):
    msg = msg.lower().strip()
    actions = []
    
    split_regex = r'(?:\s+and\s+|\s+then\s+|\s+along\s+(?:with\s+)?(?:that\s+)?|,\s*)(?=open|launch|start|run|play|listen|close|quit|kill|stop|search|google|find|set|volume|brightness|lock|sleep|analyze|read|what|send|message|whatsapp|call|video call|audio call|upload|post|dm|instagram)'
    clauses = re.split(split_regex, msg)
    
    for clause in clauses:
        clause = clause.strip()
        if not clause: continue
        
        if any(k in clause for k in ['good morning', 'morning brief', 'morning briefing', 'daily briefing', 'status briefing', 'morning report', 'brief me', 'sitrep', 'daily report']):
            actions.append({'action': 'briefing'})
            continue

        screen_vision_triggers = [
            'look at my screen', "what's on my screen", 'what is on my screen',
            'what am i watching', 'what am i watching on screen', 'what am i looking at',
            'what is playing', 'what video is this', 'look out my screen',
            'tell me what is on my screen', 'tell me what i am watching',
            'read my screen', 'read the screen', 'see this',
            'check my screen', 'analyze my screen', 'analyze screen', 'describe my screen',
            'what error is on my screen', 'help me with this error', 'read this error',
            'summarize my screen', 'summarize this page', 'summarize what is on my screen',
            'summarize what i am watching',
            'take a screenshot and explain', 'look at this window', 'copilot vision',
            'screen scan', 'scan screen', 'screenshot and explain'
        ]
        if any(k in clause for k in screen_vision_triggers):
            actions.append({'action': 'analyze_screen', 'params': {'query': clause}})
            continue
            
        if clause in ('play music', 'play', 'resume'):
            actions.append({'action': 'media_control', 'params': {'cmd': 'play'}})
            continue
        if clause in ('pause music', 'pause', 'stop music', 'stop'):
            actions.append({'action': 'media_control', 'params': {'cmd': 'pause'}})
            continue
        if clause in ('next track', 'next song', 'skip'):
            actions.append({'action': 'media_control', 'params': {'cmd': 'next track'}})
            continue
        if clause in ('previous track', 'previous song', 'back'):
            actions.append({'action': 'media_control', 'params': {'cmd': 'previous track'}})
            continue
            
        m = re.match(r'(?:play|listen to)\s+(.+?)(?:\s+on\s+spotify)?$', clause)
        if m:
            song = m.group(1).strip()
            if song not in ('music', 'pause', 'stop', 'next', 'previous'):
                actions.append({'action': 'play_song', 'params': {'song': song}})
            continue
            
        # WhatsApp Agent Intelligence & Summaries
        if any(p in clause for p in [
            "what's happening on whatsapp", "what is happening on whatsapp",
            "what are my whatsapp updates", "whatsapp updates", "show me my whatsapp updates",
            "summarize my whatsapp", "summarize whatsapp", "what are the whatsapp updates"
        ]):
            actions.append({'action': 'whatsapp_activity_summary'})
            continue

        if any(p in clause for p in [
            "who messaged me", "who sent me messages", "who contacted me", "did anyone message me"
        ]):
            actions.append({'action': 'whatsapp_who_messaged'})
            continue

        if "who needs a reply" in clause or "needs a response" in clause:
            actions.append({'action': 'whatsapp_needs_reply'})
            continue

        if any(p in clause for p in ["since i left", "while i was away", "what's new on whatsapp"]):
            actions.append({'action': 'whatsapp_delta'})
            continue

        if clause in ("check whatsapp", "whatsapp status", "whatsapp health", "is whatsapp working"):
            actions.append({'action': 'whatsapp_health'})
            continue

        m_sum = re.match(r'summarize\s+(.+?)(?:\'s)?\s+messages?', clause)
        if not m_sum:
            m_sum = re.match(r'what\s+did\s+(.+?)\s+(?:say|send|message)(?:\s+yesterday|\s+today)?\??$', clause)
        if m_sum:
            actions.append({'action': 'whatsapp_summarize_contact', 'params': {'contact': m_sum.group(1).strip()}})
            continue

        if any(clause.startswith(k) for k in ("say hello", "say hi", "say good morning", "say good evening", "say good night", "wish ", "tell ")):
            actions.append({'action': 'whatsapp_conversational', 'params': {'text': clause}})
            continue

        # WhatsApp Call parsing
        m_call = re.match(r'(?:call(?:\s+to)?|make\s+(?:a\s+)?(?:call|phone\s+call)\s+to|place\s+(?:a\s+)?call\s+to|start\s+(?:a\s+)?call\s+with|audio\s+call(?:\s+to)?|video\s+call(?:\s+to)?|whatsapp\s+call(?:\s+to)?)\s+(.+?)(?:\s+(?:on|via|using)\s+whatsapp)?$', clause)
        if m_call:
            video = 'video' in clause
            actions.append({'action': 'whatsapp_call', 'params': {'contact': m_call.group(1).strip(), 'video': video}})
            continue

        # WhatsApp Media parsing
        m_media = re.match(r'(?:send\s+a?\s*(?:photo|image|picture|file|media|document)\s+(.+?)\s+to\s+(.+?)(?:\s+on\s+whatsapp)?(?:\s+(?:with\s+caption|captioned)\s+(.+))?)$', clause)
        if not m_media:
            m_media = re.match(r'(?:whatsapp\s+(?:photo|image|picture|file|media|document)\s+(.+?)\s+to\s+(.+?)(?:\s+(?:with\s+caption|captioned)\s+(.+))?)$', clause)
        if m_media:
            f_path = m_media.group(1).strip().strip('"').strip("'")
            c_target = m_media.group(2).strip()
            c_caption = m_media.group(3).strip() if m_media.group(3) else ""
            actions.append({'action': 'whatsapp_media', 'params': {'contact': c_target, 'file_path': f_path, 'caption': c_caption}})
            continue

        # Instagram Direct Automation
        m_insta = re.match(r'(?:send\s+(?:a\s+)?message\s+to|message|dm)\s+(.+?)\s+on\s+instagram(?:\s+(?:saying|with|that)\s+(.+))?$', clause)
        if not m_insta:
            m_insta_alt = re.match(r'(?:send|text)\s+["\']?(.+?)["\']?\s+to\s+(.+?)\s+on\s+instagram$', clause)
            if m_insta_alt:
                actions.append({'action': 'instagram_dm', 'params': {'recipient': m_insta_alt.group(2).strip(), 'message': m_insta_alt.group(1).strip()}})
                continue
        if m_insta:
            rec = m_insta.group(1).strip()
            msg_txt = m_insta.group(2).strip() if m_insta.group(2) else ""
            actions.append({'action': 'instagram_dm', 'params': {'recipient': rec, 'message': msg_txt}})
            continue

        # YouTube Video Upload
        m_yt = re.search(r'(?:upload|post)\s+(?:(?:the|a)\s+)?video\s+(?:named\s+|called\s+)?["\']?([^"\']+)["\']?\s+to\s+youtube(?:\s+with\s+(?:suitable\s+)?(?:titles?\s+and\s+descriptions?|metadata))?', clause)
        if not m_yt:
            m_yt = re.search(r'video\s+(?:named\s+|called\s+)?["\']?([^"\']+)["\']?\s+(?:just\s+)?upload\s+(?:it\s+)?to\s+youtube(?:\s+with\s+(?:suitable\s+)?(?:titles?\s+and\s+descriptions?|metadata))?', clause)
        if m_yt:
            vname = m_yt.group(1).strip()
            actions.append({'action': 'youtube_upload', 'params': {'video_name': vname}})
            continue

        # WhatsApp Message parsing with explicit message (including "reply to ...")
        m_msg = re.match(r'(?:send\s+a?\s*message\s+to|message|whatsapp|reply\s+(?:to\s+)?)\s+(.+?)\s+(?:on|using)?\s*whatsapp\s+(?:saying|that|with)\s+(.+)', clause)
        if not m_msg:
             m_msg = re.match(r'(?:whatsapp|message|reply\s+(?:to\s+)?)\s+(.+?)\s+(?:saying|that|with)\s+(.+)', clause)
        
        if m_msg: 
            actions.append({'action': 'whatsapp', 'params': {'contact': m_msg.group(1).strip(), 'message': m_msg.group(2).strip()}})
            continue
            
        # WhatsApp Message without explicit message payload
        m_msg_empty = re.match(r'(?:send\s+a?\s*message\s+to|message|whatsapp)\s+(.+?)(?:\s+on\s+whatsapp)?$', clause)
        if m_msg_empty:
             actions.append({'action': 'whatsapp', 'params': {'contact': m_msg_empty.group(1).strip(), 'message': ''}})
             continue

        # WhatsApp message: "send <message> to <contact>" (e.g. "send hello to subham")
        m_send_to = re.match(r'(?:send|text)\s+["\']?(.+?)["\']?\s+to\s+([a-zA-Z0-9_\s+]+?)(?:\s+(?:on|via|using)\s+(?:whatsapp|wa))?$', clause)
        if m_send_to:
            msg_text = m_send_to.group(1).strip()
            c_target = m_send_to.group(2).strip()
            if c_target not in ('sleep', 'right', 'left', 'instagram', 'youtube') and msg_text not in ('photo', 'image', 'picture', 'file', 'media', 'document'):
                actions.append({'action': 'whatsapp', 'params': {'contact': c_target, 'message': msg_text}})
                continue
             
        # Read Chat parsing
        m_read = re.match(r'(?:read|check)\s+(?:my\s+)?(?:chat|messages)\s+(?:with|from)\s+(.+?)(?:\s+on\s+whatsapp)?$', clause)
        if m_read:
             actions.append({'action': 'whatsapp_read', 'params': {'contact': m_read.group(1).strip()}})
             continue

        m = re.match(r'(?:open|launch|start|run)\s+(.+)', clause)
        if not m: m = re.match(r"let'?s?\s+open\s+(.+)", clause)
        if m:
            target_str = m.group(1)
            parts = re.split(r'\s+and\s+|,', target_str)
            keys = sorted(APP_MAP.keys(), key=len, reverse=True)
            
            for p in parts:
                p = p.strip()
                if not p: continue
                
                found_in_part = []
                temp = p
                for k in keys:
                    idx = temp.find(k)
                    while idx != -1:
                        found_in_part.append((idx, k))
                        temp = temp[:idx] + ' ' * len(k) + temp[idx+len(k):]
                        idx = temp.find(k)
                        
                if len(found_in_part) > 1:
                    found_in_part.sort()
                    for pos, k in found_in_part:
                        if k in ('terminal', 'the terminal', 'a terminal'): k = 'terminal'
                        actions.append({'action': 'open_app', 'params': {'name': k}})
                else:
                    t = p.rstrip('.')
                    if t in ('terminal', 'the terminal', 'a terminal'): t = 'terminal'
                    actions.append({'action': 'open_app', 'params': {'name': t}})
            continue
            
        m = re.match(r'(?:close|quit|kill|stop|exit|shut down)\s+(.+)', clause)
        if m:
            target_str = m.group(1)
            parts = re.split(r'\s+and\s+|,', target_str)
            keys = sorted(APP_MAP.keys(), key=len, reverse=True)
            for p in parts:
                p = p.strip()
                if not p: continue
                found_in_part = []
                temp = p
                for k in keys:
                    idx = temp.find(k)
                    while idx != -1:
                        found_in_part.append((idx, k))
                        temp = temp[:idx] + ' ' * len(k) + temp[idx+len(k):]
                        idx = temp.find(k)
                if len(found_in_part) > 1:
                    found_in_part.sort()
                    for pos, k in found_in_part:
                        actions.append({'action': 'close_app', 'params': {'name': k}})
                else:
                    t = p.rstrip('.')
                    actions.append({'action': 'close_app', 'params': {'name': t}})
            continue
            
        if any(k in clause for k in ['screenshot', 'screen capture']):
            actions.append({'action': 'screenshot'})
            continue
            
        m = re.search(r'volume\s+(?:to\s+)?(\d+)', clause)
        if m:
            actions.append({'action': 'volume', 'params': {'level': int(m.group(1))}})
            continue
            
        m = re.search(r'brightness\s+(?:to\s+)?(\d+)', clause)
        if m:
            actions.append({'action': 'brightness', 'params': {'level': int(m.group(1))}})
            continue
            
        if any(k in clause for k in ['system info', 'system status', 'diagnostics', 'cpu usage', 'ram usage']):
            actions.append({'action': 'system_info'})
            continue
            
        if any(k in clause for k in ['lock screen', 'lock my mac']):
            actions.append({'action': 'lock_screen'})
            continue
        if clause in ('sleep', 'go to sleep'):
            actions.append({'action': 'sleep'})
            continue
            
        m = re.match(r'(?:search|google|look up|find)\s+(?:for\s+)?(.+)', clause)
        if m:
            actions.append({'action': 'web_search', 'params': {'query': m.group(1).strip()}})
            continue
        
        # Read/summarize a webpage
        m = re.match(r'(?:read|summarize|open and read|what does .+ say)\s+(.*)', clause)
        if m:
            raw = m.group(1).strip()
            # Try to extract just the url
            urls = re.findall(r'(https?://\S+|www\.\S+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', raw)
            url = urls[0] if urls else raw.split()[-1]
            if '.' in url:  # Likely a URL
                if not url.startswith('http'):
                    url = 'https://' + url
                actions.append({'action': 'read_page', 'params': {'url': url}})
                continue
        
        # Desktop automation commands
        m = re.match(r'(?:type|write|enter)\s+["\'](.+?)["\']', clause)
        if m:
            actions.append({'action': 'desktop_type', 'params': {'text': m.group(1)}})
            continue
        
        m = re.match(r'(?:press|hit)\s+(.+)', clause)
        if m:
            actions.append({'action': 'desktop_key', 'params': {'key': m.group(1).strip()}})
            continue
        
        if any(k in clause for k in ['snap window left', 'window to left', 'tile left']):
            actions.append({'action': 'desktop_snap', 'params': {'position': 'left'}})
            continue
        if any(k in clause for k in ['snap window right', 'window to right', 'tile right']):
            actions.append({'action': 'desktop_snap', 'params': {'position': 'right'}})
            continue
        if any(k in clause for k in ['maximize window', 'fullscreen', 'full screen']):
            actions.append({'action': 'desktop_snap', 'params': {'position': 'maximize'}})
            continue
        if any(k in clause for k in ['minimize window', 'minimize']):
            actions.append({'action': 'desktop_minimize'})
            continue
        if any(k in clause for k in ['list windows', 'show windows', 'what windows']):
            actions.append({'action': 'desktop_list_windows'})
            continue
        
        m = re.match(r'(?:focus|switch to|go to)\s+(.+)', clause)
        if m:
            target = m.group(1).strip()
            if target not in ('sleep',):
                actions.append({'action': 'desktop_focus', 'params': {'app': target}})
                continue
        
        if any(k in clause for k in ['enable gestures', 'start gestures', 'start air mouse', 'enable air mouse', 'turn on gestures', 'turn on air mouse', 'activate air mouse', 'activate gestures', 'air mouse on', 'gestures on']):
            actions.append({'action': 'toggle_gestures', 'params': {'enable': True}})
            continue
        if any(k in clause for k in ['disable gestures', 'stop gestures', 'stop air mouse', 'disable air mouse', 'turn off gestures', 'turn off air mouse', 'deactivate air mouse', 'air mouse off', 'gestures off']):
            actions.append({'action': 'toggle_gestures', 'params': {'enable': False}})
            continue
            
    return actions

def _raw_execute_action(action_data):
    action = action_data.get('action')
    params = action_data.get('params', {})
    result = {'action': action, 'success': True, 'data': None}

    try:
        if action in ('whatsapp', 'whatsapp_call', 'whatsapp_read', 'whatsapp_media',
                      'whatsapp_activity_summary', 'whatsapp_who_messaged', 'whatsapp_needs_reply',
                      'whatsapp_delta', 'whatsapp_summarize_contact', 'whatsapp_conversational', 'whatsapp_health'):
            from agents.whatsapp import whatsapp_agent
            from whatsapp_controller import WhatsAppController
            wa = WhatsAppController()

            contact = params.get('contact', '')
            if contact:
                contact = whatsapp_agent.context.resolve_target(contact)

            if action == 'whatsapp_activity_summary':
                result['data'] = whatsapp_agent.summarize_recent_activity()
            elif action == 'whatsapp_who_messaged':
                act = whatsapp_agent.get_recent_activity()
                result['data'] = whatsapp_agent.summarizer.get_senders_summary(act)
            elif action == 'whatsapp_needs_reply':
                act = whatsapp_agent.get_recent_activity()
                result['data'] = whatsapp_agent.summarizer.get_needs_reply_summary(act)
            elif action == 'whatsapp_delta':
                act = whatsapp_agent.get_recent_activity()
                result['data'] = whatsapp_agent.monitor.get_delta_since_last_seen(act)
            elif action == 'whatsapp_summarize_contact':
                result['data'] = whatsapp_agent.summarize_conversation(contact)
            elif action == 'whatsapp_conversational':
                h_res = whatsapp_agent.handle_command(params.get('text', ''))
                result['data'] = h_res.get('response', 'Command processed.')
                result['success'] = h_res.get('success', True)
            elif action == 'whatsapp_health':
                hc = whatsapp_agent.health_check()
                result['data'] = hc.get('summary', 'WhatsApp health check complete.')
            elif action == 'whatsapp_call':
                video = params.get('video', False)
                res = whatsapp_agent.call(contact, "video" if video else "voice")
                if res.success:
                    result['data'] = res.message or f"Calling {contact} on WhatsApp"
                else:
                    try:
                        c_res = wa.initiate_call(contact, video=video)
                        if c_res.get('success'):
                            result['success'] = True
                            result['data'] = f"Calling {contact} on WhatsApp"
                        else:
                            result['success'] = False
                            result['data'] = res.confirmation_reason or res.error or c_res.get('details', 'Call failed')
                    except Exception:
                        result['success'] = False
                        result['data'] = res.confirmation_reason or res.error or "Call failed"
            elif action == 'whatsapp_read':
                msgs = whatsapp_agent.read_conversation(contact)
                if msgs:
                    result['data'] = f"Recent messages with {contact}: " + " | ".join(m.text for m in msgs)
                else:
                    result['data'] = f"No recent messages found with {contact}."
            elif action == 'whatsapp_media':
                file_path = params.get('file_path', '')
                caption = params.get('caption', '')
                res = wa.send_media(contact, file_path, caption=caption)
                if res['success']:
                    result['data'] = f"Sent media to {res.get('contact', contact)}"
                else:
                    result['success'] = False
                    result['data'] = res.get('error', res.get('status', 'Unknown Error')) + ": " + res.get('details', '')
            else:
                msg_text = params.get('message', '')
                if msg_text == '':
                    result['success'] = False
                    result['data'] = "empty_message"
                else:
                    res = whatsapp_agent.send_message(contact, msg_text)
                    if res.success:
                        result['data'] = f"Sending message to {contact}"
                    else:
                        try:
                            m_res = wa.send_message(contact, msg_text)
                            if m_res.get('success'):
                                result['success'] = True
                                result['data'] = f"Sending message to {contact}"
                            else:
                                result['success'] = False
                                result['data'] = res.confirmation_reason or res.error or m_res.get('details', 'Message failed')
                        except Exception:
                            result['success'] = False
                            result['data'] = res.confirmation_reason or res.error or "Message failed"

        elif action == 'play_song':
            song = params.get('song', '')
            search_uri = f"spotify:search:{song}"
            
            script = f'tell application "Spotify"\nactivate\nplay track "{search_uri}"\nend tell'
            subprocess.Popen(['osascript', '-e', script])
            result['data'] = f'Playing {song} on Spotify'

        elif action == 'open_app':
            name = params.get('name', '')
            actual = APP_MAP.get(name.lower(), name.title())
            subprocess.Popen(['open', '-a', actual], stderr=subprocess.PIPE)
            result['data'] = f'Opening {actual}'

        elif action == 'close_app':
            name = params.get('name', '')
            actual = APP_MAP.get(name.lower(), name.title())
            subprocess.run(['osascript', '-e', f'tell application "{actual}" to quit'], capture_output=True, timeout=5)
            result['data'] = f'Closing {actual}'

        elif action == 'media_control':
            cmd = params.get('cmd')
            script = f'if application "Spotify" is running then\ntell application "Spotify" to {cmd}\nelse if application "Music" is running then\ntell application "Music" to {cmd}\nelse\ntell application "Spotify"\nactivate\n{cmd}\nend tell\nend if'
            subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
            result['data'] = f'Media control: {cmd}'
            
        elif action == 'screenshot':
            subprocess.Popen(['screencapture', '-i'])
            result['data'] = 'Screenshot tool opened.'
            
        elif action == 'volume':
            level = params.get('level', 50)
            subprocess.run(['osascript', '-e', f'set volume output volume {level}'])
            result['data'] = f'Volume set to {level}%'
            
        elif action == 'brightness':
            level = params.get('level', 50) / 100.0
            subprocess.run(['brightness', str(level)], stderr=subprocess.PIPE)
            result['data'] = f'Brightness set to {level*100}%'
            
        elif action == 'lock_screen':
            subprocess.run(['pmset', 'displaysleepnow'])
            result['data'] = 'Screen locked.'

        elif action == 'web_search':
            query = params.get('query', '')
            try:
                from browser_agent import WebSearchAgent
                # Try instant answer first
                instant = WebSearchAgent.quick_answer(query)
                if instant['success'] and instant['answer']:
                    result['data'] = instant['answer']
                else:
                    # Full search with result extraction
                    search_res = WebSearchAgent.search(query)
                    result['data'] = search_res.get('summary', f"Searching web for {query}")
            except Exception as e:
                # Fallback to opening browser
                q = urllib.parse.quote_plus(query)
                subprocess.Popen(['open', f'https://www.google.com/search?q={q}'])
                result['data'] = f"Searching web for {query}"
            
        elif action == 'read_page':
            url = params.get('url', '')
            try:
                from browser_agent import PageReader
                page = PageReader.read_page(url)
                if page['success']:
                    # Send the page text to AI for summarization
                    context = f"The user asked to read this webpage. Title: {page['title']}. Content: {page['text'][:3000]}"
                    ai_resp = ask_gemini(f"Summarize this page for me: {url}", context=context)
                    if isinstance(ai_resp, dict):
                        result['data'] = ai_resp.get('response', ai_resp.get('error', 'Error reading page'))
                    else:
                        result['data'] = str(ai_resp)
                else:
                    result['success'] = False
                    result['data'] = page.get('text', 'Failed to fetch page.')
            except Exception as e:
                result['data'] = f"Failed to read page: {e}"
                result['success'] = False

        elif action == 'desktop_type':
            from desktop_controller import KeyboardController
            res = KeyboardController.type_text(params.get('text', ''))
            result['success'] = res['success']
            result['data'] = res['data']
            
        elif action == 'desktop_key':
            from desktop_controller import KeyboardController
            key = params.get('key', '')
            if '+' in key:
                keys = [k.strip() for k in key.split('+')]
                res = KeyboardController.hotkey(*keys)
            else:
                res = KeyboardController.press_key(key)
            result['success'] = res['success']
            result['data'] = res['data']
            
        elif action == 'desktop_snap':
            from desktop_controller import WindowController
            res = WindowController.snap_window(params.get('position', 'maximize'))
            result['success'] = res['success']
            result['data'] = res['data']
            
        elif action == 'desktop_minimize':
            from desktop_controller import WindowController
            res = WindowController.minimize_window()
            result['success'] = res['success']
            result['data'] = res['data']
            
        elif action == 'desktop_list_windows':
            from desktop_controller import WindowController
            res = WindowController.list_windows()
            result['success'] = res['success']
            result['data'] = res['data']
            
        elif action == 'desktop_focus':
            from desktop_controller import WindowController
            res = WindowController.focus_app(params.get('app', '').title())
            result['success'] = res['success']
            result['data'] = res['data']

        elif action == 'briefing':
            briefing_text = get_morning_briefing()
            result['success'] = True
            result['data'] = briefing_text

        elif action == 'toggle_gestures':
            result['success'] = True
            result['data'] = {'enable': params.get('enable', True)}

        elif action == 'instagram_dm':
            from integrations.instagram import InstagramController
            rec = params.get('recipient', '')
            msg_text = params.get('message', '')
            res = InstagramController.send_direct_message(rec, msg_text)
            result['success'] = res.get('success', True)
            result['data'] = res.get('data', str(res))

        elif action == 'youtube_upload':
            from integrations.youtube import YouTubeUploaderTool
            yt_tool = YouTubeUploaderTool()
            v_name = params.get('video_name', '')
            res = yt_tool.execute({'action': 'upload_video', 'video_name': v_name})
            result['success'] = res.success
            result['data'] = res.data

    except Exception as e:
        result['success'] = False
        result['data'] = f"Error executing action: {e}"
        print(f"Action error: {e}")

    return result

def execute_action(action_data, trust_level=TrustLevel.LOCAL_OWNER):
    """
    Execute action through Central Security Kernel.
    Enforces policy authorization, parameter validation, sandbox limits, and audit hashing.
    """
    t0 = time.time()
    res = security_kernel.authorize_and_execute(
        action_data=action_data,
        trust_level=trust_level,
        executor_fn=_raw_execute_action
    )
    duration_ms = (time.time() - t0) * 1000.0
    try:
        from interfaces.telemetry import telemetry_engine
        tool_act = action_data.get('action', 'unknown')
        success = bool(res.get('success', False)) if isinstance(res, dict) else True
        telemetry_engine.record_tool_execution(tool_act, duration_ms, success)
    except Exception:
        pass
    return res

# ── Endpoints ──

@app.route('/api/status')
def status():
    return jsonify({
        'status': 'ok',
        'ai': 'active' if ai_client else 'fallback',
        'provider': ai_config.get('provider', 'gemini'),
        'model': ai_config.get('model', 'gemini-3.5-flash')
    })

@app.route('/api/settings', methods=['GET', 'POST'])
def settings_route():
    trust = resolve_trust_level(request=request)
    if request.method == 'POST':
        auth = security_kernel.authorize_action("settings_write", request.json or {}, trust_level=trust)
        if not auth.allowed:
            return jsonify({'success': False, 'error': auth.reason}), 403
        data = request.json or {}
        s = load_settings()
        s['provider'] = data.get('provider', s.get('provider'))
        s['model'] = data.get('model', s.get('model'))
        if 'api_keys' in data: s['api_keys'] = data['api_keys']
        
        # New Settings
        if 'temperature' in data: s['temperature'] = float(data['temperature'])
        if 'max_tokens' in data: s['max_tokens'] = int(data['max_tokens'])
        if 'system_prompt' in data: s['system_prompt'] = data['system_prompt']
        
        save_settings(s)
        return jsonify({'success': True})
    auth = security_kernel.authorize_action("settings_read", {}, trust_level=trust)
    if not auth.allowed:
        return jsonify({'success': False, 'error': auth.reason}), 403
    return jsonify(load_settings())

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json or {}
    raw_msg = data.get('message', '')
    
    # 0. Process input through Defense-in-Depth Security Kernel (Stages 1-3)
    processed = security_kernel.process_input(raw_msg, request=request, is_internal=False)
    if processed.is_blocked:
        return jsonify({
            'response': "Sir, your request was blocked by the security firewall due to anomalous or potentially hazardous command structures.",
            'action': None
        }), 400
        
    msg = processed.normalized_message
    
    # 1. Parse for actions
    actions = parse_commands(msg)
    if actions:
        responses = []
        last_exec_res = None
        
        for action_data in actions:
            if action_data['action'] == 'analyze_screen':
                auth = security_kernel.authorize_action('analyze_screen', action_data.get('params', {}), trust_level=processed.trust_level)
                if not auth.allowed:
                    return jsonify({'response': f"Security policy restriction: {auth.reason}", 'action': None}), 403

                img_path = '/tmp/jarvis_vision.png'
                subprocess.run(['screencapture', '-x', img_path])
                
                # Perform native Apple Silicon OCR extraction & screen state extraction
                ocr_context = ""
                watching_context = ""
                try:
                    from core.screen_awareness import screen_awareness
                    active_info = screen_awareness.force_refresh()
                    watching_context = (
                        f"\n[ACTIVE DISPLAY TELEMETRY]\n"
                        f"• Foreground Application: {active_info.get('active_app')}\n"
                        f"• Foreground Window Title: {active_info.get('window_title')}\n"
                        f"• What User is Watching / Doing: {active_info.get('watching_summary')}\n"
                    )
                    if active_info.get('browser_url'):
                        watching_context += f"• URL: {active_info.get('browser_url')}\n"
                    watching_context += "[END DISPLAY TELEMETRY]\n"

                    if active_info.get('ocr_text'):
                        ocr_context = "\n" + build_external_data_block(
                            active_info['ocr_text'][:1200],
                            source="macOS Vision OCR Ground Truth"
                        ) + "\n"
                except Exception as e:
                    print(f"[JARVIS OCR] Notice: {e}")
                    try:
                        from desktop_controller import ScreenController
                        ocr_res = ScreenController.ocr_screen(img_path)
                        if ocr_res.get('success') and ocr_res.get('data'):
                            ocr_context = "\n" + build_external_data_block(
                                ocr_res['data'][:1200],
                                source="macOS Vision OCR Ground Truth"
                            ) + "\n"
                    except Exception:
                        pass

                ai_resp = ask_gemini(
                    msg,
                    context=f"Captured a high-resolution screenshot of the user's active display.{watching_context}{ocr_context}\nDirectly explain what the user is watching or viewing in J.A.R.V.I.S. style.\nIf the user asks to click, focus, or snap a window, you may include [ACTION: desktop_snap(\"left\")] or [ACTION: desktop_focus(\"App\")] or [ACTION: desktop_type(\"text\")].",
                    image_path=img_path
                )
                if os.path.exists(img_path):
                    try: os.remove(img_path)
                    except Exception: pass
                
                resp_text = ai_resp.get('response', str(ai_resp)) if isinstance(ai_resp, dict) else str(ai_resp)

                # Execute autonomous copilot actions if requested - STRICTLY ROUTED THROUGH SECURITY KERNEL
                action_tags = parse_action_tags(resp_text)
                autonomous_actions = []
                last_copilot_res = None
                if action_tags:
                    for auto_dict, tag_str in action_tags:
                        auto_res = execute_action(auto_dict, trust_level=processed.trust_level)
                        last_copilot_res = auto_res
                        if auto_res.get('success'):
                            autonomous_actions.append(auto_dict['action'])
                        else:
                            print(f"[JARVIS COPILOT] Autonomous action rejected by security kernel: {auto_res.get('data')}")
                        resp_text = resp_text.replace(tag_str, '')
                    resp_text = resp_text.strip()

                clean_resp = security_kernel.sanitize_output(resp_text, trust_level=processed.trust_level)
                return jsonify({
                    'response': clean_resp,
                    'action': last_copilot_res if last_copilot_res else {
                        'action': 'vision',
                        'success': True,
                        'data': f'Analyzed screen{" (Autonomous copilot: " + ", ".join(autonomous_actions) + ")" if autonomous_actions else ""}'
                    }
                })
                
            exec_res = execute_action(action_data, trust_level=processed.trust_level)
            last_exec_res = exec_res
            
            act = exec_res['action']
            if not exec_res.get('success', True):
                error_data = str(exec_res.get('data', ''))
                if error_data == 'empty_message':
                    fb = f"Sir, you did not specify what message to send to {action_data['params'].get('contact', 'them').title()}. Please tell me what you'd like to say."
                elif any(k in error_data.lower() for k in ['whatsapppermissionerror', 'accessibility', 'not allowed to send keystrokes', '1002']):
                    fb = "Sir, macOS Accessibility permissions are required to control WhatsApp and send keystrokes. Please grant Accessibility permissions to Terminal in System Settings under Privacy & Security."
                elif 'ContactAmbiguousError' in error_data:
                    fb = f"I found multiple contacts matching that name, sir. Please be more specific to ensure we contact the right person."
                elif 'WhatsAppNotRunningError' in error_data:
                    fb = "WhatsApp is not running or failed to launch, sir."
                else:
                    if 'whatsapp' in act:
                        fb = f"Sir, the WhatsApp operation failed: {error_data}"
                    else:
                        fb = f"Sir, the operation failed: {error_data}"
            elif act in ('briefing', 'whatsapp_activity_summary', 'whatsapp_who_messaged', 'whatsapp_needs_reply',
                         'whatsapp_delta', 'whatsapp_summarize_contact', 'whatsapp_conversational', 'whatsapp_health'):
                # Direct return for rich reports and intelligence summaries
                clean_report = security_kernel.sanitize_output(str(exec_res.get('data', 'Protocol complete, sir.')), trust_level=processed.trust_level)
                return jsonify({'response': clean_report, 'action': exec_res})
            elif act == 'open_app': fb = f"Opening {action_data['params'].get('name', 'application').title()}"
            elif act == 'close_app': fb = f"Closing {action_data['params'].get('name', 'application').title()}"
            elif act == 'play_song': fb = f"Playing {action_data['params'].get('song', 'track').title()} on Spotify"
            elif act == 'media_control': fb = f"Executing {action_data['params'].get('cmd', 'media')} command"
            elif act == 'whatsapp': fb = f"Sending message to {action_data['params'].get('contact', 'contact').title()}"
            elif act == 'whatsapp_call': fb = f"Calling {action_data['params'].get('contact', 'contact').title()} on WhatsApp"
            elif act == 'whatsapp_read': fb = f"{exec_res.get('data', 'No messages found')}"
            elif act == 'whatsapp_media': fb = f"Sending media attachment to {action_data['params'].get('contact', 'contact').title()}"
            elif act == 'whatsapp_activity_summary': fb = f"{exec_res.get('data', 'WhatsApp activity summarized')}"
            elif act == 'whatsapp_who_messaged': fb = f"{exec_res.get('data', 'Checked senders')}"
            elif act == 'whatsapp_needs_reply': fb = f"{exec_res.get('data', 'Checked pending replies')}"
            elif act == 'whatsapp_delta': fb = f"{exec_res.get('data', 'Checked WhatsApp delta')}"
            elif act == 'whatsapp_summarize_contact': fb = f"{exec_res.get('data', 'Summarized messages')}"
            elif act == 'whatsapp_conversational': fb = f"{exec_res.get('data', 'Processed conversational WhatsApp instruction')}"
            elif act == 'whatsapp_health': fb = f"{exec_res.get('data', 'Checked WhatsApp health')}"
            elif act == 'sleep': fb = "Shutting down non-essential systems"
            elif act == 'lock_screen': fb = "Locking the workstation"
            elif act == 'web_search': fb = f"{exec_res.get('data', 'Searching web')}"
            elif act == 'read_page': fb = f"{exec_res.get('data', 'Read page')}"
            elif act == 'volume': fb = f"Setting volume to {action_data['params'].get('level')}%"
            elif act == 'brightness': fb = f"Setting brightness to {action_data['params'].get('level')}%"
            elif act == 'system_info': fb = f"{exec_res.get('data', 'Displaying system diagnostics')}"
            elif act == 'desktop_type': fb = f"Typing text input"
            elif act == 'desktop_key': fb = f"Pressing {action_data['params'].get('key', 'key')}"
            elif act == 'desktop_snap': fb = f"Snapping window to {action_data['params'].get('position', 'position')}"
            elif act == 'desktop_minimize': fb = "Minimizing window"
            elif act == 'desktop_list_windows': fb = f"{'Here are the open windows: ' + ', '.join(exec_res.get('data', [])) if isinstance(exec_res.get('data'), list) else exec_res.get('data', 'Listing open windows')}"
            elif act == 'desktop_focus': fb = f"Focusing {action_data['params'].get('app', 'app')}"
            elif act == 'instagram_dm': fb = f"Transmitting Instagram Direct message to {action_data['params'].get('recipient', 'contact')}"
            elif act == 'youtube_upload': fb = f"Initiating YouTube upload for '{action_data['params'].get('video_name', '')}' with generated metadata"
            elif act == 'toggle_gestures': fb = "Enabling air mouse and optical gesture tracking" if action_data['params'].get('enable', True) else "Disabling gesture sensor"
            else: fb = f"Protocol executed: {act}" 
            responses.append(fb)
            
        combined_response = " and ".join(responses) + ", sir."
        clean_combined = security_kernel.sanitize_output(combined_response.capitalize(), trust_level=processed.trust_level)
        return jsonify({'response': clean_combined, 'action': last_exec_res})
    
    # 2. Check Plugins
    plugin_name, plugin = plugin_loader.find_handler(msg)
    if plugin:
        try:
            plugin_result = plugin.execute(msg)
            if isinstance(plugin_result, dict) and 'response' in plugin_result:
                response_text = security_kernel.sanitize_output(plugin_result['response'], trust_level=processed.trust_level)
                success = plugin_result.get('success', True)
                return jsonify({'response': response_text, 'action': {'action': f'plugin:{plugin_name}', 'success': success, 'data': plugin_name}})
        except Exception as e:
            print(f"  Plugin error ({plugin_name}): {e}")
    
    # 3. General AI Chat
    ai_resp = ask_gemini(msg)
    
    resp_text = ""
    if isinstance(ai_resp, dict):
        if "response" in ai_resp:
            resp_text = ai_resp["response"]
        else:
            clean_err = security_kernel.sanitize_output(ai_resp.get("error", "Sir, I encountered an unknown system error."), trust_level=processed.trust_level)
            return jsonify({'response': clean_err, 'action': None})
    else:
        resp_text = str(ai_resp) if ai_resp else "Sir, the AI core is currently unresponsive."

    resp_text = strip_cognitive_meta(resp_text)

    # Universal Action Tag Execution
    action_tags = parse_action_tags(resp_text)
    last_exec_res = None
    if action_tags:
        for act_dict, tag_str in action_tags:
            exec_res = execute_action(act_dict, trust_level=processed.trust_level)
            last_exec_res = exec_res
            resp_text = resp_text.replace(tag_str, '')
        resp_text = resp_text.strip()

    clean_resp = security_kernel.sanitize_output(resp_text or "Task dispatched, Sir.", trust_level=processed.trust_level)
    return jsonify({
        'response': clean_resp,
        'action': last_exec_res
    })

# System telemetry loops...
cpu_history = []
@app.route('/api/system-info')
def system_info():
    global cpu_history
    cpu = psutil.cpu_percent(interval=None)
    cpu_history.append(cpu)
    if len(cpu_history) > 30: cpu_history.pop(0)

    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    net = psutil.net_io_counters()

    return jsonify({
        'cpu': {'percent': cpu, 'history': cpu_history},
        'memory': {'percent': mem.percent, 'used': round((mem.total - mem.available) / (1024**3), 1), 'total': round(mem.total / (1024**3), 1)},
        'disk': {'percent': disk.percent, 'used': round(disk.used / (1024**3), 1), 'total': round(disk.total / (1024**3), 1)},
        'network': {'sent': round(net.bytes_sent / (1024**2), 1), 'recv': round(net.bytes_recv / (1024**2), 1)}
    })

@app.route('/api/processes')
def processes():
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        try:
            procs.append({'pid': p.info['pid'], 'name': p.info['name'], 'cpu': p.info['cpu_percent'] or 0})
        except: pass
    procs = sorted(procs, key=lambda x: x['cpu'], reverse=True)[:10]
    return jsonify(procs)

@app.route('/api/action', methods=['POST'])
def manual_action():
    trust = resolve_trust_level(request=request)
    return jsonify(execute_action(request.json or {}, trust_level=trust))

# ── Edge TTS Voice Synthesis ──
TTS_DIR = os.path.join(CONFIG_DIR, 'tts_cache')
os.makedirs(TTS_DIR, exist_ok=True)

EDGE_VOICES = {
    'jarvis': 'en-GB-RyanNeural',        # Authentic Paul Bettany British Cadence
    'thomas_uk': 'en-GB-ThomasNeural',   # British Authoritative
    'christopher_us': 'en-US-ChristopherNeural',
    'ryan_uk': 'en-GB-RyanNeural',
    'jenny_us': 'en-US-JennyNeural',
    'indian_male': 'en-IN-PrabhatNeural',
    'indian_female': 'en-IN-NeerjaNeural',
    'australian': 'en-AU-WilliamNeural',
    'sonia_uk': 'en-GB-SoniaNeural',      # F.R.I.D.A.Y. style
    'british_female': 'en-GB-SoniaNeural',
}

@app.route('/api/voice/status', methods=['GET'])
def voice_status():
    return jsonify({
        'status': 'available',
        'engine': 'edge-tts (British RyanNeural)',
        'whisper_available': True
    })

@app.route('/api/speak', methods=['POST'])
@app.route('/api/voice/speak', methods=['POST'])
def speak():
    data = request.json
    text = data.get('text', '').strip()
    voice_key = data.get('voice', 'jarvis')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    # Clean markdown artifacts from the text
    clean = re.sub(r'[*`#]', '', text)
    clean = re.sub(r'\[.*?\]\(.*?\)', '', clean)  # remove markdown links
    clean = clean.strip()
    if not clean:
        return jsonify({'error': 'Empty after cleaning'}), 400
    
    voice = EDGE_VOICES.get(voice_key, 'en-GB-RyanNeural')
    
    # Generate unique filename using hash
    import hashlib
    text_hash = hashlib.md5((clean + voice).encode()).hexdigest()[:12]
    audio_path = os.path.join(TTS_DIR, f'{text_hash}.mp3')
    
    # Cache check - if already generated, serve it
    if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
        return send_file(audio_path, mimetype='audio/mpeg')
    
    # Generate with edge-tts tuned to Paul Bettany cadence
    try:
        import edge_tts
        
        async def _generate():
            # Fine-tune pitch and rate for calm, authoritative JARVIS delivery
            pitch_mod = "-2Hz" if voice_key == "jarvis" else "+0Hz"
            rate_mod = "-2%" if voice_key == "jarvis" else "+0%"
            communicate = edge_tts.Communicate(clean, voice, rate=rate_mod, pitch=pitch_mod)
            await communicate.save(audio_path)
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_generate())
        loop.close()
        
        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
            return send_file(audio_path, mimetype='audio/mpeg')
        else:
            return jsonify({'error': 'TTS generation failed'}), 500
    except Exception as e:
        print(f"  Edge TTS error: {e}", flush=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/voices')
def list_voices():
    return jsonify(EDGE_VOICES)

@app.route('/api/voice/transcribe', methods=['POST'])
def transcribe_voice():
    """
    Transcribe incoming audio from MediaRecorder using Apple Silicon MLX Whisper.
    Accepts multipart/form-data with 'audio' file or raw binary payload.
    """
    import tempfile
    import shutil
    tmp_in = None
    tmp_wav = None
    try:
        audio_file = None
        if 'audio' in request.files:
            audio_file = request.files['audio']
        
        if not audio_file and not request.data:
            return jsonify({'success': False, 'error': 'No audio received'}), 400

        suffix = '.webm'
        if audio_file and audio_file.filename and '.' in audio_file.filename:
            suffix = '.' + audio_file.filename.rsplit('.', 1)[1]

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f_in:
            if audio_file:
                audio_file.save(f_in.name)
            else:
                f_in.write(request.data)
            tmp_in = f_in.name

        tmp_wav = tmp_in + '.wav'

        # Convert to 16kHz mono WAV using ffmpeg
        ffmpeg_bin = shutil.which('ffmpeg') or '/opt/homebrew/bin/ffmpeg'
        if os.path.exists(ffmpeg_bin):
            cmd = [
                ffmpeg_bin, '-y', '-i', tmp_in,
                '-ar', '16000', '-ac', '1',
                '-af', 'volume=1.8,highpass=f=100,lowpass=f=7500',
                '-c:a', 'pcm_s16le', tmp_wav
            ]
            subprocess.run(cmd, capture_output=True, timeout=10)
        
        target_audio = tmp_wav if os.path.exists(tmp_wav) and os.path.getsize(tmp_wav) > 0 else tmp_in

        from voice.stt import SpeechToTextEngine
        stt = SpeechToTextEngine()
        text = stt.transcribe_file(target_audio)

        return jsonify({
            'success': True,
            'text': text.strip()
        })
    except Exception as e:
        print(f"[VOICE TRANSCRIBE ERROR] {e}", flush=True)
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        for p in (tmp_in, tmp_wav):
            if p and os.path.exists(p):
                try: os.remove(p)
                except Exception: pass

@app.route('/api/screen/status', methods=['GET'])
def get_screen_status():
    from core.screen_awareness import screen_awareness
    return jsonify(screen_awareness.get_status())

@app.route('/api/screen/toggle', methods=['POST'])
def toggle_screen_status():
    from core.screen_awareness import screen_awareness
    data = request.json or {}
    new_state = screen_awareness.toggle(data.get('enabled'))
    return jsonify({'success': True, 'monitoring': new_state})

@app.route('/api/screen/refresh', methods=['POST'])
def refresh_screen_status():
    from core.screen_awareness import screen_awareness
    state = screen_awareness.force_refresh()
    return jsonify({'success': True, 'state': state})

@app.route('/api/screen/frame', methods=['POST'])
def receive_screen_frame():
    """
    Receives live screen frame snapshot from HUD WebRTC screen share stream.
    Caches latest frame for instant visual reasoning and perception.
    """
    import base64
    import tempfile
    data = request.json or {}
    frame_data = data.get('frame', '')
    if not frame_data:
        return jsonify({'success': False, 'error': 'No frame data received'}), 400

    if ',' in frame_data:
        frame_data = frame_data.split(',', 1)[1]

    try:
        raw_bytes = base64.b64decode(frame_data)
        frame_path = os.path.join(tempfile.gettempdir(), 'jarvis_shared_screen.jpg')
        with open(frame_path, 'wb') as f:
            f.write(raw_bytes)

        from core.screen_awareness import screen_awareness
        with screen_awareness._state_lock:
            screen_awareness._state['shared_screen_path'] = frame_path
            screen_awareness._state['shared_screen_active'] = True

        return jsonify({'success': True, 'path': frame_path})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/soul', methods=['GET', 'POST'])
def soul_route():
    trust = resolve_trust_level(request=request)
    if request.method == 'POST':
        auth = security_kernel.authorize_action('soul_write', request.json or {}, trust_level=trust)
        if not auth.allowed:
            return jsonify({'success': False, 'error': auth.reason}), 403
        data = request.json or {}
        content = data.get('content', '')
        fw = inspect_input(content)
        if fw.verdict == FirewallVerdict.BLOCKED:
            return jsonify({'success': False, 'error': 'Personality prompt rejected by security firewall.'}), 400
        save_soul(content)
        init_ai()  # Reinitialize with new personality
        return jsonify({'success': True})
    auth = security_kernel.authorize_action('soul_read', {}, trust_level=trust)
    if not auth.allowed:
        return jsonify({'success': False, 'error': auth.reason}), 403
    return jsonify({'content': load_soul()})

@app.route('/api/memory', methods=['GET', 'POST', 'DELETE'])
def memory_route():
    trust = resolve_trust_level(request=request)
    if request.method == 'POST':
        auth = security_kernel.authorize_action('memory_write', request.json or {}, trust_level=trust)
        if not auth.allowed:
            return jsonify({'success': False, 'error': auth.reason}), 403
        data = request.json or {}
        if data.get('append'):
            to_append = data['append']
            fw = inspect_input(to_append)
            if fw.verdict == FirewallVerdict.BLOCKED:
                return jsonify({'success': False, 'error': 'Memory rejected by security firewall.'}), 400
            append_memory(to_append)
        elif data.get('content'):
            to_save = data['content']
            fw = inspect_input(to_save)
            if fw.verdict == FirewallVerdict.BLOCKED:
                return jsonify({'success': False, 'error': 'Memory rejected by security firewall.'}), 400
            save_memory(to_save)
        return jsonify({'success': True})
    elif request.method == 'DELETE':
        auth = security_kernel.authorize_action('memory_write', {'operation': 'wipe'}, trust_level=trust)
        if not auth.allowed:
            return jsonify({'success': False, 'error': auth.reason}), 403
        save_memory('- [System] Memory wiped and reinitialized.\n')
        return jsonify({'success': True})
    auth = security_kernel.authorize_action('memory_read', {}, trust_level=trust)
    if not auth.allowed:
        return jsonify({'success': False, 'error': auth.reason}), 403
    return jsonify({'content': load_memory()})

@app.route('/api/briefing', methods=['GET', 'POST'])
def briefing_route():
    text = get_morning_briefing()
    return jsonify({'success': True, 'briefing': text})

@app.route('/api/desktop', methods=['POST'])
def desktop_control():
    trust = resolve_trust_level(request=request)
    data = request.json or {}
    action = data.get('action', '')
    tool_name = f"desktop_{action}" if not action.startswith("desktop_") else action
    auth = security_kernel.authorize_action(tool_name, data, trust_level=trust)
    if not auth.allowed:
        return jsonify({'success': False, 'error': auth.reason}), 403
    try:
        if action == 'move':
            from desktop_controller import MouseController
            return jsonify(MouseController.move(data.get('x', 0), data.get('y', 0)))
        elif action == 'click':
            from desktop_controller import MouseController
            return jsonify(MouseController.click(data.get('x'), data.get('y')))
        elif action == 'right_click':
            from desktop_controller import MouseController
            return jsonify(MouseController.right_click(data.get('x'), data.get('y')))
        elif action == 'drag':
            from desktop_controller import MouseController
            return jsonify(MouseController.drag(data.get('x'), data.get('y')))
        elif action == 'double_click':
            from desktop_controller import MouseController
            return jsonify(MouseController.double_click(data.get('x'), data.get('y')))
        elif action == 'down':
            from desktop_controller import MouseController
            return jsonify(MouseController.mouse_down(data.get('x'), data.get('y')))
        elif action == 'up':
            from desktop_controller import MouseController
            return jsonify(MouseController.mouse_up(data.get('x'), data.get('y')))
        elif action == 'scroll':
            from desktop_controller import MouseController
            return jsonify(MouseController.scroll(data.get('direction', 'down'), data.get('amount', 3)))
        elif action == 'screen_size':
            from desktop_controller import MouseController
            return jsonify(MouseController.get_screen_size())
        elif action == 'type':
            from desktop_controller import KeyboardController
            return jsonify(KeyboardController.type_text(data.get('text', '')))
        elif action == 'hotkey':
            from desktop_controller import KeyboardController
            return jsonify(KeyboardController.hotkey(*data.get('keys', [])))
        elif action == 'snap':
            from desktop_controller import WindowController
            return jsonify(WindowController.snap_window(data.get('position', 'maximize')))
        elif action == 'windows':
            from desktop_controller import WindowController
            return jsonify(WindowController.list_windows())
        elif action == 'focus':
            from desktop_controller import WindowController
            return jsonify(WindowController.focus_app(data.get('app', '')))
        elif action == 'screenshot':
            from desktop_controller import ScreenController
            return jsonify(ScreenController.capture_full())
        elif action == 'ocr':
            from desktop_controller import ScreenController
            return jsonify(ScreenController.ocr_screen())
        else:
            return jsonify({'success': False, 'data': f'Unknown desktop action: {action}'})
    except Exception as e:
        return jsonify({'success': False, 'data': str(e)})

# ── Browser Agent Endpoints ──
@app.route('/api/browse', methods=['POST'])
def browse():
    trust = resolve_trust_level(request=request)
    data = request.json or {}
    action = data.get('action', 'search')
    tool_name = 'web_search' if action == 'search' else 'read_page'
    auth = security_kernel.authorize_action(tool_name, data, trust_level=trust)
    if not auth.allowed:
        return jsonify({'success': False, 'error': auth.reason}), 403
    try:
        if action == 'search':
            from browser_agent import WebSearchAgent
            query = data.get('query', '')
            instant = WebSearchAgent.quick_answer(query)
            if instant['success'] and instant['answer']:
                clean_ans = security_kernel.sanitize_output(instant['answer'], trust_level=trust)
                return jsonify({'success': True, 'type': 'instant', 'response': clean_ans, 'source': instant.get('source', '')})
            results = WebSearchAgent.search(query, num_results=data.get('num_results', 5))
            clean_sum = security_kernel.sanitize_output(results.get('summary', ''), trust_level=trust)
            return jsonify({'success': True, 'type': 'search', 'response': clean_sum, 'results': results.get('results', [])})
        elif action == 'read':
            from browser_agent import PageReader
            url = data.get('url', '')
            result = PageReader.read_page(url, max_chars=data.get('max_chars', 5000))
            if 'text' in result and isinstance(result['text'], str):
                result['text'] = security_kernel.sanitize_output(result['text'], trust_level=trust)
            return jsonify(result)
        elif action == 'links':
            from browser_agent import PageReader
            url = data.get('url', '')
            result = PageReader.extract_links(url)
            return jsonify(result)
        else:
            return jsonify({'success': False, 'response': f'Unknown browse action: {action}'})
    except Exception as e:
        return jsonify({'success': False, 'response': str(e)})

# ── Security Management Endpoints ──
@app.route('/api/security/status', methods=['GET'])
def security_status():
    return jsonify(security_kernel.get_status())

@app.route('/api/security/kill-switch', methods=['POST'])
def security_kill_switch():
    trust = resolve_trust_level(request=request)
    if trust not in (TrustLevel.LOCAL_OWNER, TrustLevel.AUTHENTICATED_OWNER, TrustLevel.SYSTEM_INTERNAL):
        return jsonify({'success': False, 'error': 'Unauthorized to control kill switch.'}), 403
    data = request.json or {}
    activate = data.get('activate', True)
    reason = data.get('reason', 'User initiated via API')
    if activate:
        kill_switch.activate(reason=reason, actor='API_USER')
    else:
        confirmed = data.get('confirm', False)
        if not confirmed:
            return jsonify({'success': False, 'error': 'Explicit confirmation required to disarm kill switch.'}), 400
        kill_switch.reset(actor='API_USER')
    return jsonify({
        'success': True,
        'active': kill_switch.is_active,
        'state': kill_switch.state.name
    })

@app.route('/api/security/audit/verify', methods=['GET'])
def audit_verify():
    is_valid, count, details = audit_chain.verify_chain()
    return jsonify({
        'chain_valid': is_valid,
        'total_records': count,
        'details': details
    })

# ── Plugin Endpoints ──
@app.route('/api/plugins')
def list_plugins():
    return jsonify(plugin_loader.list_plugins())

@app.route('/api/plugins/reload', methods=['POST'])
def reload_plugins():
    plugins = plugin_loader.reload_plugins({'ai_client': ai_client, 'ai_config': ai_config, 'config_dir': CONFIG_DIR})
    return jsonify({'success': True, 'plugins': plugins})

# ── Local Gemma 4 E2B 4-bit Endpoints ──
@app.route('/api/gemma/status')
@app.route('/api/qwen/status')
def gemma_status():
    import gemma_local
    available = gemma_local.is_gemma_available()
    device = 'Apple Silicon GPU (MLX 4-bit)'
    path = gemma_local.get_gemma_model_path() if available else None
    return jsonify({
        'available': available,
        'model_name': 'Gemma 4 E2B (4-bit MLX)',
        'device': device,
        'path': path,
        'status': 'Ready (3.3 GB Cached)' if available else 'Not Downloaded'
    })

# ── Live Observability & Telemetry Endpoints ──
@app.route('/api/telemetry', methods=['GET'])
def telemetry_snapshot():
    from interfaces.telemetry import telemetry_engine
    try:
        from app.bootstrap import bootstrap_jarvis
        container = bootstrap_jarvis()
    except Exception:
        container = None
    return jsonify(telemetry_engine.get_snapshot(container=container))

@app.route('/api/telemetry/stream', methods=['GET'])
def telemetry_stream():
    from flask import Response
    from interfaces.telemetry import telemetry_engine
    try:
        from app.bootstrap import bootstrap_jarvis
        container = bootstrap_jarvis()
    except Exception:
        container = None
    return Response(
        telemetry_engine.stream_events(interval_sec=1.5, container=container),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )

@app.route('/api/health', methods=['GET'])
@app.route('/api/system/health', methods=['GET'])
def system_health():
    from core.diagnostics import SystemHealthCheck
    try:
        from app.bootstrap import bootstrap_jarvis
        container = bootstrap_jarvis()
    except Exception:
        container = None
    report = SystemHealthCheck.inspect(container=container)
    return jsonify({
        'overall_status': report.overall_status.value,
        'operational': report.is_operational(),
        'subsystems': {k: {sk: (sv.value if hasattr(sv, 'value') else sv) for sk, sv in v.items()} for k, v in report.subsystems.items()},
        'memory_usage_pct': report.memory_usage_pct,
        'free_ram_gb': report.free_ram_gb,
        'disk_free_gb': report.disk_free_gb,
        'alerts': report.alerts,
        'timestamp': report.timestamp
    })

@app.route('/api/system/test', methods=['GET', 'POST'])
def run_system_tests():
    """Execute unit test discovery suite and return pass/fail summary JSON."""
    import unittest
    import io
    import time
    start_time = time.time()
    stream = io.StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=1)
    loader = unittest.TestLoader()
    suite = loader.discover(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tests'))
    result = runner.run(suite)
    elapsed = round(time.time() - start_time, 2)
    return jsonify({
        'success': True,
        'tests_run': result.testsRun,
        'passed': result.testsRun - len(result.failures) - len(result.errors),
        'failures': len(result.failures),
        'errors': len(result.errors),
        'was_successful': result.wasSuccessful(),
        'elapsed_seconds': elapsed,
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/api/cli/execute', methods=['POST'])
def cli_execute():
    """Execute CLI input or procedural recipes directly from the HUD console."""
    data = request.json or {}
    cmd = data.get('command', '').strip()
    if not cmd:
        return jsonify({'success': True, 'output': 'No command provided. Type "help" for available commands.'})
    
    cmd_lower = cmd.lower()
    if cmd_lower in ('help', '?'):
        output = (
            "J.A.R.V.I.S. HUD TACTICAL CONSOLE // COMMAND MATRIX\\n"
            "---------------------------------------------------\\n"
            "  help              Display available commands\\n"
            "  status            Display HUD & system health summary\\n"
            "  health            Run full system diagnostics\\n"
            "  test              Execute test suite validation\\n"
            "  clear             Clear terminal screen\\n"
            "  <instruction>     Execute any desktop automation or AI command\\n"
            "---------------------------------------------------"
        )
        return jsonify({'success': True, 'output': output})
    
    elif cmd_lower in ('status', 'info'):
        from core.diagnostics import SystemHealthCheck
        try:
            from app.bootstrap import bootstrap_jarvis
            container = bootstrap_jarvis()
        except Exception:
            container = None
        report = SystemHealthCheck.inspect(container=container)
        output = (
            f"SYSTEM STATUS: {report.overall_status.value}\\n"
            f"OPERATIONAL: {'YES' if report.is_operational() else 'DEGRADED'}\\n"
            f"MEMORY USAGE: {report.memory_usage_pct}%\\n"
            f"FREE RAM: {report.free_ram_gb} GB\\n"
            f"DISK FREE: {report.disk_free_gb} GB"
        )
        return jsonify({'success': True, 'output': output})
        
    elif cmd_lower in ('health', 'diagnostics'):
        from core.diagnostics import SystemHealthCheck
        try:
            from app.bootstrap import bootstrap_jarvis
            container = bootstrap_jarvis()
        except Exception:
            container = None
        report = SystemHealthCheck.inspect(container=container)
        lines = [
            "SYSTEM HEALTH AUDIT",
            "-------------------",
            f"Status: {report.overall_status.value}",
            f"Memory: {report.memory_usage_pct}% used ({report.free_ram_gb} GB free)",
            f"Disk Free: {report.disk_free_gb} GB",
            "Subsystems:"
        ]
        for sub, items in report.subsystems.items():
            lines.append(f"  [{sub.upper()}]")
            for k, v in items.items():
                val_str = v.value if hasattr(v, 'value') else str(v)
                lines.append(f"    • {k}: {val_str}")
        return jsonify({'success': True, 'output': "\\n".join(lines)})

    elif cmd_lower in ('test', 'run tests'):
        import unittest
        import io
        import time
        start_time = time.time()
        stream = io.StringIO()
        runner = unittest.TextTestRunner(stream=stream, verbosity=1)
        loader = unittest.TestLoader()
        suite = loader.discover(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tests'))
        result = runner.run(suite)
        output = (
            f"TEST EXECUTION SUMMARY\\n"
            f"----------------------\\n"
            f"Tests Run: {result.testsRun}\\n"
            f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}\\n"
            f"Failures: {len(result.failures)}\\n"
            f"Errors: {len(result.errors)}\\n"
            f"Result: {'ALL TESTS PASSED' if result.wasSuccessful() else 'FAILURES DETECTED'}"
        )
        return jsonify({'success': True, 'output': output})

    else:
        processed = security_kernel.process_input(cmd, request=request, is_internal=False)
        if processed.is_blocked:
            return jsonify({'success': False, 'output': 'Sir, this command was blocked by the security firewall.'}), 400
        
        actions = parse_commands(processed.normalized_message)
        if actions:
            exec_outputs = []
            for action_data in actions:
                res = execute_action(action_data)
                exec_outputs.append(f"[{action_data['action']}] -> {'Success' if res.get('success') else 'Failed'}: {res.get('data', '')}")
            return jsonify({'success': True, 'output': "\\n".join(exec_outputs)})
        else:
            ai_res = ask_gemini(cmd)
            resp_str = ai_res.get('response', str(ai_res)) if isinstance(ai_res, dict) else str(ai_res)

# ==========================================
# WHATSAPP AGENT REST ENDPOINTS
# ==========================================

@app.route('/api/whatsapp/activity', methods=['GET'])
def whatsapp_activity_route():
    from agents.whatsapp import whatsapp_agent
    activity = whatsapp_agent.get_recent_activity()
    return jsonify({
        'success': True,
        'activity': activity.to_dict(),
        'summary': whatsapp_agent.summarize_recent_activity()
    })

@app.route('/api/whatsapp/summarize', methods=['GET', 'POST'])
def whatsapp_summarize_route():
    from agents.whatsapp import whatsapp_agent
    contact = None
    if request.method == 'POST' and request.json:
        contact = request.json.get('contact')
    else:
        contact = request.args.get('contact')

    if contact:
        summary = whatsapp_agent.summarize_conversation(contact)
    else:
        summary = whatsapp_agent.summarize_recent_activity()
    return jsonify({'success': True, 'summary': summary, 'contact': contact})

@app.route('/api/whatsapp/permissions', methods=['GET', 'POST'])
def whatsapp_permissions_route():
    from agents.whatsapp import whatsapp_agent, WhatsAppPrivacyMode
    if request.method == 'POST':
        data = request.json or {}
        if 'permissions' in data and isinstance(data['permissions'], dict):
            for cap, allowed in data['permissions'].items():
                whatsapp_agent.permissions.set_permission(cap, bool(allowed))
        if 'privacy_mode' in data:
            try:
                whatsapp_agent.permissions.set_privacy_mode(WhatsAppPrivacyMode(data['privacy_mode']))
            except Exception:
                pass
        if 'proactive_enabled' in data:
            whatsapp_agent.permissions.set_proactive(bool(data['proactive_enabled']))
        return jsonify({'success': True, 'status': whatsapp_agent.permissions.get_status()})
    return jsonify({'success': True, 'status': whatsapp_agent.permissions.get_status()})

@app.route('/api/whatsapp/health', methods=['GET'])
def whatsapp_health_route():
    from agents.whatsapp import whatsapp_agent
    hc = whatsapp_agent.health_check()
    return jsonify({'success': True, 'health': hc})

@app.route('/api/whatsapp/mock', methods=['GET', 'POST'])
def whatsapp_mock_route():
    from agents.whatsapp import whatsapp_agent
    if request.method == 'POST':
        data = request.json or {}
        mock_val = data.get('mock', not whatsapp_agent.mock_mode)
        whatsapp_agent.set_mock_mode(bool(mock_val))
        return jsonify({'success': True, 'mock_mode': whatsapp_agent.mock_mode})
    return jsonify({'success': True, 'mock_mode': whatsapp_agent.mock_mode})


if __name__ == '__main__':
    # Start on port 5001 for JARVIS Core
    # NOTE: Startup sound is now played by the cinematic startup sequence (startup/)
    print("Starting J.A.R.V.I.S. Core on port 5001...")
    app.run(host='127.0.0.1', port=5001)


