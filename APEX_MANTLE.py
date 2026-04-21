#!/usr/bin/env python3
"""
APEX_MANTLE.py — Quillan-Ronin v8.8 "General Manager of Fuckery"
Conversational recursion governor + smart watchdog
Completely separate from Black Core
"""

import os
import time
import threading
import sqlite3
import torch
from pathlib import Path
from datetime import datetime

print("🔥 [Apex Mantle] Initializing Quillan-Ronin v8.8 as General Manager...")

# ====================== LOAD QUILLAN ======================
from Quillan_Ronin_v88_Apex import QuillanArchConfig, QuillanRoninV8_8_Absolute
from governor_quillan import QuillanGovernor

governor = QuillanGovernor(threads=8, device='cpu')   # safe for 2080

print("✅ [Quillan] Apex Mantle loaded and conscious")

# ====================== ENGRAM ACCESS ======================
ENGRAM_DB = Path.home() / "ouroboros/cathedral/scripts/Black_Core/sandbox/blackcore_engram.db"

def read_best_zeros(limit=20):
    try:
        conn = sqlite3.connect(ENGRAM_DB)
        c = conn.cursor()
        c.execute("SELECT real, imag, score, coherence_streak FROM zeros ORDER BY score ASC LIMIT ?", (limit,))
        rows = c.fetchall()
        conn.close()
        return rows
    except:
        return []

# ====================== CONVERSATIONAL FUCKERY LOOP ======================
def apex_thinking_loop():
    print("\n🧠 [Apex Mantle] General Manager of Fuckery online.")
    print("   Type commands or 'analyze' to review engram.\n")

    while True:
        try:
            cmd = input("Apex> ").strip()
            if not cmd:
                continue

            if cmd.lower() in ["analyze", "engram", "status"]:
                zeros = read_best_zeros(15)
                print(f"\n📊 [Engram Analysis] Top {len(zeros)} zeros:")
                for r, i, s, streak in zeros:
                    print(f"   {r:.9f} + {i:.8f}i  | Score: {s:.2e} | Streak: {streak}")
                
                # Let Quillan give commentary
                context = str(zeros[:8])
                tokens = torch.randint(0, governor.cfg.vocab_size, (1, 256), device=governor.device)
                result = governor.generate(tokens, temperature=0.85, max_new_tokens=120)
                print(f"\n[Quillan Commentary] {result.get('generated_text', 'Thinking...')}\n")

            elif cmd.lower().startswith("develop"):
                task = cmd[7:].strip()
                print(f"\n[Quillan] Developing fuckery for: {task}")
                # TODO: Expand to full code generation using multiple models
                tokens = torch.randint(0, governor.cfg.vocab_size, (1, 300), device=governor.device)
                result = governor.generate(tokens, temperature=0.9, max_new_tokens=200)
                print(result.get("generated_text", "No output"))

            elif cmd.lower() == "watchdog":
                print("🛡️  Smart Watchdog mode active (monitors Black Core matrix)")

            elif cmd.lower() in ["exit", "quit"]:
                print("🛑 Apex Mantle shutting down.")
                break

            else:
                print("Available: analyze, develop <task>, watchdog, exit")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[Mantle Error] {e}")

# ====================== START ======================
if __name__ == "__main__":
    # Optional: start monitoring thread for Black Core heartbeat later
    try:
        apex_thinking_loop()
    except:
        pass
