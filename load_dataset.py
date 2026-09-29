"""Load a synthetic UAV fleet maintenance history into Hindsight (run once)."""
import os, sys, time
from datetime import datetime
from dotenv import load_dotenv
from hindsight_client import Hindsight

load_dotenv()
sys.stdout.reconfigure(encoding="utf-8")

client = Hindsight(base_url="https://api.hindsight.vectorize.io",
                   api_key=os.environ["HINDSIGHT_API_KEY"])
BANK = "uav-fleet-v2"
FLAG = "loaded_dataset.flag"

REPORTS = [
    ("2026-01-08", "inventory audit", "UAV-204 - motor inventory audit: all four installed motors are new units from batch M-B7."),
    ("2026-01-14", "inspection report", "UAV-132 - intermittent motor vibration at mid throttle after 31 flight hours. Motor replaced but vibration persisted. Motor mount screws then found loose on arm 2 and re-torqued with thread locker. Vibration gone. Original motor tested fine and returned to stock."),
    ("2026-01-22", "routine check", "UAV-158 - 50-hour scheduled inspection. All motors within vibration limits. ESC temperatures nominal. Battery pack 2 shows 40 mV cell imbalance, logged for monitoring."),
    ("2026-02-03", "inspection report", "UAV-219 - motor 1 vibration with grinding noise at high RPM after 52 flight hours. Motor from batch M-B7. Bearing replaced."),
    ("2026-02-10", "inspection report", "UAV-233 - high-RPM vibration on motor 4 at 49 flight hours with audible bearing whine. Motor from batch M-B7. Bearing replaced."),
    ("2026-02-18", "inspection report", "UAV-247 - ESC 2 overheated and triggered thermal cutback in hot weather (ambient 41 C). Airflow duct partially blocked with dust; cleaned. Resolved."),
    ("2026-02-25", "inspection report", "UAV-101 - compass heading drift after takeoff. Battery power cable was routed close to the compass module. Cable rerouted and ferrite ring added, compass recalibrated. Drift gone."),
    ("2026-03-02", "routine check", "UAV-117 - 60-hour check after motor mount screw repair. Vibration normal across the throttle range. No thermal issues."),
    ("2026-03-05", "inspection report", "UAV-233 - preventive bearing replacement on motors 1-3 (batch M-B7) at 55 flight hours after motor 4 failed early. No defects found but bearings showed early wear."),
    ("2026-03-19", "inspection report", "UAV-158 - intermittent vibration at low-to-mid throttle at 28 flight hours. Motor mount screws loose on arm 3; re-torqued with thread locker. Bearings inspected, no defect."),
    ("2026-03-27", "inspection report", "UAV-132 - GPS position wandered during hover. Power cable near the flight controller rerouted and shielded. Issue resolved."),
    ("2026-04-04", "inspection report", "UAV-247 - battery pack voltage sagging under load after 152 charge cycles. Pack retired and replaced."),
    ("2026-04-11", "routine check", "UAV-233 - post-repair check at 88 flight hours. Vibration normal, no bearing noise."),
    ("2026-04-19", "inspection report", "UAV-219 - propeller on motor 2 chipped after a minor ground strike. Propeller replaced and rebalanced. Vibration normal afterwards."),
    ("2026-04-28", "inspection report", "UAV-101 - ESC 1 overheating in hot-weather flights (ambient 39 C). Thermal paste reapplied and airflow duct cleaned. Resolved."),
    ("2026-05-06", "inspection report", "UAV-158 - ESC 3 thermal cutback at ambient 40 C. Duct cleaned and thermal paste reapplied, but cutback recurred on the next hot day. ESC replaced, problem resolved."),
    ("2026-05-14", "routine check", "UAV-204 - 70-hour check. Motor vibration normal at cruise and high RPM. Mount screw torque verified."),
    ("2026-05-22", "inspection report", "UAV-132 - motor 1 vibration at high RPM at 46 flight hours. Motor from batch M-B7. Mount screws checked and tight. Bearing replaced."),
    ("2026-06-02", "inspection report", "UAV-247 - high-RPM vibration on motor 2 at 51 flight hours. Motor from batch M-B7. Mount screws tight. Bearing replaced."),
    ("2026-06-09", "inspection report", "UAV-219 - compass drift and jittery heading after an arm replacement. Power cable routed near the compass again. Rerouted with ferrite ring; resolved."),
    ("2026-07-08", "inspection report", "UAV-158 - motor vibration at 55 flight hours, worse during throttle changes. One mount screw had backed out again despite thread locker. Replaced with new self-locking screws. Resolved."),
    ("2026-07-15", "inspection report", "UAV-101 - motor vibration at low throttle after transport in a vehicle. Mount screws loose on arm 1; re-torqued. Technician recommends torque check after every transport."),
    ("2026-07-22", "inspection report", "UAV-247 - ESC 2 overheating again in hot weather (ambient 42 C). Duct cleaned and firmware updated to reduce peak current. Resolved."),
    ("2026-08-01", "inspection report", "UAV-117 - ESC 3 overheating in hot weather (ambient 40 C). Duct cleaned and thermal paste reapplied. Resolved."),
    ("2026-08-16", "routine check", "UAV-219 - post-repair check at 95 flight hours. Vibration normal at cruise; slight bearing noise on motor 1 at max RPM, monitor."),
    ("2026-08-24", "inspection report", "UAV-132 - propeller nut loose on motor 2 causing mild vibration at all throttle settings. Nut re-torqued and lock-nut replaced."),
    ("2026-09-03", "inspection report", "UAV-233 - battery pack 1 cell imbalance of 90 mV at 140 cycles. Pack balanced; replaced at 160 cycles when imbalance returned."),
    ("2026-09-10", "routine check", "UAV-158 - 100-hour check. Vibration normal. Replacement ESC 3 temperatures nominal at 39 C ambient. Battery pack 2 retired due to persistent cell imbalance."),
    ("2026-09-17", "routine check", "UAV-101 - 80-hour check. Vibration normal, no bearing noise. Motors are from batch M-C2. Mount screw torque verified."),
]

def store(date, ctx, text):
    for attempt in range(3):
        try:
            client.retain(bank_id=BANK, content=text, context=ctx,
                          timestamp=datetime.fromisoformat(date).isoformat())
            return True
        except Exception as e:
            print(f"   retry {attempt + 1}: {e}")
            time.sleep(3)
    return False

def main():
    if os.path.exists(FLAG):
        print("Already loaded. Delete loaded_dataset.flag only if you want duplicates.")
        return
    failed = 0
    for i, (date, ctx, text) in enumerate(REPORTS, 1):
        ok = store(date, ctx, text)
        failed += not ok
        print(f"[{i}/{len(REPORTS)}] {'stored' if ok else 'FAILED'}: {text[:60]}...")
    open(FLAG, "w").write("done")
    print(f"\nDone. {len(REPORTS) - failed} stored, {failed} failed.")

if __name__ == "__main__":
    try:
        main()
    finally:
        client.close()