# enc_qubit_cloning.py — Complete User Manual

> Encrypted Qubit Cloning — Security Analysis & Live Demonstration  
> Faithful implementation of Yamaguchi & Kempf (PRL 2026) + adversarial extensions  
> arXiv:2501.02757 · arXiv:2602.10695

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [CLI Reference](#cli-reference)
- [Experiments](#experiments)
  - [1–4 — Physics (Yamaguchi et al.)](#experiments-1-4--physics-yamaguchi-et-al)
  - [5–9 — Security Extensions](#experiments-5-9--security-extensions)
- [Backends](#backends)
- [Output Files](#output-files)
- [Plotting](#plotting)
  - [Individual Figures](#individual-figures)
  - [Backend Comparison Figures](#backend-comparison-figures)
- [Circuit Diagrams](#circuit-diagrams)
- [Persistence — save and load](#persistence--save-and-load)
- [Live Demo Commands](#live-demo-commands)
- [Suggested Calls per Scenario](#suggested-calls-per-scenario)

---

## Prerequisites

```
Python 3.11 or 3.12
qiskit >= 2.4.0, < 3.0.0
qiskit-aer >= 0.17.0
qiskit-ibm-runtime >= 0.35.0
numpy >= 1.26.0
matplotlib >= 3.8.0
```

Install with:

```bash
pip install -r requirements.txt
```

IBM credentials required only for `--backend real`. Store them in `.env`:

```
IBM_QUANTUM_TOKEN=your_token
IBM_QUANTUM_INSTANCE=ibm-q/open/main
```

Or as a CRN (newer IBM accounts):

```
IBM_QUANTUM_INSTANCE=crn:v1:bluemix:public:quantum-computing:us-east:...
```

---

## Quick Start

```bash
# Verify the implementation is correct — always run this first on a new machine
python enc_qubit_cloning.py --verify

# The central demonstration in 20 seconds (no IBM account needed)
python enc_qubit_cloning.py -e 5 --n 2 --backend ideal --no-verify
```

Expected output for the central demonstration:

```
  A · Honest (enc + dec)          Fe = 1.0000  ✓ normal operation
  B · Victim (enc, no key)        Fe = 0.2539  ✗ RANSOMWARE VICTIM
  C · Adversary (with key)        Fe = 1.0000  ⚠ attacker profits
  Δ Fe (victim vs honest): -0.7461
```

---

## CLI Reference

### Core flags

| Flag | Default | Description |
|---|---|---|
| `-e`, `--experiment` | `1` | Experiment to run: `1`–`9`, `all`, `security` |
| `--backend` | `ideal` | `ideal`, `nisq`, or `real` |
| `--n` | `2` | Cloning parameter n |
| `--shots` | `4096` | Measurement repetitions per circuit |
| `--sweep` | off | Sweep the primary parameter (n, l, or r) |
| `--plot` | off | Generate PNG figure(s) |
| `--figures-dir` | `figures` | Directory for all PNG output |
| `--no-verify` | off | Skip pre-run protocol check (~5 s saved) |

### Experiment-specific flags

| Flag | Used by | Description |
|---|---|---|
| `--r` | Exp 4 | GHZ qubit count (default: 4) |
| `--l` | Exp 3 | Iteration level (default: 1) |
| `--n-drops` | Exp 7 | Number of dead-drop locations (default: 3) |
| `--activate-drop` | Exp 7 | Which drop Alice activates (default: 0) |

### Infrastructure flags

| Flag | Description |
|---|---|
| `--verify` | Run protocol self-check for n=2,3,4; exit |
| `--list-backends` | List available IBM backends; exit (requires `.env`) |
| `--export-circuits` | Export circuits to `circuits/` (QPY + QASM2); exit |
| `--draw-circuits` | Render circuit diagrams to `--figures-dir`; exit |
| `--draw-style` | `clifford` (default), `bw`, `iqp`, `default` |
| `--draw-dpi` | PNG resolution in DPI (default: 150) |
| `--draw-decompose` | Also save primitive-gate expanded versions |
| `--save-json PATH` | Save result + job IDs to PATH after experiment |
| `--load-json PATH [PATH ...]` | Load saved results instead of running circuits |
| `--ibm-backend` | Backend name or `least-busy` (default) |
| `--token` | IBM API token (overrides `.env`) |
| `--instance` | IBM instance CRN (overrides `.env`) |
| `--creds-file PATH` | JSON file with IBM credentials |

---

## Experiments

### Experiments 1–4 — Physics (Yamaguchi et al.)

These reproduce the four hardware experiments from arXiv:2602.10695.

#### Experiment 1 — Fe vs n

Measures entanglement fidelity Fe as a function of clone count n.  
Key result: Fe decays with **circuit depth**, not with n — the protocol does not dilute quantum information.

```bash
# Single n
python enc_qubit_cloning.py -e 1 --n 3 --backend ideal --shots 4096 --plot --no-verify --figures-dir figures

# Sweep n=2..8 (ideal/nisq) or n=2,3,4 (real — automatically restricted)
python enc_qubit_cloning.py -e 1 --backend ideal --sweep --shots 4096 --plot --no-verify --figures-dir figures

# Save result for later comparison
python enc_qubit_cloning.py -e 1 --n 2 --backend ideal --shots 4096 --no-verify \
  --save-json data/ideal/exp1_n2_ideal.json
```

Output fields: `Fe_BSM`, `Fe_BSM_err`, `Fe_POM`, `Fe_POM_err`, `Fe_UQCM`, `witnessed`, `above_floor`.

#### Experiment 2 — CHSH Violation

Measures the CHSH parameter S under three measurement orderings (Scenarios 2-1, 2-2, 2-3).  
Key result: S > 2 (CHSH violation) for n=2,3 proves the recovered state is genuinely quantum.

```bash
# Single n, all three scenarios
python enc_qubit_cloning.py -e 2 --n 2 --backend ideal --shots 4096 --no-verify

# Sweep n=2,3,4
python enc_qubit_cloning.py -e 2 --backend ideal --sweep --shots 4096 --no-verify
```

Output fields: `scenario`, `S`, `S_err`, `S_UQCM`, `violated`.

> **Note:** S is computed from four correlators (Z×B0, Z×B1, X×B0, X×B1) using the standard CHSH formula. The UQCM theoretical ceiling is shown for comparison; encrypted cloning exceeds it.

#### Experiment 3 — Iterated Cloning

Measures Fe after `l` generations of iterative encrypted cloning.  
Key result: clone count grows as 3^(l+1) while circuit depth grows linearly.

```bash
# Single level l=2
python enc_qubit_cloning.py -e 3 --l 2 --backend ideal --shots 4096 --plot --no-verify --figures-dir figures

# Sweep l=0..3
python enc_qubit_cloning.py -e 3 --backend ideal --sweep --shots 4096 --plot --no-verify --figures-dir figures
```

Output fields: `l`, `n_virtual_clones`, `circuit_depth`, `Fe`, `Fe_err`.

#### Experiment 4 — GHZ Parallel Cloning

Measures GHZ state fidelity Fr after independently cloning each qubit.  
Key result: multipartite entanglement is preserved through enc + dec.

```bash
# Single r
python enc_qubit_cloning.py -e 4 --r 3 --backend ideal --shots 4096 --no-verify

# Sweep r=1..6
python enc_qubit_cloning.py -e 4 --backend ideal --sweep --shots 4096 --no-verify
```

Output fields: `r`, `n_clones`, `Fr`, `Fr_err`, `noise_floor`, `witnessed`, `above_floor`.

---

### Experiments 5–9 — Security Extensions

These are the DEF CON / Quantum Village contributions.

Run all security experiments in one pass:

```bash
python enc_qubit_cloning.py -e security --backend ideal --n 2 \
  --n-drops 4 --activate-drop 1 --shots 4096 --plot --no-verify --figures-dir figures
```

#### Experiment 5 — Quantum Ransomware

Three scenarios measured side-by-side:

| Scenario | Circuit | Expected Fe |
|---|---|---|
| A · Honest | enc + dec + BSM | ≈ 1.00 |
| B · Victim | enc only, no dec, no key | ≈ 0.25 |
| C · Adversary | enc + retained key → dec | ≈ 1.00 |

```bash
# n=2, ideal
python enc_qubit_cloning.py -e 5 --n 2 --backend ideal --shots 4096 --plot --no-verify --figures-dir figures

# n=2,3,4 sweep
python enc_qubit_cloning.py -e 5 --backend ideal --sweep --shots 4096 --plot --no-verify --figures-dir figures

# Save for comparison
python enc_qubit_cloning.py -e 5 --n 2 --backend ideal --shots 4096 --no-verify \
  --save-json data/ideal/exp5_n2_ideal.json
```

Output fields: `Fe_honest`, `Fe_honest_err`, `Fe_victim`, `Fe_victim_err`, `Fe_adversary`, `Fe_adversary_err`.

#### Experiment 6 — Harvest Now, Decrypt Later

Two phases measured:

| Phase | Scenario | Expected Fe |
|---|---|---|
| Phase 1 (T₁) | Adversary holds S_i, no key | ≈ 0.25 |
| Phase 2 (T₂) | Key intercepted, dec applied | ≈ Fe_honest |

```bash
python enc_qubit_cloning.py -e 6 --n 2 --backend ideal --shots 4096 --plot --no-verify --figures-dir figures

python enc_qubit_cloning.py -e 6 --n 2 --backend ideal --shots 4096 --no-verify \
  --save-json data/ideal/exp6_n2_ideal.json
```

Output fields: `Fe_no_key`, `Fe_no_key_err`, `Fe_with_key`, `Fe_with_key_err`, `message`.

#### Experiment 7 — Quantum Dead Drop

Simulates m deposit locations; one is activated by key delivery.

```bash
# 4 drops, activate drop index 1
python enc_qubit_cloning.py -e 7 --n 2 --n-drops 4 --activate-drop 1 \
  --backend ideal --shots 4096 --plot --no-verify --figures-dir figures
```

Output fields: `n_drops`, `Fe_activated`, `Fe_activated_err`, `Fe_inactive`, `Fe_inactive_err`, `drop_index`.

The figure shows: Bloch sphere (before/after key delivery) + bar chart of Fe per drop location.

#### Experiment 8 — Partial Key Attack

Sweeps k from 0 to n, measuring Fe for each level of key completeness.

```bash
# n=2: measures k=0,1,2
python enc_qubit_cloning.py -e 8 --n 2 --backend ideal --shots 4096 --plot --no-verify --figures-dir figures

# n=4: clearest step function for slides
python enc_qubit_cloning.py -e 8 --n 4 --backend ideal --shots 4096 --plot --no-verify --figures-dir figures
```

Output: a `list` of records with fields `k`, `Fe`, `Fe_err`, `theory_Fe`.

> **Security nuance (Gianini et al., arXiv:2604.10155):** The all-or-nothing threshold holds for the case tested here (adversary holds signal qubits + k of n noise qubits). Mixed subsets spanning both S and N from different pairs may retain partial y-Bloch information. Individual clones S_i remain I/2.

#### Experiment 9 — Classical Channel Reduction

No quantum circuits. Prints and optionally plots a structured threat model.

```bash
python enc_qubit_cloning.py -e 9 --plot --no-verify --figures-dir figures
```

Shows four adversary classes mapped to mitigations. No IBM token or backend needed.

---

## Backends

| `--backend` | What it runs on | IBM account needed |
|---|---|---|
| `ideal` | `AerSimulator(method="statevector")` — noiseless | No |
| `nisq` | `AerSimulator` with depolarizing noise (1q: 0.1%, 2q: 1%) or `FakeKingstonV2` | No |
| `real` | Real IBM quantum processor | Yes |

For `--backend real`:

```bash
# Use the least-busy available backend (default)
python enc_qubit_cloning.py -e 5 --backend real --n 2 --shots 4096 --no-verify ...

# Specify a backend by name
python enc_qubit_cloning.py -e 5 --backend real --ibm-backend ibm_brisbane --n 2 ...

# List all available backends first
python enc_qubit_cloning.py --list-backends
```

> **Open Plan budget:** All security experiments (Exp 5–8) for n=2 consume ≈ 24–48 seconds of quantum time. The monthly limit is 600 seconds. Queue wait times are 2–48 hours — collect hardware data days before any presentation.

> **Transient errors:** IBM error 9701 ("Temporary Internal Error") is handled automatically with exponential-backoff retry (up to 5 attempts, starting at 10 s). Non-transient errors are surfaced immediately.

> **Sweep on real hardware:** `--sweep` for Experiment 1 with `--backend real` is automatically restricted to n=2,3,4 to protect the Open Plan budget.

---

## Output Files

### Data files (`--save-json`)

```bash
python enc_qubit_cloning.py -e 5 --n 2 --backend ideal --shots 4096 --no-verify \
  --save-json data/ideal/exp5_n2_ideal.json
```

Each JSON file contains:

```json
{
  "schema_version": "1.1",
  "meta": {
    "experiment": "5",
    "n": 2,
    "shots": 4096,
    "backend_label": "aer_simulator",
    "backend_type": "ideal",
    "timestamp": "2026-05-01T12:00:00Z"
  },
  "result": {
    "Fe_honest": 1.0,
    "Fe_victim": 0.254,
    ...
  },
  "jobs": []
}
```

For real hardware runs, the `jobs` array contains:

```json
{
  "job_id": "cXXXXXXXXXX",
  "circuit_name": "Exp1_BSM_n2",
  "shots": 4096,
  "backend": "ibm_brisbane",
  "counts": {"00": 4083, "01": 4, "10": 5, "11": 4},
  "attempt": 1
}
```

Any `job_id` is independently verifiable at `quantum.ibm.com/jobs/<job_id>`.

### Circuit files (`--export-circuits`)

```bash
python enc_qubit_cloning.py --export-circuits --n 2 --no-verify
```

Produces in `circuits/`:

| File | Format | Contents |
|---|---|---|
| `circuits_n2.qpy` | QPY binary | All 4 circuits in one bundle |
| `enc_dec_n2.qasm` | QASM2 text | Full enc + dec + BSM protocol |
| `ransomware_victim_n2.qasm` | QASM2 text | Enc only (attack circuit) |
| `enc_only_n2.qasm` | QASM2 text | U_enc unitary |
| `dec_only_n2.qasm` | QASM2 text | U_dec unitary |

Reload QPY in any Qiskit project:

```python
from qiskit import qpy
circuits = qpy.load(open("circuits/circuits_n2.qpy", "rb"))
```

---

## Plotting

### Individual Figures

All figures go to `--figures-dir` (default: `figures/`). Use `--figures-dir .` to write to the current directory.

| Experiment | `--plot` generates |
|---|---|
| 1 | `exp1_result.png` — Fe vs n with UQCM ceiling |
| 3 | `exp3_iterated.png` — Fe vs depth and vs clone count |
| 5 | `exp5_ransomware_n{n}.png` — bar chart, three scenarios |
| 6 | `exp6_harvest_n{n}.png` — timeline + bar chart |
| 7 | `exp7_dead_drop_n{n}.png` — Bloch spheres + drop bar chart |
| 8 | `exp8_partial_key_n{n}.png` — step-function plot |
| 9 | `exp9_threat_model.png` — threat model diagram |

### Backend Comparison Figures

After collecting JSON files from multiple backends, load them together:

```bash
# Exp 5 — ideal vs NISQ vs real
python enc_qubit_cloning.py \
  --load-json \
    data/ideal/exp5_n2_ideal.json \
    data/nisq/exp5_n2_nisq.json \
    data/real/exp5_n2_real.json \
  --plot --no-verify --figures-dir figures
```

Produces `compare_exp5.png` — grouped bar chart, one group per scenario, one bar per backend.

```bash
# Exp 6
python enc_qubit_cloning.py \
  --load-json data/ideal/exp6_n2_ideal.json data/real/exp6_n2_real.json \
  --plot --no-verify --figures-dir figures

# Exp 8
python enc_qubit_cloning.py \
  --load-json \
    data/ideal/exp8_n2_ideal.json \
    data/nisq/exp8_n2_nisq.json \
    data/real/exp8_n2_real.json \
  --plot --no-verify --figures-dir figures

# Exp 1 (multiple n values from sweep)
python enc_qubit_cloning.py \
  --load-json data/ideal/exp1_sweep_ideal.json data/real/exp1_n2_real.json \
  --plot --no-verify --figures-dir figures
```

### Load and re-plot a single saved result

```bash
python enc_qubit_cloning.py \
  --load-json data/real/exp5_n2_real.json \
  --plot --no-verify --figures-dir figures
```

---

## Circuit Diagrams

Generate structural circuit diagrams — no IBM account, no backend, no execution:

```bash
# Colour-coded (for slides), 150 dpi
python enc_qubit_cloning.py --draw-circuits --n 2 --figures-dir figures

# Black-and-white, 300 dpi (for print or LaTeX)
python enc_qubit_cloning.py --draw-circuits --n 2 --draw-style bw --draw-dpi 300 --figures-dir figures

# Also emit primitive-gate decomposition (*_decomposed.png)
python enc_qubit_cloning.py --draw-circuits --n 2 --draw-decompose --figures-dir figures

# n=3 for depth comparison slides
python enc_qubit_cloning.py --draw-circuits --n 3 --figures-dir figures
```

Files produced (12 per run, or 24 with `--draw-decompose`):

| File | Shows |
|---|---|
| `uenc_n2.png` | U_enc as a labelled black box |
| `udec_n2.png` | U_dec as a labelled black box |
| `exp1_bsm_n2.png` | Bell state → enc → dec → BSM |
| `exp2_chsh_s22_n2.png` | Exp 2 Scenario 2-2 CHSH circuit |
| `exp3_iterated_l1_n2.png` | One generation of iterated cloning |
| `exp4_ghz_r2_n2.png` | GHZ parallel cloning (r=2) |
| `exp5_honest_n2.png` | Honest protocol baseline |
| `exp5_victim_n2.png` | Ransomware victim — enc, no dec |
| `exp6_phase1_n2.png` | HNDL Phase 1 — no key |
| `exp6_phase2_n2.png` | HNDL Phase 2 — key seized |
| `exp8_fullkey_n2.png` | Partial key, k=n (full recovery) |
| `exp8_partkey_n2.png` | Partial key, k<n (noise floor) |

The high-level diagrams (no `--draw-decompose`) show U_enc and U_dec as labelled boxes — this is intentional for slides. The boxes communicate that the operations are well-defined unitaries without obscuring the protocol structure with gates.

---

## Persistence — save and load

### Collecting data in advance (recommended workflow)

```bash
# Step 1: collect ideal baselines (fast, no IBM)
python enc_qubit_cloning.py -e 5 --n 2 --backend ideal --shots 4096 --no-verify \
  --save-json data/ideal/exp5_n2_ideal.json

# Step 2: collect NISQ baselines (fast, no IBM)
python enc_qubit_cloning.py -e 5 --n 2 --backend nisq --shots 4096 --no-verify \
  --save-json data/nisq/exp5_n2_nisq.json

# Step 3: collect real hardware (submit days before the talk)
python enc_qubit_cloning.py -e 5 --n 2 --backend real --shots 4096 --no-verify \
  --save-json data/real/exp5_n2_real.json

# Step 4: generate comparison figure (no IBM needed)
python enc_qubit_cloning.py \
  --load-json \
    data/ideal/exp5_n2_ideal.json \
    data/nisq/exp5_n2_nisq.json \
    data/real/exp5_n2_real.json \
  --plot --no-verify --figures-dir figures
```

### Displaying pre-collected data during a talk

```bash
# Shows result table and re-generates the figure from the saved JSON
python enc_qubit_cloning.py \
  --load-json data/real/exp5_n2_real.json \
  --plot --no-verify --figures-dir figures
```

---

## Live Demo Commands

These are designed for stage execution in under 90 seconds. All use `--backend ideal` — no IBM connection required.

```bash
# 1. Protocol self-check (~30 s)
python enc_qubit_cloning.py --verify

# 2. Ransomware attack — the central claim (~20 s)
python enc_qubit_cloning.py -e 5 --n 2 --backend ideal --no-verify

# 3. All-or-nothing key threshold (~20 s)
python enc_qubit_cloning.py -e 8 --n 4 --backend ideal --no-verify

# 4. Display pre-collected hardware result with IBM job ID (~5 s)
python enc_qubit_cloning.py --load-json data/real/exp5_n2_real.json --plot --no-verify --figures-dir figures

# 5. Comparison: ideal vs real hardware (~5 s)
python enc_qubit_cloning.py \
  --load-json data/ideal/exp5_n2_ideal.json data/real/exp5_n2_real.json \
  --plot --no-verify --figures-dir figures
```

---

## Suggested Calls per Scenario

The calls below are organised by scenario and backend. Two calls are suggested for each combination: the first is the primary demonstration call (results and/or figure), the second adds persistence or comparison value.

---

### Ideal Simulation `[SIM]`

**Protocol baseline — Exp 1**

> The sweep establishes Fe vs n with the UQCM ceiling; keeps the original `--sweep` you already ran.

```bash
python enc_qubit_cloning.py -e 1 --backend ideal --plot --sweep --shots 4096 \
  --figures-dir figures --save-json data/ideal/exp1_sweep_ideal.json
```

> A single n=2 point produces the same core result faster and is the right choice before a live audience.

```bash
python enc_qubit_cloning.py -e 1 --n 2 --backend ideal --shots 4096 --plot --no-verify \
  --figures-dir figures --save-json data/ideal/exp1_n2_ideal.json
```

---

**Quantum Ransomware — Exp 5**

> The central demonstration: three bars, Fe_victim pinned at 0.25 regardless of n — the physics argument in one figure.

```bash
python enc_qubit_cloning.py -e 5 --n 2 --backend ideal --shots 4096 --plot --no-verify \
  --figures-dir figures --save-json data/ideal/exp5_n2_ideal.json
```

> n=3 shows the same result with a slightly deeper circuit — stronger evidence that the noise floor is protocol-governed, not backend-limited.

```bash
python enc_qubit_cloning.py -e 5 --n 3 --backend ideal --shots 4096 --plot --no-verify \
  --figures-dir figures --save-json data/ideal/exp5_n3_ideal.json
```

---

**Harvest Now, Decrypt Later — Exp 6**

> n=2 produces the cleanest figure; the two-phase bar is the narrative.

```bash
python enc_qubit_cloning.py -e 6 --n 2 --backend ideal --shots 4096 --plot --no-verify \
  --figures-dir figures --save-json data/ideal/exp6_n2_ideal.json
```

> n=3 extends the argument to a slightly richer circuit while still being fast on ideal.

```bash
python enc_qubit_cloning.py -e 6 --n 3 --backend ideal --shots 4096 --plot --no-verify \
  --figures-dir figures --save-json data/ideal/exp6_n3_ideal.json
```

---

**Quantum Dead Drop — Exp 7**

> 4 drops, activate drop 1: gives a 4-bar chart where 3 are at 0.25 and one is at 1.00.

```bash
python enc_qubit_cloning.py -e 7 --n 2 --n-drops 4 --activate-drop 1 \
  --backend ideal --shots 4096 --plot --no-verify \
  --figures-dir figures --save-json data/ideal/exp7_n2_ideal.json
```

> Activating a different drop (index 2) produces the same physics with a different active bar — useful for showing the choice is arbitrary.

```bash
python enc_qubit_cloning.py -e 7 --n 2 --n-drops 4 --activate-drop 2 \
  --backend ideal --shots 4096 --plot --no-verify --figures-dir figures
```

---

**Partial Key Attack — Exp 8**

> n=4 produces the most dramatic step function: four bars at 0.25 then one at 1.00.

```bash
python enc_qubit_cloning.py -e 8 --n 4 --backend ideal --shots 4096 --plot --no-verify \
  --figures-dir figures --save-json data/ideal/exp8_n4_ideal.json
```

> This is also the command already used in the existing demo set — it is worth keeping exactly as-is.

```bash
python enc_qubit_cloning.py -e 8 --backend real --n 2 --shots 4096 --plot --no-verify \
  --figures-dir figures --save-json data/real/exp8_n2_real.json
```

> *(The second call here is a real-hardware variant of n=2. Keep it in the suggested set as the hardware evidence companion to the ideal n=4 call.)*

---

### NISQ Simulation `[NISQ]`

**Protocol baseline — Exp 1**

> The NISQ sweep shows how Fe degrades realistically with n before committing any IBM budget.

```bash
python enc_qubit_cloning.py -e 1 --backend nisq --sweep --shots 4096 --plot --no-verify \
  --figures-dir figures --save-json data/nisq/exp1_sweep_nisq.json
```

> A single n=2 NISQ point is the minimal reference for backend comparison figures.

```bash
python enc_qubit_cloning.py -e 1 --n 2 --backend nisq --shots 4096 --no-verify \
  --save-json data/nisq/exp1_n2_nisq.json
```

---

**Quantum Ransomware — Exp 5**

> The NISQ n=2 run shows that Fe_victim ≈ 0.25 holds under hardware-realistic noise — the key reproducibility claim.

```bash
python enc_qubit_cloning.py -e 5 --n 2 --backend nisq --shots 4096 --plot --no-verify \
  --figures-dir figures --save-json data/nisq/exp5_n2_nisq.json
```

> n=3 with NISQ shows Fe_honest dropping (circuit is deeper) while Fe_victim stays at 0.25 — the indistinguishability argument becomes visually clearer.

```bash
python enc_qubit_cloning.py -e 5 --n 3 --backend nisq --shots 4096 --plot --no-verify \
  --figures-dir figures --save-json data/nisq/exp5_n3_nisq.json
```

---

**Partial Key Attack — Exp 8**

> n=2 NISQ: confirms the step function survives realistic noise.

```bash
python enc_qubit_cloning.py -e 8 --n 2 --backend nisq --shots 4096 --plot --no-verify \
  --figures-dir figures --save-json data/nisq/exp8_n2_nisq.json
```

> n=3 NISQ: wider step function, still clean. Used in the comparison figure with real hardware.

```bash
python enc_qubit_cloning.py -e 8 --n 3 --backend nisq --shots 4096 --plot --no-verify \
  --figures-dir figures --save-json data/nisq/exp8_n3_nisq.json
```

---

### Real IBM Hardware `[HW]`

> ⚠️ Queue wait times are 2–48 hours. Submit these days before any talk. Each command below stays well within the 600 s/month Open Plan budget.

**Protocol baseline — Exp 1 (run this first)**

> This is the control that proves the backend is functional. If Fe_BSM < 0.5 for n=2 on the returned backend, request a different one.

```bash
python enc_qubit_cloning.py -e 1 --backend real --n 2 --shots 4096 --plot --no-verify \
  --figures-dir figures --save-json data/real/exp1_n2_real.json
```

> n=3 extends the evidence one step beyond the minimum; useful for the Fe vs n chart.

```bash
python enc_qubit_cloning.py -e 1 --backend real --n 3 --shots 4096 --no-verify \
  --save-json data/real/exp1_n3_real.json
```

---

**Quantum Ransomware — Exp 5**

> n=2 real hardware is the chain-of-custody evidence: Fe_victim ≈ 0.25 with a verifiable IBM job_id. This is the single most important hardware run.

```bash
python enc_qubit_cloning.py -e 5 --backend real --n 2 --shots 4096 --plot --no-verify \
  --figures-dir figures --save-json data/real/exp5_n2_real.json
```

> n=3 is optional but reinforces that the result is independent of n.

```bash
python enc_qubit_cloning.py -e 5 --backend real --n 3 --shots 4096 --no-verify \
  --save-json data/real/exp5_n3_real.json
```

---

**Partial Key Attack — Exp 8**

> This call is already in your existing command set. For real hardware n=2, k sweeps {0,1,2} — three circuits, well within budget.

```bash
python enc_qubit_cloning.py -e 8 --backend real --n 2 --shots 4096 --plot --no-verify \
  --figures-dir figures --save-json data/real/exp8_n2_real.json
```

> After this, generate the comparison figure without any IBM connection:

```bash
python enc_qubit_cloning.py \
  --load-json \
    data/ideal/exp8_n2_ideal.json \
    data/nisq/exp8_n2_nisq.json \
    data/real/exp8_n2_real.json \
  --plot --no-verify --figures-dir figures
```
