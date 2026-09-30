# Aerospace Maintenance Intelligence Agent

An assistant that answers UAV fault reports using the maintenance history of
the fleet, remembered and recalled via [Hindsight](https://github.com/vectorize-io/hindsight)
agent memory.

Without memory: "UAV-264 has high-RPM motor vibration and it's on a batch
M-B7 motor. What should we check?" gets a generic checklist.

With memory: the agent recalls that batch M-B7 motors have a recurring
bearing-wear pattern in the 44–52 flight-hour range across several aircraft,
and that motor replacement alone hasn't fixed similar cases before — and
leads with that, citing the specific prior reports it's drawing from.

## The problem

Maintenance teams produce a steady stream of inspection reports, fault
notes, component swaps, and technician observations. The useful signal is
usually buried: the last time this exact airframe, or this exact component
batch, had this problem, and what actually fixed it. When that history
lives across scattered logs, it's hard to retrieve at the moment it matters.

**All data in this repository is synthetic**, written by hand to plant
realistic, checkable patterns rather than pulled from real fleet records.

## How it works

```
Technician report ──▶ retain() ──▶ Hindsight memory bank
                                          │
Technician question ──▶ recall() ────────┤
                                          ▼
                                     reflect()
                                          │
                                          ▼
                               Answer + cited evidence
```

The agent talks to a Hindsight memory bank through three operations:

| Command | What it does | Hindsight call |
|---|---|---|
| `log` | Stores a new maintenance report, event-timestamped | `retain()` |
| `ask` | Answers a fault question, citing prior evidence | `reflect()` |
| `demo` | Runs a small built-in scenario, with and without memory | `retain()`, `reflect()` |

The recalled evidence — the actual retained report text — is always
available separately from the final answer, via `recall()`. This is what
makes every citation checkable: the answer and the evidence behind it are
never the same call.

### Design decisions

- **One bank per fleet.** Aircraft identity (`UAV-###`) is in the report
  text and the retained context, not a separate index. Hindsight's keyword
  and entity-aware search keeps identifiers from blurring across aircraft
  with similar symptoms.
- **A mission, not just a prompt.** The bank is created with a fixed
  mission string that defines the agent's role and its "advisory only"
  boundary — this travels with the bank, not just a single call.
- **Real event dates.** Reports are retained with the date the event
  actually happened, not the date they were loaded, so ordering and
  hour/cycle patterns stay meaningful.
- **"No relevant history" is a valid answer.** The agent is instructed to
  say so rather than generalize as if it had evidence it doesn't.
- **Evidence ships with every answer.** In the CLI this means running
  `recall()` alongside `reflect()`; in the web UI this is a dedicated panel
  next to the chat, so a technician can verify a claim without digging
  through logs.

## The dataset

`load_dataset.py` seeds a fresh bank (`uav-fleet-v2`) with 29 hand-written
inspection and routine-check reports across 8 aircraft, with five patterns
planted on purpose:

- **Loose motor mount screws** causing intermittent vibration at low-to-mid
  throttle — replacing the motor alone doesn't fix it.
- **Bearing wear at ~44–52 flight hours** on motors from batch **M-B7**.
- **ESC overheating** in hot weather (ambient 39–42°C) — duct cleaning
  alone sometimes doesn't hold.
- **Compass drift** from power cables routed near the compass module.
- **Battery cell imbalance** after ~140–160 charge cycles.

The dataset is small enough to audit by hand: every claim the agent makes
can be checked against the 29 source reports directly.

## Quick start

Requirements: Python 3.10+, a Hindsight API key, and an LLM provider key
(this project uses Groq by default).

**1. Install dependencies**
```
pip install -r requirements.txt
```

**2. Set environment variables** (in a `.env` file, never committed)
```
HINDSIGHT_API_KEY=your-key-here
GROQ_API_KEY=your-key-here
```

**3. Seed the memory bank** (run once)
```
python load_dataset.py
```
This stores all 29 reports into the `uav-fleet-v2` bank. Each report goes
through LLM extraction on Hindsight's side, so this takes a few minutes.
A `loaded_dataset.flag` file prevents accidental re-seeding — delete it
only if you intentionally want to reload from scratch (use a new bank name
to avoid duplicating data).

**4. Ask questions from the CLI**
```
python uav_agent_code.py ask "UAV-264 has motor vibration at 49 flight hours on batch M-B7. What should we check?"
python uav_agent_code.py log "UAV-264 - bearing replaced on motor 2 after grinding noise at 50 flight hours. Motor from batch M-B7. Resolved."
python uav_agent_code.py demo
```

**5. Or run the web UI**
```
streamlit run streamlit_app.py
```
Two tabs: **Ask**, with the agent's guidance next to a "memory used" panel
showing the exact reports it recalled; and **Log new report**, which stores
a new report immediately, available to the very next question — the
learning loop, end to end.

## Configuration

| Setting | Where | Notes |
|---|---|---|
| Hindsight server URL | `BASE_URL` in `uav_agent_code.py` | Defaults to Hindsight Cloud |
| API keys | Environment variables | Never commit real keys |
| Bank ID | `BANK` in `uav_agent_code.py` and `load_dataset.py` | Must match in both files |
| Mission | `MISSION` in `uav_agent_code.py` | Defines the agent's role and advisory-only behavior |
| Seed dataset | `REPORTS` in `load_dataset.py` | 29 reports across 8 aircraft |

## Limitations and next steps

- `reflect()` is a synchronous LLM call; a production path should push
  ingestion (`retain()`) to a background job.
- The "advisory only, technician decides" rule lives in the mission string;
  it's not (yet) a hard, non-negotiable guardrail enforced in code.
- Answers are generated and should be reviewed against the recalled
  evidence, not acted on directly — the memory panel exists specifically
  to make that review fast.
- Tested at prototype scale (29 reports, 8 aircraft); recall behavior at
  real-fleet scale hasn't been measured.

## Prototype Execution Video: "https://www.youtube.com/watch?v=qVlc_u8FFZo"

## Learn more

- [Hindsight on GitHub](https://github.com/vectorize-io/hindsight)
- [Hindsight documentation](https://hindsight.vectorize.io/)
- [What is agent memory?](https://vectorize.io/what-is-agent-memory)
