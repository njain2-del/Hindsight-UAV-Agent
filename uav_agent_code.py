import os, sys, requests
from datetime import datetime
from dotenv import load_dotenv
from hindsight_client import Hindsight

load_dotenv()
sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "https://api.hindsight.vectorize.io"
client = Hindsight(base_url=BASE_URL, api_key=os.environ["HINDSIGHT_API_KEY"])

BANK = "uav-fleet-maintenance"
MISSION = (
    "I am a maintenance intelligence assistant for a UAV fleet. When a fault is "
    "reported, I use the maintenance history of that specific aircraft and component "
    "(prior faults, replaced parts, technician observations) to prioritise inspection "
    "steps. I cite the prior events I rely on. I only give advisory guidance; "
    "airworthiness decisions belong to certified technicians. If there is no relevant "
    "history, I say so and give general guidance."
)

HISTORY = [
    (datetime(2026, 3, 12), "inspection report",
     "UAV-204 - motor vibration increased after 47 flight hours. Bearing replaced. "
     "Technician noted vibration was worse at high RPM."),
    (datetime(2026, 5, 2), "inspection report",
     "UAV-117 - ESC overheating on motor 3 during hot-weather flights. "
     "Thermal paste reapplied, airflow duct cleaned. Resolved."),
    (datetime(2026, 6, 20), "inspection report",
     "UAV-117 - motor vibration traced to loose motor mount screws. "
     "Screws re-torqued with thread locker. Bearings checked, no defect."),
    (datetime(2026, 8, 9), "routine check",
     "UAV-204 - post-repair check at 95 flight hours. Vibration normal at cruise; "
     "slight bearing noise at max RPM, monitor."),
]

def ensure_bank(bank_id, name):
    for kwargs in ({"mission": MISSION}, {}):   # fall back if 'mission' isn't supported
        try:
            client.create_bank(bank_id=bank_id, name=name, **kwargs)
            return
        except TypeError:
            continue
        except Exception as e:                   # e.g. bank already exists
            print(f"(create_bank: {e})")
            return

def seed():
    ensure_bank(BANK, "UAV Fleet Maintenance")
    if client.recall(bank_id=BANK, query="UAV-204").results:
        print("Bank already seeded, skipping.")
        return
    for ts, ctx, text in HISTORY:
        client.retain(bank_id=BANK, content=text, context=ctx, timestamp=ts.isoformat())
    print(f"Seeded {len(HISTORY)} reports.")

def log(report):
    client.retain(bank_id=BANK, content=report, context="inspection report",
                  timestamp=datetime.now().isoformat())
    print("Stored.")

def ask(question):
    return client.reflect(bank_id=BANK, query=question).text

def generic_ai(question):
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}"},
        json={"model": "openai/gpt-oss-120b",
              "messages": [
                  {"role": "system", "content": "You are a UAV maintenance assistant."},
                  {"role": "user", "content": question}]},
        timeout=60)
    return r.json()["choices"][0]["message"]["content"]

def demo():
    seed()
    q = "UAV-204 has high motor vibration again. What should we check?"
    print(f"\nQ: {q}\n\n--- Generic AI (no memory) ---\n{generic_ai(q)}")
    print(f"\n--- Memory-enabled agent ---\n{ask(q)}")
    print("\n--- Raw recall (evidence) ---")
    for r in client.recall(bank_id=BANK, query="UAV-204 motor vibration").results[:5]:
        print("-", r.text)

if __name__ == "__main__":
    try:
        cmd, *rest = sys.argv[1:] or ["demo"]
        {"demo": demo, "log": lambda: log(" ".join(rest)),
         "ask": lambda: print(ask(" ".join(rest)))}[cmd]()
    finally:
        client.close()