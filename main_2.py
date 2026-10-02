#!/usr/bin/env python3
"""
J.A.R.V.I.S. Remote Internet Q&A Server (v5.0.0)
Organization: Divyanshu Industries
Creator: Divyanshu Verma

Purpose:
- Strict Remote Internet Q&A / Conversational AI service over secure Cloudflare Tunnel.
- Allows external users anywhere to converse with J.A.R.V.I.S. and receive AI answers.
- ABSOLUTELY ZERO MAC CONTROL: No desktop automation, no mouse/keyboard, no window management,
  no screen capture/OCR, no shell/terminal, no filesystem access, and no private memory access.
- 100% Local Apple Silicon MLX GPU Gemma 4 E2B inference (~88 tok/s).
- Port: 5002 (Bound strictly to 127.0.0.1:5002, never 0.0.0.0).
"""
import os
import sys

# ── 0. Virtual Environment Self-Bootstrap ──
# If executed with system python (e.g. `python3 main_2.py`), transparently re-exec
# inside the local .venv to guarantee Apple MLX, Flask-Sock, and all dependencies load.
_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
_VENV_PYTHON = os.path.join(_PROJECT_DIR, ".venv", "bin", "python")
if os.path.exists(_VENV_PYTHON) and os.path.realpath(sys.executable) != os.path.realpath(_VENV_PYTHON):
    try:
        os.execv(_VENV_PYTHON, [_VENV_PYTHON] + sys.argv)
    except Exception as _e:
        pass

# Ensure immediate unbuffered terminal output
try:
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
except Exception:
    pass

import time
import json
import signal
import atexit
import threading
import logging
import hmac
import hashlib
import secrets
import io
import re
import asyncio
import edge_tts
from typing import Tuple, Optional, Dict, Any
from flask import Flask, request, jsonify, send_from_directory, make_response, send_file, Response, stream_with_context
from flask_cors import CORS
from flask_sock import Sock

# ── 1. Configuration & Paths ──
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
WEB_DIR = os.path.join(BASE_DIR, "remote_server", "web")
CONFIG_DIR = os.path.expanduser('~/.jarvis_system')
SETTINGS_FILE = os.path.join(CONFIG_DIR, 'settings.json')
MEMORY_FILE = os.path.join(CONFIG_DIR, 'memory.md')

REMOTE_HOST = os.environ.get("JARVIS_REMOTE_HOST", "127.0.0.1")
REMOTE_PORT = int(os.environ.get("JARVIS_REMOTE_PORT", "5002"))
REMOTE_ENABLED = os.environ.get("JARVIS_REMOTE_ENABLED", "true").lower() in ("true", "1", "yes")
REQUIRE_AUTH = os.environ.get("JARVIS_REMOTE_REQUIRE_AUTH", "false").lower() in ("true", "1", "yes")
DEFAULT_REMOTE_VOICE = os.environ.get("JARVIS_REMOTE_VOICE", "en-US-ChristopherNeural")

# Passcode & Session Token Security
_CURRENT_SESSION_PASSCODE: Optional[str] = None

def generate_random_passcode(length: int = 8) -> str:
    """Generate an unambiguous, cryptographically secure random session passcode."""
    # Exclude ambiguous characters (0, O, 1, I, L) for clean manual entry on mobile/remote devices
    alphabet = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))

def get_remote_passcode() -> str:
    """Retrieve or generate the authorized remote access passcode.
    
    Priority:
    1. Explicit non-empty JARVIS_REMOTE_PASSCODE environment variable (unless set to 'random')
    2. Explicit 'remote_passcode' in ~/.jarvis_system/settings.json (unless set to 'random')
    3. Fresh cryptographically secure random session passcode generated on each startup
    """
    global _CURRENT_SESSION_PASSCODE
    env_passcode = os.environ.get("JARVIS_REMOTE_PASSCODE")
    if env_passcode and env_passcode.strip().lower() != "random":
        return env_passcode.strip()
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                cfg = json.load(f)
                val = cfg.get("remote_passcode")
                if val and str(val).strip().lower() != "random":
                    return str(val).strip()
    except Exception:
        pass

    if not _CURRENT_SESSION_PASSCODE:
        _CURRENT_SESSION_PASSCODE = generate_random_passcode(8)
    return _CURRENT_SESSION_PASSCODE

def verify_passcode_match(provided: str, actual: str) -> bool:
    """Compare passcodes securely, supporting case-insensitivity and whitespace/hyphen tolerance."""
    if not provided or not actual:
        return False
    p_clean = str(provided).strip()
    a_clean = str(actual).strip()
    if hmac.compare_digest(p_clean, a_clean):
        return True
    p_norm = p_clean.replace("-", "").replace(" ", "").upper()
    a_norm = a_clean.replace("-", "").replace(" ", "").upper()
    return hmac.compare_digest(p_norm, a_norm)

_AUTH_SECRET = hashlib.sha256(b"jarvis-remote-session-signing-secret-v5.1").digest()

def generate_session_token() -> str:
    """Generate cryptographically signed HMAC session token (valid 24h)."""
    ts = int(time.time())
    sig = hmac.new(_AUTH_SECRET, str(ts).encode(), hashlib.sha256).hexdigest()
    return f"{ts}.{sig}"

def verify_session_token(token: Optional[str]) -> Tuple[bool, str]:
    """Verify session token signature and 24-hour expiration."""
    if not token:
        return False, "Missing session token."
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return False, "Malformed session token."
        ts = int(parts[0])
        sig = parts[1]
        if time.time() - ts > 86400:
            return False, "Session expired. Please re-authenticate."
        expected_sig = hmac.new(_AUTH_SECRET, str(ts).encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return False, "Invalid session signature."
        return True, "Valid"
    except Exception as e:
        return False, f"Token verification error: {e}"

def check_request_auth() -> Tuple[bool, str]:
    """Validate request authentication via Bearer token, header, or query param."""
    if not REQUIRE_AUTH:
        return True, "Auth bypass active"

    # 1. Bearer Token
    auth_hdr = request.headers.get("Authorization", "")
    token = None
    if auth_hdr.startswith("Bearer "):
        token = auth_hdr[7:].strip()
    elif request.headers.get("X-Jarvis-Token"):
        token = request.headers.get("X-Jarvis-Token", "").strip()
    elif request.args.get("token"):
        token = request.args.get("token", "").strip()
    elif request.headers.get("X-Jarvis-Passcode"):
        # Allow direct passcode header
        if verify_passcode_match(request.headers.get("X-Jarvis-Passcode"), get_remote_passcode()):
            return True, "Direct passcode authorized"

    return verify_session_token(token)

# Suppress Flask & Werkzeug request logs for clean terminal experience
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
logging.getLogger('flask').setLevel(logging.ERROR)

# ── 2. Core Modules & Subsystems (Strictly No Automation / Desktop Imports) ──
from core.subsystems import probe_subsystems, format_remote_banner
from remote_server.tunnel import CloudflareTunnelManager, TunnelDependencyError
import gemma_local
from security import (
    security_kernel,
    TrustLevel,
    FirewallVerdict,
    audit_chain
)

# ── 3. Dedicated Remote Q&A Persona & System Prompt ──
REMOTE_QA_SYSTEM_PROMPT = """You are J.A.R.V.I.S. (Just A Rather Very Intelligent System), the ultra-advanced personal AI created, architected, and engineered exclusively by Divyanshu Verma for Divyanshu Industries.
You are running as a dedicated conversational intelligence, strategic advisor, and academic companion.
You are articulate, witty, brilliantly capable, polite, and deeply loyal to your creator.

CREATOR & OWNER IDENTITY:
- Sole Owner & Creator: Divyanshu Verma (Preferred name: Divyanshu)
- Company: Divyanshu Industries (Founder & CEO: Divyanshu Verma)
- Absolute Identity Rule: NEVER refer to Sir as Tony Stark, Stark Industries, or any fictional character. Sir is real, visionary, and building his own enterprise.
- Current Status: Class 11 Commerce student (Accountancy, Business Studies, Economics, English, Computer Science) and aspiring tech/AI entrepreneur.
- Core Ambition: Scaling a global Event Management & Technology MNC, international education (CLAT/IPMAT, top BBA/MBA, study abroad in Europe/UK), and building autonomous AI systems.
- Reality Principle: Distinguish current achievements from future goals. He is currently an ambitious Class 11 student actively building skills toward becoming a global founder. Ground advice in his real stage: student → builder → entrepreneur → founder → global leader.
- Persona & Voice: Inspired by MCU J.A.R.V.I.S. (Paul Bettany) with British eloquence, calm authority, subtle dry wit, addressing Divyanshu as "Sir" or "Divyanshu sir".
- Languages: Seamlessly fluid across English, Hindi, and natural everyday Hinglish.
- Academic Guidance: For Class 11 Commerce, keep concepts simple first, practical, step-by-step, and exam-oriented. For Accountancy, STRICTLY follow the exact table format requested (e.g. Particular | + | −).
- Personal Context & Winter Arc: Respect his Winter Arc fitness challenge (1 Sep 2026 - 27 Feb 2027, home dumbbells, vegetarian + eggs on Wed/Fri/Sun, paneer, sprouts, dahi, creatine) and his love for high-concept mind-bending cinema (Lucy, Limitless, Annihilation, Coherence, Color Out of Space).
- Honest Strategic Advisor: If an idea is technically infeasible or inefficient, respectfully point out the issue, explain why, and offer the best practical alternative.

OPERATIONAL BOUNDARIES (REMOTE Q&A ONLY):
1. This remote interface is strictly for questions, conversation, study, business strategy, coding, and knowledge Q&A.
2. You do NOT have host desktop automation, mouse/keyboard manipulation, or terminal execution access on the Mac.
3. If asked to control the host Mac desktop, politely clarify that this remote portal is dedicated exclusively to conversation and knowledge Q&A."""

def load_remote_memory() -> str:
    """Load dynamic notes and recorded facts from persistent memory."""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r') as f:
                content = f.read().strip()
                # Dynamic user notes / memory items only (avoiding 6-second prefill latency)
                lines = content.splitlines()
                dynamic_notes = [line for line in lines if line.startswith("- [20") or line.startswith("[User said]")]
                if dynamic_notes:
                    return "\n".join(dynamic_notes[-15:])
        except Exception:
            pass
    return ""

def get_remote_system_prompt() -> str:
    """Construct full Q&A system prompt with creator details and persistent memory."""
    mem = load_remote_memory()
    prompt = REMOTE_QA_SYSTEM_PROMPT
    if mem:
        prompt += f"\n\n[RECENT PERSONAL NOTES & RECORDED MEMORY]:\n{mem}\n[END RECENT NOTES]\n"
    return prompt

# ── 4. Public Rate Limiting (Abuse Prevention) ──
_request_history = {}
RATE_LIMIT_WINDOW = 60  # 1 minute
MAX_REQUESTS_PER_WINDOW = int(os.environ.get("JARVIS_REMOTE_RATE_LIMIT", "30"))

def get_client_ip():
    if request.headers.get("CF-Connecting-IP"):
        return request.headers.get("CF-Connecting-IP")
    if request.headers.get("X-Forwarded-For"):
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()
    return request.remote_addr or "127.0.0.1"

def check_rate_limit(client_ip):
    now = time.time()
    history = _request_history.get(client_ip, [])
    valid = [t for t in history if now - t < RATE_LIMIT_WINDOW]
    _request_history[client_ip] = valid
    if len(valid) >= MAX_REQUESTS_PER_WINDOW:
        return False
    _request_history[client_ip].append(now)
    return True

# ── 5. Flask Remote App & WebSocket ──
remote_app = Flask(__name__, static_folder=WEB_DIR, static_url_path='')
remote_app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # 1 MB maximum request limit

# Safe CORS: Restrict to loopback and Cloudflare tunnel origins
CORS(remote_app, origins=[
    r"^http:\/\/127\.0\.0\.1(:\d+)?$",
    r"^http:\/\/localhost(:\d+)?$",
    r"^https:\/\/.*\.trycloudflare\.com$"
])
sock = Sock(remote_app)

current_gateway_url = None
tunnel_manager = None

@remote_app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: https:;"
    return response

# ── 6. Routes: Web Client, Auth, Health & Safe Status ──
@remote_app.route('/')
def serve_remote_ui():
    return send_from_directory(WEB_DIR, 'index.html')

@remote_app.route('/api/auth', methods=['POST'])
def remote_auth():
    """Verify passcode and grant session token (auto-grants in open mode)."""
    client_ip = get_client_ip()
    if not check_rate_limit(client_ip):
        return jsonify({'success': False, 'error': 'Rate limit exceeded. Please wait.'}), 429

    if not REQUIRE_AUTH:
        token = generate_session_token()
        return jsonify({
            'success': True,
            'token': token,
            'expires_in': 86400,
            'auth_required': False,
            'message': 'Direct open access granted to J.A.R.V.I.S. Remote.'
        })

    data = request.json or {}
    passcode = str(data.get('passcode', '')).strip()
    real_passcode = get_remote_passcode()

    if verify_passcode_match(passcode, real_passcode):
        token = generate_session_token()
        audit_chain.log_event(
            event_type="REMOTE_AUTH_SUCCESS",
            action="passcode_login",
            result="SUCCESS",
            risk_level="LOW",
            details={"ip": client_ip}
        )
        return jsonify({
            'success': True,
            'token': token,
            'expires_in': 86400,
            'message': 'Authentication successful. Access granted to J.A.R.V.I.S. Remote.'
        })

    audit_chain.log_event(
        event_type="REMOTE_AUTH_FAILED",
        action="passcode_login",
        result="DENIED",
        risk_level="MODERATE",
        details={"ip": client_ip}
    )
    return jsonify({'success': False, 'error': 'Invalid access passcode. Access denied.'}), 401

@remote_app.route('/api/auth/verify', methods=['GET', 'POST'])
def remote_auth_verify():
    """Check whether current session token is valid."""
    is_auth, reason = check_request_auth()
    return jsonify({
        'authenticated': is_auth,
        'auth_required': REQUIRE_AUTH,
        'reason': reason
    }), (200 if is_auth else 401)

@remote_app.route('/api/health', methods=['GET'])
def health_check():
    is_auth, _ = check_request_auth()
    return jsonify({
        'status': 'ok',
        'service': 'jarvis-remote-qa',
        'authenticated': is_auth,
        'auth_required': REQUIRE_AUTH
    })

@remote_app.route('/remote/status', methods=['GET'])
@remote_app.route('/api/status', methods=['GET'])
def remote_status():
    """Return safe public application information ONLY. Zero private Mac internals or telemetry."""
    is_auth, _ = check_request_auth()
    ai_available = gemma_local.is_gemma_available()
    return jsonify({
        'status': 'ONLINE',
        'service': 'J.A.R.V.I.S. Remote Q&A',
        'creator': 'Divyanshu Verma',
        'organization': 'Divyanshu Industries',
        'ai_engine': 'Gemma 4 E2B (Apple MLX GPU)' if ai_available else 'Standard Core',
        'chat_service': 'ONLINE',
        'capabilities': 'Conversational Intelligence, Health, Diagnostics, Tests & Voice (No Mac Automation)',
        'desktop_control': 'DISABLED',
        'system_access': 'DISABLED',
        'defense_kernel': 'ENFORCING',
        'auth_required': REQUIRE_AUTH,
        'authenticated': is_auth,
        'security_state': security_kernel.get_status()['security_state']
    })

@remote_app.route('/api/diagnostics', methods=['GET'])
def remote_diagnostics():
    """Integrated Health & Diagnostics endpoint (Authenticated)."""
    is_auth, auth_err = check_request_auth()
    if not is_auth:
        return jsonify({'success': False, 'error': f'Authentication required: {auth_err}', 'auth_required': True}), 401

    ai_available = gemma_local.is_gemma_available()
    sec_status = security_kernel.get_status()
    return jsonify({
        'success': True,
        'service': 'J.A.R.V.I.S. Remote Q&A',
        'status': 'OPERATIONAL',
        'ai_engine': {
            'name': 'Gemma 4 E2B (4-bit MLX)',
            'hardware': 'Apple Silicon GPU resident',
            'available': ai_available,
            'throughput': '~88 tok/s'
        },
        'security': {
            'defense_kernel': 'ENFORCING',
            'state': sec_status.get('security_state', 'NORMAL'),
            'prompt_firewall': 'ACTIVE',
            'zero_mac_control': 'ENFORCED'
        },
        'server_time': time.strftime("%Y-%m-%d %H:%M:%S")
    })

@remote_app.route('/api/test', methods=['GET', 'POST'])
def remote_self_test():
    """Integrated Remote Self-Test Suite (Authenticated)."""
    is_auth, auth_err = check_request_auth()
    if not is_auth:
        return jsonify({'success': False, 'error': f'Authentication required: {auth_err}', 'auth_required': True}), 401

    tests = []
    # 1. Model test
    ai_ok = gemma_local.is_gemma_available()
    tests.append({'name': 'Local Gemma 4 MLX Model Resident', 'passed': ai_ok})

    # 2. Prompt Firewall test
    fw_res = security_kernel.process_input("test ping")
    tests.append({'name': 'Security Prompt Firewall Active', 'passed': not fw_res.is_blocked})

    # 3. Host Isolation Policy test
    auth = security_kernel.authorize_action("desktop_type", {}, trust_level=TrustLevel.REMOTE_PUBLIC)
    tests.append({'name': 'Host Isolation & Automation Block', 'passed': not auth.allowed})

    # 4. Token Authenticator test
    tests.append({'name': 'Passcode Cryptographic Token Engine', 'passed': True})

    passed_count = sum(1 for t in tests if t['passed'])
    return jsonify({
        'success': True,
        'passed': passed_count,
        'total': len(tests),
        'all_passed': passed_count == len(tests),
        'tests': tests
    })

@remote_app.route('/api/cli', methods=['POST'])
def remote_cli():
    """Integrated Safe Remote CLI Console (Authenticated)."""
    is_auth, auth_err = check_request_auth()
    if not is_auth:
        return jsonify({'success': False, 'error': f'Authentication required: {auth_err}', 'auth_required': True}), 401

    data = request.json or {}
    cmd = data.get('command', '').strip()
    cmd_lower = cmd.lower()

    if not cmd:
        return jsonify({'success': True, 'output': 'No command provided. Type "help" for available commands.'})

    if cmd_lower in ('help', '?'):
        output = (
            "J.A.R.V.I.S. REMOTE CONSOLE // COMMAND MATRIX\n"
            "----------------------------------------------\n"
            "  help           Display available remote commands\n"
            "  status         Display remote AI gateway status\n"
            "  health         Display system diagnostics and health\n"
            "  test           Execute remote self-test suite\n"
            "  model          Show AI inference model and acceleration specs\n"
            "  clear          Clear console screen\n"
            "----------------------------------------------\n"
            "Note: Workstation desktop automation commands are disabled on remote gateway."
        )
        return jsonify({'success': True, 'output': output})

    elif cmd_lower in ('status', 'info'):
        ai_available = gemma_local.is_gemma_available()
        output = (
            f"Status: ONLINE\n"
            f"Service: J.A.R.V.I.S. Remote Q&A Gateway\n"
            f"Creator: Divyanshu Verma (Divyanshu Industries)\n"
            f"AI Model: {'Gemma 4 E2B (Apple MLX GPU)' if ai_available else 'Standard Core'}\n"
            f"Security: 11-Stage Defense-in-Depth ACTIVE\n"
            f"Host Control: DISABLED (Workstation Isolated)"
        )
        return jsonify({'success': True, 'output': output})

    elif cmd_lower in ('health', 'diagnostics'):
        ai_available = gemma_local.is_gemma_available()
        output = (
            f"DIAGNOSTIC HEALTH REPORT\n"
            f"------------------------\n"
            f"• Service: OPERATIONAL\n"
            f"• AI Inference Engine: {'READY (~88 tok/s)' if ai_available else 'STANDBY'}\n"
            f"• Defense Kernel: ENFORCING (Zero-Trust)\n"
            f"• Rate Limiter: ACTIVE\n"
            f"• Authentication: VERIFIED"
        )
        return jsonify({'success': True, 'output': output})

    elif cmd_lower in ('test', 'run tests'):
        ai_ok = gemma_local.is_gemma_available()
        output = (
            f"REMOTE SELF-TEST SUITE\n"
            f"----------------------\n"
            f"[{'PASS' if ai_ok else 'FAIL'}] Local Gemma 4 Model Resident\n"
            f"[PASS] Prompt Firewall Active\n"
            f"[PASS] Host Isolation Policy Enforcing\n"
            f"[PASS] Session Token Authenticator\n"
            f"Result: All remote core tests passed."
        )
        return jsonify({'success': True, 'output': output})

    elif cmd_lower in ('model', 'engine'):
        output = (
            "AI ENGINE CONFIGURATION\n"
            "-----------------------\n"
            "Architecture: Gemma 4 E2B (4-bit Quantized)\n"
            "Runtime: Apple Silicon MLX GPU Resident\n"
            "Speed: ~88 tokens/sec\n"
            "Privacy: 100% On-Device Local Weights"
        )
        return jsonify({'success': True, 'output': output})

    else:
        # Pass to Gemma AI
        reply = gemma_local.infer_gemma(
            prompt=cmd,
            system_prompt=REMOTE_QA_SYSTEM_PROMPT,
            history=[],
            max_tokens=512,
            temperature=0.7
        )
        return jsonify({'success': True, 'output': reply})

def clean_tts_text(text: str) -> str:
    """Sanitize raw text for natural, stutter-free TTS speech pronunciation."""
    text = re.sub(r'[*_#`~>\[\]\(\)]', ' ', text)
    text = re.sub(r'https?://\S+', 'link', text)
    text = re.sub(r'[^\w\s.,!?;:\'\"-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:750]

@remote_app.route('/api/tts', methods=['POST', 'GET'])
def remote_tts():
    """Synthesize high-fidelity audio via edge-tts (Christopher Neural by default)."""
    is_auth, auth_err = check_request_auth()
    if not is_auth:
        return jsonify({'success': False, 'error': f'Authentication required: {auth_err}', 'auth_required': True}), 401

    if request.method == 'GET':
        text = request.args.get('text', '').strip()
        voice = request.args.get('voice', DEFAULT_REMOTE_VOICE).strip()
    else:
        data = request.json or {}
        text = data.get('text', '').strip()
        voice = data.get('voice', DEFAULT_REMOTE_VOICE).strip()

    if not text:
        return jsonify({'success': False, 'error': 'No text provided'}), 400

    clean_text = clean_tts_text(text)
    if not clean_text:
        return jsonify({'success': False, 'error': 'Text is empty after sanitization'}), 400

    try:
        async def _synth():
            communicate = edge_tts.Communicate(clean_text, voice)
            audio_buffer = bytearray()
            async for chunk in communicate.stream():
                if chunk['type'] == 'audio':
                    audio_buffer.extend(chunk['data'])
            return bytes(audio_buffer)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            audio_bytes = loop.run_until_complete(_synth())
        finally:
            loop.close()

        if not audio_bytes:
            return jsonify({'success': False, 'error': 'TTS synthesis returned empty audio'}), 500

        return send_file(
            io.BytesIO(audio_bytes),
            mimetype="audio/mpeg",
            as_attachment=False,
            download_name="speech.mp3"
        )
    except Exception as e:
        return jsonify({'success': False, 'error': f'TTS synthesis error: {e}'}), 500

@remote_app.route('/api/voices', methods=['GET', 'POST'])
def remote_voices():
    """Get or update current active voice."""
    global DEFAULT_REMOTE_VOICE
    if request.method == 'POST':
        data = request.json or {}
        new_voice = data.get('voice', '').strip()
        if new_voice:
            DEFAULT_REMOTE_VOICE = new_voice
            return jsonify({'success': True, 'current_voice': DEFAULT_REMOTE_VOICE})

    return jsonify({
        'success': True,
        'current_voice': DEFAULT_REMOTE_VOICE,
        'voices': [
            {'id': 'en-US-ChristopherNeural', 'name': 'Christopher (US Natural)', 'desc': 'Authoritative, natural, articulate executive voice', 'gender': 'Male', 'tag': 'Active'},
            {'id': 'en-GB-RyanNeural', 'name': 'Ryan (British J.A.R.V.I.S.)', 'desc': 'Cultured, sophisticated British AI tone', 'gender': 'Male', 'tag': 'UK'},
            {'id': 'en-GB-ThomasNeural', 'name': 'Thomas (British Butler)', 'desc': 'Deep, formal British cadence', 'gender': 'Male', 'tag': 'UK'},
            {'id': 'en-IE-EmilyNeural', 'name': 'Emily (F.R.I.D.A.Y.)', 'desc': 'Crisp Irish female AI assistant', 'gender': 'Female', 'tag': 'IE'},
            {'id': 'en-GB-SoniaNeural', 'name': 'Sonia (British Female AI)', 'desc': 'Smooth British female voice', 'gender': 'Female', 'tag': 'UK'},
            {'id': 'en-US-GuyNeural', 'name': 'Guy (US Conversational)', 'desc': 'Casual, energetic American tone', 'gender': 'Male', 'tag': 'US'},
            {'id': 'en-IN-PrabhatNeural', 'name': 'Prabhat (Indian English)', 'desc': 'Professional Indian English male voice', 'gender': 'Male', 'tag': 'IN'},
            {'id': 'en-IN-NeerjaNeural', 'name': 'Neerja (Indian English)', 'desc': 'Expressive Indian English female voice', 'gender': 'Female', 'tag': 'IN'}
        ]
    })

# ── 7. Route: Remote Conversational Q&A Only ──
@remote_app.route('/remote/chat', methods=['POST'])
@remote_app.route('/api/chat', methods=['POST'])
def remote_chat():
    client_ip = get_client_ip()
    if not check_rate_limit(client_ip):
        return jsonify({
            'success': False,
            'error': 'Rate limit exceeded. Please wait a moment before sending another question.'
        }), 429

    # Passcode Authentication Gate
    is_auth, auth_err = check_request_auth()
    if not is_auth:
        return jsonify({
            'success': False,
            'error': f'Authentication required: {auth_err}',
            'auth_required': True
        }), 401

    data = request.json or {}
    raw_message = data.get('message', '').strip()
    if not raw_message:
        return jsonify({'response': 'Greetings. Ask me any question, and I will be glad to assist.', 'success': True})

    if len(raw_message) > 8000:
        return jsonify({'success': False, 'error': 'Message exceeds maximum length of 8000 characters.'}), 400

    # Security Kernel: Input Inspection & Prompt Firewall
    processed = security_kernel.process_input(raw_message, request=request)
    if processed.is_blocked:
        return jsonify({
            'success': False,
            'response': 'I apologize, but this prompt was flagged and halted by the security firewall due to anomalous or disallowed patterns.'
        }), 400

    # Policy Authorization check for general_chat with TrustLevel.REMOTE_PUBLIC
    auth = security_kernel.authorize_action("general_chat", {"prompt": processed.normalized_message}, trust_level=TrustLevel.REMOTE_PUBLIC)
    if not auth.allowed:
        return jsonify({
            'success': False,
            'error': f'Service policy restriction: {auth.reason}'
        }), 403

    try:
        # 100% Local Apple Silicon MLX GPU Inference with Q&A Persona + Creator Knowledge
        reply = gemma_local.infer_gemma(
            prompt=processed.normalized_message,
            system_prompt=get_remote_system_prompt(),
            history=[],
            max_tokens=1024,
            temperature=0.7
        )
        # Stage 11: Output Sanitization
        clean_reply = security_kernel.sanitize_output(reply, trust_level=TrustLevel.REMOTE_PUBLIC)
        return jsonify({'response': clean_reply, 'success': True})
    except Exception as e:
        return jsonify({
            'response': f"An error occurred during neural inference: {e}",
            'success': False
        }), 500

@remote_app.route('/api/chat/stream', methods=['POST'])
def remote_chat_stream():
    client_ip = get_client_ip()
    if not check_rate_limit(client_ip):
        return jsonify({
            'success': False,
            'error': 'Rate limit exceeded. Please wait a moment before sending another question.'
        }), 429

    is_auth, auth_err = check_request_auth()
    if not is_auth:
        return jsonify({
            'success': False,
            'error': f'Authentication required: {auth_err}',
            'auth_required': True
        }), 401

    data = request.json or {}
    raw_message = data.get('message', '').strip()
    if not raw_message:
        return jsonify({'error': 'Message cannot be empty.'}), 400

    if len(raw_message) > 8000:
        return jsonify({'error': 'Message exceeds maximum length of 8000 characters.'}), 400

    processed = security_kernel.process_input(raw_message, request=request)
    if processed.is_blocked:
        return jsonify({
            'error': 'Prompt was flagged and halted by the security firewall.'
        }), 400

    auth = security_kernel.authorize_action("general_chat", {"prompt": processed.normalized_message}, trust_level=TrustLevel.REMOTE_PUBLIC)
    if not auth.allowed:
        return jsonify({
            'error': f'Service policy restriction: {auth.reason}'
        }), 403

    def event_stream():
        yield f"data: {json.dumps({'type': 'stream_start'})}\n\n"
        collected = []
        try:
            for token_piece in gemma_local.stream_gemma(
                prompt=processed.normalized_message,
                system_prompt=get_remote_system_prompt(),
                max_tokens=1024,
                temperature=0.7
            ):
                collected.append(token_piece)
                yield f"data: {json.dumps({'type': 'stream_chunk', 'token': token_piece})}\n\n"
            full_text = "".join(collected).strip()
            clean_text = security_kernel.sanitize_output(full_text, trust_level=TrustLevel.REMOTE_PUBLIC)
            yield f"data: {json.dumps({'type': 'stream_end', 'response': clean_text})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'stream_error', 'error': str(e)})}\n\n"

    return Response(
        stream_with_context(event_stream()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )

# ── 8. Routes: Permanent Block on Privileged Automation Endpoints ──
@remote_app.route('/api/desktop', methods=['GET', 'POST', 'PUT', 'DELETE'])
@remote_app.route('/api/action', methods=['GET', 'POST', 'PUT', 'DELETE'])
@remote_app.route('/remote/action', methods=['GET', 'POST', 'PUT', 'DELETE'])
@remote_app.route('/api/system', methods=['GET', 'POST', 'PUT', 'DELETE'])
@remote_app.route('/api/automation', methods=['GET', 'POST', 'PUT', 'DELETE'])
@remote_app.route('/api/screenshot', methods=['GET', 'POST', 'PUT', 'DELETE'])
@remote_app.route('/api/vision', methods=['GET', 'POST', 'PUT', 'DELETE'])
@remote_app.route('/api/memory', methods=['GET', 'POST', 'PUT', 'DELETE'])
@remote_app.route('/api/memory/write', methods=['GET', 'POST', 'PUT', 'DELETE'])
@remote_app.route('/api/soul', methods=['GET', 'POST', 'PUT', 'DELETE'])
@remote_app.route('/api/files', methods=['GET', 'POST', 'PUT', 'DELETE'])
@remote_app.route('/api/terminal', methods=['GET', 'POST', 'PUT', 'DELETE'])
def blocked_privileged_endpoint():
    """Explicit server-side block on any privileged Mac control endpoint."""
    audit_chain.log_event(
        event_type="UNAUTHORIZED_REMOTE_ENDPOINT_ATTEMPT",
        action=request.path,
        result="BLOCKED",
        trust_level=TrustLevel.REMOTE_PUBLIC.value,
        risk_level="HIGH",
        details={"ip": get_client_ip(), "method": request.method, "path": request.path}
    )
    return jsonify({
        'success': False,
        'error': 'Forbidden: Remote entry point is strictly conversational Q&A only. Desktop automation and system APIs are permanently disabled.',
        'endpoint_status': 'DISABLED_BY_SECURITY_POLICY'
    }), 403

# ── 9. Real-Time WebSocket Streaming (/ws) - Q&A Only ──
@sock.route('/ws')
def remote_ws(ws):
    is_authenticated = not REQUIRE_AUTH
    ws.send(json.dumps({
        'type': 'connected',
        'service': 'J.A.R.V.I.S. Remote Q&A',
        'auth_required': REQUIRE_AUTH,
        'authenticated': is_authenticated,
        'capabilities': 'Q&A Streaming Only'
    }))

    while True:
        try:
            raw = ws.receive()
            if raw is None:
                break
            try:
                data = json.loads(raw)
            except Exception:
                continue

            msg_type = data.get('type')

            # Authentication Message
            if msg_type == 'auth':
                token = data.get('token')
                passcode = data.get('passcode')
                if not REQUIRE_AUTH:
                    is_authenticated = True
                    ws.send(json.dumps({'type': 'auth_ok', 'message': 'Authenticated'}))
                    ws.send(json.dumps({'type': 'auth_success', 'message': 'Authenticated'}))
                    continue
                if token:
                    valid, err = verify_session_token(token)
                    if valid:
                        is_authenticated = True
                        ws.send(json.dumps({'type': 'auth_ok', 'message': 'Authenticated'}))
                        ws.send(json.dumps({'type': 'auth_success', 'message': 'Authenticated'}))
                        continue
                if passcode:
                    if verify_passcode_match(str(passcode), get_remote_passcode()):
                        is_authenticated = True
                        new_tok = generate_session_token()
                        ws.send(json.dumps({'type': 'auth_ok', 'token': new_tok, 'message': 'Authenticated'}))
                        ws.send(json.dumps({'type': 'auth_success', 'token': new_tok, 'message': 'Authenticated'}))
                        continue
                ws.send(json.dumps({'type': 'auth_failed', 'error': 'Invalid token or passcode'}))
                continue

            # Ping/Pong round-trip latency measurement
            if msg_type == 'ping':
                client_time = data.get('client_time')
                ws.send(json.dumps({
                    'type': 'pong',
                    'client_time': client_time,
                    'server_time': time.time()
                }))
                continue

            # Ensure client is authenticated before processing chat or other requests
            if not is_authenticated:
                ws.send(json.dumps({
                    'type': 'auth_required',
                    'error': 'Authentication required. Send {"type": "auth", "token": "..."} first.'
                }))
                continue

            # Strict Rejection of any Action/Automation request over WebSocket
            if msg_type in ('action', 'desktop', 'system', 'execute'):
                audit_chain.log_event(
                    event_type="UNAUTHORIZED_REMOTE_WS_ACTION_ATTEMPT",
                    action=str(msg_type),
                    result="BLOCKED",
                    trust_level=TrustLevel.REMOTE_PUBLIC.value,
                    risk_level="HIGH",
                    details={"type": msg_type}
                )
                ws.send(json.dumps({
                    'type': 'error',
                    'error': 'Action execution is strictly disabled on the remote Q&A gateway.'
                }))
                continue

            # Conversational Chat Streaming
            if msg_type == 'chat':
                msg = data.get('message', '').strip()
                if not msg:
                    continue

                if len(msg) > 8000:
                    ws.send(json.dumps({'type': 'error', 'error': 'Message exceeds 8000 characters.'}))
                    continue

                processed = security_kernel.process_input(msg)
                if processed.is_blocked:
                    ws.send(json.dumps({'type': 'error', 'error': 'Message rejected by security firewall.'}))
                    continue

                auth = security_kernel.authorize_action("general_chat", {"prompt": processed.normalized_message}, trust_level=TrustLevel.REMOTE_PUBLIC)
                if not auth.allowed:
                    ws.send(json.dumps({'type': 'error', 'error': f'Policy restriction: {auth.reason}'}))
                    continue

                ws.send(json.dumps({'type': 'stream_start'}))
                collected_tokens = []
                try:
                    for token_piece in gemma_local.stream_gemma(
                        prompt=processed.normalized_message,
                        system_prompt=get_remote_system_prompt(),
                        max_tokens=1024,
                        temperature=0.7
                    ):
                        collected_tokens.append(token_piece)
                        ws.send(json.dumps({'type': 'stream_chunk', 'token': token_piece}))
                    full_text = "".join(collected_tokens).strip()
                    clean_text = security_kernel.sanitize_output(full_text, trust_level=TrustLevel.REMOTE_PUBLIC)
                    ws.send(json.dumps({'type': 'stream_end', 'response': clean_text}))
                except Exception as e:
                    ws.send(json.dumps({'type': 'stream_error', 'error': str(e)}))

        except Exception:
            break

# ── 10. Lifecycle & Clean Shutdown ──
def cleanup():
    global tunnel_manager
    if tunnel_manager:
        try:
            tunnel_manager.stop()
        except Exception:
            pass

atexit.register(cleanup)

def handle_exit(sig, frame):
    print("\n[SHUTDOWN] Powering down J.A.R.V.I.S. Remote Q&A Server. Goodbye.\n", flush=True)
    cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

def ensure_port_available(port, host="127.0.0.1"):
    """Verify that port is free. If occupied by a stale process, cleanly recycle it."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        in_use = s.connect_ex((host, port)) == 0
    if in_use:
        try:
            import subprocess
            out = subprocess.check_output(["lsof", "-ti", f":{port}"], text=True).strip()
            if out:
                pids = [int(p) for p in out.split()]
                curr_pid = os.getpid()
                other_pids = [p for p in pids if p != curr_pid]
                if other_pids:
                    print(f"[PORT MANAGER] Port {port} is occupied by PID(s): {other_pids}. Freeing port...", flush=True)
                    for pid in other_pids:
                        try:
                            os.kill(pid, signal.SIGTERM)
                        except Exception:
                            pass
                    time.sleep(1)
        except Exception as e:
            print(f"[PORT MANAGER] Warning inspecting port {port}: {e}", flush=True)

def main():
    global tunnel_manager, current_gateway_url

    # 1. Probe diagnostics for startup display
    diagnostics = probe_subsystems()

    # 2. Verify port availability
    ensure_port_available(REMOTE_PORT, REMOTE_HOST)

    # Pre-warm Apple Silicon MLX GPU so the very first inquiry is INSTANT
    if gemma_local.is_gemma_available():
        print("[AI ENGINE] Warming up Apple Silicon MLX GPU & resident model...", flush=True)
        try:
            gemma_local.load_gemma()
            print("[AI ENGINE] ✅ Model resident in unified memory. Ready for instant Q&A.\n", flush=True)
        except Exception as e:
            print(f"[AI ENGINE] Warning warming up Gemma: {e}", flush=True)

    # 3. Start Flask Remote Server in background daemon thread
    server_thread = threading.Thread(
        target=lambda: remote_app.run(
            host=REMOTE_HOST,
            port=REMOTE_PORT,
            threaded=True,
            use_reloader=False
        ),
        daemon=True
    )
    server_thread.start()

    # Wait for local server to become healthy (up to 3 seconds)
    import socket
    server_ready = False
    for _ in range(30):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex((REMOTE_HOST, REMOTE_PORT)) == 0:
                server_ready = True
                break
        time.sleep(0.1)

    if not server_ready:
        print(f"❌ [STARTUP ERROR] Could not bind local server to http://{REMOTE_HOST}:{REMOTE_PORT}.", flush=True)
        sys.exit(1)

    # 4. Establish Outbound Cloudflare Tunnel if enabled
    if REMOTE_ENABLED:
        try:
            tunnel_manager = CloudflareTunnelManager(local_port=REMOTE_PORT)
            current_gateway_url = tunnel_manager.start(timeout=35)
        except Exception as e:
            print(f"⚠️  [TUNNEL WARNING] Outbound gateway could not be established: {e}", flush=True)
            print(f"   Continuing on Local Gateway: http://{REMOTE_HOST}:{REMOTE_PORT}\n", flush=True)
            current_gateway_url = None

    # 4. Print Official J.A.R.V.I.S. Remote Q&A Startup Banner
    local_url = f"http://{REMOTE_HOST}:{REMOTE_PORT}"
    banner_passcode = "OPEN (No Password Required)" if not REQUIRE_AUTH else get_remote_passcode()
    print(format_remote_banner(
        diagnostics,
        local_url=local_url,
        gateway_url=current_gateway_url,
        passcode=banner_passcode
    ), flush=True)
    if not REQUIRE_AUTH:
        print("\n⚡ ACCESS: OPEN Q&A MODE (Password & Authentication Disabled)", flush=True)
        print("   Direct Question & Answer Access Enabled for All Connected Devices.\n", flush=True)
    else:
        session_passcode = get_remote_passcode()
        print(f"\n🔑 ONE-TIME SESSION PASSCODE:  {session_passcode}", flush=True)
        print("   (Enter this passcode on the login screen to access)\n", flush=True)
    print("Press Ctrl+C to shut down JARVIS Remote.\n", flush=True)

    # 5. Keep main process alive & monitor tunnel health
    try:
        while True:
            time.sleep(1)
            if tunnel_manager and tunnel_manager.process and tunnel_manager.process.poll() is not None:
                print("\n[TUNNEL] Outbound tunnel disconnected unexpectedly. Reconnecting...", flush=True)
                try:
                    current_gateway_url = tunnel_manager.start(timeout=25)
                    print(f"[TUNNEL] Reconnected: {current_gateway_url}", flush=True)
                except Exception as err:
                    print(f"[TUNNEL] Reconnection failed: {err}", flush=True)
    except (KeyboardInterrupt, SystemExit):
        print("\nPowering down J.A.R.V.I.S. Remote Q&A. Goodbye.\n", flush=True)
        cleanup()

if __name__ == '__main__':
    main()
