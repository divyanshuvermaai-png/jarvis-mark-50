"""
J.A.R.V.I.S. Cloudflare Tunnel Manager
Manages:
- Detection of cloudflared executable
- Outbound ephemeral HTTPS tunnel generation (trycloudflare.com)
- Non-blocking URL extraction
- Clean subprocess termination & zombie cleanup
"""
import os
import re
import sys
import time
import shutil
import signal
import atexit
import subprocess
import threading

class TunnelDependencyError(Exception):
    pass

class CloudflareTunnelManager:
    def __init__(self, local_port=5002):
        self.local_port = local_port
        self.process = None
        self.public_url = None
        self.log_buffer = []
        self._find_binary()
        atexit.register(self.stop)

    def _find_binary(self):
        """Locate cloudflared across PATH and standard Homebrew directories."""
        candidates = [
            shutil.which("cloudflared"),
            "/opt/homebrew/bin/cloudflared",
            "/usr/local/bin/cloudflared",
            os.path.expanduser("~/bin/cloudflared")
        ]
        for path in candidates:
            if path and os.path.exists(path) and os.access(path, os.X_OK):
                self.binary_path = path
                return
        raise TunnelDependencyError(
            "\n[TUNNEL ERROR] Cloudflare Tunnel executable ('cloudflared') not found.\n"
            "To install it on your Mac, please run:\n"
            "    brew install cloudflared\n"
        )

    def start(self, timeout=35):
        """Start the tunnel and block until the public HTTPS URL is captured."""
        if self.process:
            self.stop()
        self.public_url = None
        self.log_buffer = []

        cmd = [
            self.binary_path,
            "tunnel",
            "--url", f"http://127.0.0.1:{self.local_port}",
            "--no-autoupdate"
        ]
        
        print(f"[TUNNEL] Launching secure tunnel to 127.0.0.1:{self.local_port}...")
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        url_found_event = threading.Event()
        url_regex = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

        def _reader(stream):
            for line in iter(stream.readline, ""):
                self.log_buffer.append(line)
                match = url_regex.search(line)
                if match and not self.public_url:
                    self.public_url = match.group(0)
                    url_found_event.set()
            stream.close()

        t_err = threading.Thread(target=_reader, args=(self.process.stderr,), daemon=True)
        t_out = threading.Thread(target=_reader, args=(self.process.stdout,), daemon=True)
        t_err.start()
        t_out.start()

        # Wait for URL extraction
        success = url_found_event.wait(timeout=timeout)
        if not success or not self.public_url:
            # Check if process exited early
            if self.process.poll() is not None:
                err_msg = "".join(self.log_buffer[-10:])
                raise RuntimeError(f"Tunnel process terminated prematurely: {err_msg}")
            raise TimeoutError(f"Cloudflare Tunnel timed out after {timeout} seconds. Logs:\n" + "".join(self.log_buffer[-5:]))

        # Verify DNS reachability before returning to prevent ERR_NAME_NOT_RESOLVED
        hostname = self.public_url.replace("https://", "").split("/")[0]
        import socket
        for _ in range(25):
            try:
                socket.gethostbyname(hostname)
                break
            except Exception:
                time.sleep(0.4)

        print(f"[TUNNEL] Tunnel connected: {self.public_url}")
        return self.public_url

    def stop(self):
        """Cleanly terminate the tunnel subprocess."""
        if self.process:
            try:
                if self.process.poll() is None:
                    print("\n[TUNNEL] Terminating Cloudflare tunnel...")
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
                        self.process.wait(timeout=1)
                    print("[TUNNEL] Tunnel terminated cleanly.")
            except Exception as e:
                pass
            finally:
                self.process = None
