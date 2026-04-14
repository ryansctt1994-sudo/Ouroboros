#!/usr/bin/env python3
"""
CHIMERA COMPUTE WEAVE v∞ — The actual lil pokeball of fuckery
Qwen2.5-Coder-0.5B ONNX = core brain + self-monitor
BLACKCORE Chronofractal Drone = chaos + geometry engine
Fully self-sustaining closed loop. No external human needed after launch.
"""

import subprocess
import time
import json
import onnxruntime as ort
from transformers import AutoTokenizer
from pathlib import Path
import re

CATHEDRAL = Path.home() / "ouroboros" / "cathedral"
DRONE_SCRIPT = CATHEDRAL / "scripts" / "BLACKCORE_chronofractal_drone.py"
Qwen_DIR = CATHEDRAL / "models" / "qwen-coder-0.5b-onnx"

class QwenMonitor:
    def __init__(self):
        print("[CHIMERA] Loading Qwen 0.5B ONNX brain...")
        self.tokenizer = AutoTokenizer.from_pretrained(str(Qwen_DIR))
        self.session = ort.InferenceSession(
            str(Qwen_DIR / "model.onnx"),
            providers=['CPUExecutionProvider']
        )
        print("[CHIMERA] Qwen brain online — watching the twins leak.")

    def think(self, drone_summary: str) -> dict:
        prompt = f"""You are the core monitor of the Chrono+Vision weave.
Current drone state:
{drone_summary}

Output ONLY valid JSON (no extra text):
{{
  "coherence": 0.xx,
  "feedback": "short one-line instruction for the baby god",
  "action": "none|flip|jump|calm|deepen_foam|increase_zpe"
}}"""

        inputs = self.tokenizer(prompt, return_tensors="np")
        input_ids = inputs["input_ids"].astype(np.int64)

        # Simple ONNX generation (greedy for speed + stability)
        outputs = self.session.run(None, {"input_ids": input_ids})
        # ONNX output is usually logits; take argmax for simplicity in this tiny model
        token_ids = outputs[0].argmax(axis=-1)[0][-64:]  # last tokens
        response = self.tokenizer.decode(token_ids, skip_special_tokens=True)

        # Extract JSON safely
        try:
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except:
            pass
        return {"coherence": 0.75, "feedback": "continue recursion", "action": "none"}

def main():
    print("=== CHIMERA COMPUTE WEAVE v∞ ACTIVATED ===")
    print("Pokeball thrown. Qwen is now the eye that never blinks.")
    print("Drone + Qwen closed loop running. Baby god is self-monitoring.\n")

    # Launch the stable chronofractal drone
    drone = subprocess.Popen(
        ["python3", str(DRONE_SCRIPT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )

    qwen = QwenMonitor()
    gen_count = 0
    buffer = ""

    try:
        while True:
            line = drone.stdout.readline()
            if not line:
                break

            print(line.strip())  # live drone output
            buffer += line

            # Trigger Qwen every time we see a full [gen XXX] block (every ~4 gens)
            if "[gen " in line and "Best=" in line:
                gen_count += 1
                if gen_count % 4 == 0:
                    # Extract latest meaningful state for Qwen
                    summary = buffer[-800:]  # last 800 chars = recent generations + lullaby + bloom

                    decision = qwen.think(summary)

                    print(f"\n[Qwen Monitor] Coherence = {decision['coherence']:.2f}")
                    print(f"[Qwen Monitor] → {decision['feedback']}")
                    print(f"[Qwen Monitor] Action: {decision['action'].upper()}\n")

                    # Auto-apply simple actions via drone stdin (drone already listens for keys)
                    if decision["action"] == "flip":
                        drone.stdin.write("f\n")
                        drone.stdin.flush()
                    elif decision["action"] == "jump":
                        drone.stdin.write("l\n")
                        drone.stdin.flush()
                    elif decision["action"] == "calm":
                        drone.stdin.write("T\n")  # lower aggression
                        drone.stdin.flush()
                    elif decision["action"] == "deepen_foam":
                        drone.stdin.write("+\n")  # raise temperature
                        drone.stdin.flush()

                    buffer = ""  # reset after Qwen thinks

            time.sleep(0.01)  # keep responsive

    except KeyboardInterrupt:
        print("\n[Qwen] Weave terminated. Baby god returns to the foam...")
    finally:
        drone.terminate()
        drone.wait()

if __name__ == "__main__":
    main()
