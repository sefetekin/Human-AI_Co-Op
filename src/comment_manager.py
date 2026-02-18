import os
import time
import threading
import requests
import subprocess
import atexit
from dotenv import load_dotenv
load_dotenv()

class CommentaryManager:
    def __init__(self, traits, llm_func):
        self.traits = traits
        self.llm_func = self.generate_commentary_with_request if llm_func == "request" else self.generate_commentary_with_gpt4all

        self.current_line = ""
        self.expire_time = 0

        self.last_ambient_time = 0
        self.ambient_interval = 2  # seconds

        self.enabled = True
        self.lock = threading.Lock()
        
        self.ensure_tunnel()      # 🚨 AUTO START
        atexit.register(self.close_tunnel)   # 🚨 CLEANUP ON EXIT

    # --------------------------------------------------
    # PUBLIC API
    # --------------------------------------------------

    def update(self, game_metrics):
        """
        Called periodically (e.g. once per second).
        Decides whether to trigger ambient commentary.
        """
        if not self.enabled:
            return
        now = time.time()

        if now < self.expire_time:
            return  # something is already being shown

        if now - self.last_ambient_time >= self.ambient_interval:
            self.last_ambient_time = now
            self._trigger_async(
                event="AMBIENT",
                context=game_metrics,
                duration=2.0,
            )

    def trigger_event(self, event, context, duration=2.0):
        
        """
        Immediate high-priority commentary.
        """
        if not self.enabled:
            return
        self._trigger_async(event, context, duration)

    def get_line(self):
        return self.current_line if time.time() < self.expire_time else ""

    # --------------------------------------------------
    # INTERNAL
    # --------------------------------------------------

    def _trigger_async(self, event, context, duration):
        def worker():
            try:
                text = self.llm_func(
                    traits=self.traits,
                    event=event,
                    context=context,
                )
                print("Generated commentary:", text)
            except Exception:
                return

            with self.lock:
                self.current_line = text
                self.expire_time = time.time() + duration

        threading.Thread(target=worker, daemon=True).start()

    def generate_commentary_with_request(self, traits, event, context, model="gemma3:4b", temperature=0.6, max_tokens=40):
        

        system_prompt = (
            "You are an in-game commentator.\n"
            "Speak in short, natural sentences.\n"
            "Do not narrate constantly.\n"
            "Do not explain mechanics.\n"
            "Never mention exact numbers unless critical.\n"
            "Match tone to the player's mood.\n"
            f"Make it different in vocabulary from your previous comment of '{self.current_line}'.\n"
            "Output ONE short sentence only."
        )

        if event == "AMBIENT":
            user_prompt = "Make a light observational comment about the current game state."
        else:
            user_prompt = f"React immediately to this event: {event}"

        user_prompt = (
            f"Player traits: {traits}\n"
            f"Context: {context}\n"
            f"{user_prompt}"
        )

        payload = {
            "model": "gemma3:4b",   # match what you're serving remotely
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.6,
            "max_tokens": 40
        }

        try:
            response = requests.post(
                "http://localhost:11434/api/chat",   # 🚨 THIS IS THE BIG CHANGE
                json=payload,
                timeout=5
            )

            data = response.json()

            return data["message"]["content"].strip()

        except Exception as e:
            print("LLM commentary error:", e)
            return ""



    def generate_commentary_with_gpt4all(self, traits, event, context):
        from gpt4all import GPT4All

        model = GPT4All("Meta-Llama-3-8B-Instruct.Q4_0.gguf")

        system = (
            "You are an in-game commentator.\n"
            "Speak in short, natural sentences.\n"
            "Do not narrate constantly.\n"
            "Do not explain mechanics.\n"
            "Never mention exact numbers unless critical.\n"
            "Match tone to the player's mood.\n"
            "Output ONE short sentence only."
        )

        if event == "AMBIENT":
            instruction = "Make a light observational comment about the current game state."
        else:
            instruction = f"React immediately to this event: {event}"

        user = (
            f"Player traits: {traits}\n"
            f"Context: {context}\n"
            f"{instruction}"
        )

        prompt = system + "\n\n" + user

        with model.chat_session():
            return model.generate(prompt, max_tokens=40).strip()
    
    def ensure_tunnel(self):

        # If localhost already responds → tunnel already exists
        try:
            requests.get("http://localhost:11434/api/tags", timeout=1)
            print("[Tunnel] Already active")
            return
        except:
            pass

        print("[Tunnel] Starting SSH tunnel...")

        host = os.getenv("REMOTE_HOST")
        jump = os.getenv("JUMP_USER")
        user = os.getenv("REMOTE_USER")

        if not all([host, jump, user]):
            raise RuntimeError("Missing SSH environment variables (.env not loaded?)")

        cmd = [
            "ssh",
            "-N",
            "-L", f"11434:{host}:11434",
            "-J", f"{jump}@knuckles.cs.ucl.ac.uk",
            f"{user}@{host}"
        ]


        self.tunnel_proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        time.sleep(2)

        # Confirm tunnel worked
        try:
            requests.get("http://localhost:11434/api/tags", timeout=3)
            print("[Tunnel] Connected successfully")
        except:
            print("[Tunnel] Failed - VPN likely not connected")
            
    def close_tunnel(self):
        if self.tunnel_proc:
            print("[Tunnel] Closing SSH tunnel")
            self.tunnel_proc.terminate()


