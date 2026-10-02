# JARVIS Sovereign Cognitive Architecture (v5.0)

![JARVIS](https://img.shields.io/badge/JARVIS-Sovereign%20AI-00e5ff?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)

JARVIS v5.0 is a highly advanced, multi-modal **Sovereign AI Agent** designed for deep macOS integration. Unlike standard LLM wrappers, JARVIS bridges the gap between raw artificial intelligence and physical desktop execution. It features a multi-tiered cognitive memory system, defense-in-depth security (including biometric TouchID authorization), native macOS Swift automation, and an advanced Voice/Spatial UI.

## 🧠 Core Architecture

### Intelligence & Orchestration
- **Specialized Agents:** Distinct roles including a Planner for long-term goal setting, an Executor for taking actions, a Computer agent for OS manipulation, and a Validator.
- **Dynamic Routing:** Intelligently routes queries across Gemini, Groq, or local models (`gemma_local.py`) based on speed, cost, and capability requirements.
- **Screen Awareness:** Native computer vision integration allowing JARVIS to "see" and interpret what is on the screen.

### 🗄️ Multi-Tier Memory System
Simulates human cognition through structured memory banks:
- **Short-term Memory:** Immediate conversation and task context.
- **Episodic Memory:** Specific past events and interactions.
- **Semantic Memory:** Long-term factual knowledge and user preferences.
- **Procedural Memory:** "Muscle memory" for executing complex workflows on macOS.

### 💻 Physical Desktop Control
- **Swift Automation:** Injects native Swift code (`mouse_helper.swift`) directly into the Python backend for low-latency, precise pointer manipulation, bypassing standard macOS sandbox limitations.
- **Direct App Hooks:** Integrates deeply with the Apple Suite, Calendar, Email, and heavily custom-engineered WhatsApp controllers.

### 🔒 Defense-in-Depth Security
- **Kill Switch:** Emergency hardware and software stops to freeze the agent instantly.
- **Biometric Authorization:** Hooks into macOS TouchID to authorize sensitive AI actions (e.g., sending payments, deleting files).
- **Prompt Firewall & Output Guard:** Defends against prompt injection and prevents destructive system commands.

### 🗣️ Voice & Spatial UI
- **Neural Voice & Speech:** Modular Edge TTS neural voice synthesis and low-latency Speech-to-Text.
- **Holo-Reactor UI:** Iron Man-style 3D Heads-Up Display utilizing Three.js and MediaPipe for webcam-based hand gesture recognition.

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/divyanshuvermaai-png/jarvis-mark-50.git
   cd jarvis-mark-50
   ```

2. **Install dependencies:**
   *(Ensure you have Python 3.9+ and Node.js v26+ installed)*
   ```bash
   npm install
   pip install -r requirements.txt # (if generated)
   ```

3. **Start the Sovereign Core:**
   ```bash
   npm start
   ```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
