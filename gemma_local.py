"""
Local Gemma 4 E2B 4-bit inference engine accelerated on Apple Silicon GPU via MLX.
Supports:
- Local offline text generation & general AI reasoning
- Local computer vision & image understanding
- Blazing-fast inference (~88 tokens/sec) with zero API keys required
"""
import os
import glob
import warnings
warnings.filterwarnings("ignore")
import mlx_vlm
from mlx_vlm import load, generate
from mlx_vlm.utils import load_image

_gemma_model = None
_gemma_processor = None
MODEL_ID = "mlx-community/gemma-4-e2b-it-4bit"

def get_gemma_model_path():
    matches = glob.glob(os.path.expanduser("~/.cache/huggingface/hub/models--mlx-community--gemma-4-e2b-it-4bit/snapshots/*"))
    if matches:
        return matches[0]
    return MODEL_ID

def is_gemma_available():
    matches = glob.glob(os.path.expanduser("~/.cache/huggingface/hub/models--mlx-community--gemma-4-e2b-it-4bit/snapshots/*"))
    return len(matches) > 0

def load_gemma():
    global _gemma_model, _gemma_processor
    if _gemma_model is not None and _gemma_processor is not None:
        return _gemma_model, _gemma_processor

    model_path = get_gemma_model_path()
    print(f"[Gemma 4 E2B] Loading 4-bit MLX model into Apple Silicon Unified Memory from {model_path}...")
    _gemma_model, _gemma_processor = load(model_path)
    print("[Gemma 4 E2B] ✅ Model successfully resident in Apple Silicon Unified Memory.")
    return _gemma_model, _gemma_processor

def infer_gemma(prompt, system_prompt="", history=None, image_path=None, max_tokens=1024, temperature=0.7):
    model, processor = load_gemma()

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": [{"type": "text", "text": system_prompt}]})

    if history:
        for msg in history[-10:]:
            role = "assistant" if msg.get("role") in ("model", "assistant") else "user"
            text_content = msg["parts"][0]["text"] if "parts" in msg else msg.get("content", "")
            messages.append({"role": role, "content": [{"type": "text", "text": text_content}]})

    user_content = []
    image = None
    if image_path and os.path.exists(image_path):
        try:
            image = load_image(image_path)
            user_content.append({"type": "image"})
        except Exception as e:
            print(f"[Gemma 4 E2B] Warning: Could not load image {image_path}: {e}")

    user_content.append({"type": "text", "text": prompt})
    messages.append({"role": "user", "content": user_content})

    formatted_prompt = processor.apply_chat_template(messages, add_generation_prompt=True)
    
    gen_kwargs = {
        "max_tokens": max_tokens,
        "temperature": max(0.1, float(temperature))
    }
    if image is not None:
        gen_kwargs["image"] = image

    result = generate(model, processor, formatted_prompt, **gen_kwargs)
    text_out = result.text if hasattr(result, "text") else str(result)
    return text_out.strip()

def stream_gemma(prompt, system_prompt="", history=None, image_path=None, max_tokens=1024, temperature=0.7):
    """Stream tokens piece-by-piece using Apple MLX stream_generate."""
    model, processor = load_gemma()

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": [{"type": "text", "text": system_prompt}]})

    if history:
        for msg in history[-10:]:
            role = "assistant" if msg.get("role") in ("model", "assistant") else "user"
            text_content = msg["parts"][0]["text"] if "parts" in msg else msg.get("content", "")
            messages.append({"role": role, "content": [{"type": "text", "text": text_content}]})

    user_content = []
    image = None
    if image_path and os.path.exists(image_path):
        try:
            image = load_image(image_path)
            user_content.append({"type": "image"})
        except Exception as e:
            print(f"[Gemma 4 E2B] Warning: Could not load image {image_path}: {e}")

    user_content.append({"type": "text", "text": prompt})
    messages.append({"role": "user", "content": user_content})

    formatted_prompt = processor.apply_chat_template(messages, add_generation_prompt=True)
    
    gen_kwargs = {
        "max_tokens": max_tokens,
        "temperature": max(0.1, float(temperature))
    }
    if image is not None:
        gen_kwargs["image"] = image

    for piece in mlx_vlm.stream_generate(model, processor, formatted_prompt, **gen_kwargs):
        yield piece.text


if __name__ == "__main__":
    import sys
    print("\n" + "=" * 62)
    print("🤖  J.A.R.V.I.S. Local Gemma 4 E2B Terminal Interface")
    print("    Owner: Divyanshu Verma | Divyanshu Industries")
    print("    Engine: Apple Silicon MLX GPU (~88 tokens/sec, 100% Offline)")
    print("    Exit:  Type 'exit' or 'quit' to terminate session")
    print("=" * 62 + "\n")

    sys_prompt = "You are J.A.R.V.I.S., an ultra-advanced AI assistant created by Divyanshu Verma for Divyanshu Industries. You are sophisticated, witty, concise, and helpful. Always address Divyanshu Verma as Sir."
    
    model, processor = load_gemma()
    chat_history = []

    print("\n[JARVIS System Ready. Online and listening.]")
    while True:
        try:
            user_input = input("\nDivyanshu Verma > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                print("\nJARVIS: Powering down terminal interface. Have a good day, Sir.\n")
                break

            messages = [{"role": "system", "content": [{"type": "text", "text": sys_prompt}]}]
            for h in chat_history[-6:]:
                messages.append(h)
            messages.append({"role": "user", "content": [{"type": "text", "text": user_input}]})

            formatted_prompt = processor.apply_chat_template(messages, add_generation_prompt=True)
            res = generate(model, processor, formatted_prompt, max_tokens=1024, temperature=0.7, verbose=False)
            reply = res.text if hasattr(res, "text") else str(res)
            print(f"\nJARVIS: {reply.strip()}\n")
            chat_history.append({"role": "user", "content": [{"type": "text", "text": user_input}]})
            chat_history.append({"role": "assistant", "content": [{"type": "text", "text": reply.strip()}]})
        except (KeyboardInterrupt, EOFError):
            print("\nJARVIS: Session terminated. Goodbye, Sir.\n")
            break

