```
  ██████╗██╗      ██████╗ ███╗   ██╗██╗███╗   ██╗ ██████╗ 
 ██╔════╝██║     ██╔═══██╗████╗  ██║██║████╗  ██║██╔════╝ 
 ██║     ██║     ██║   ██║██╔██╗ ██║██║██╔██╗ ██║██║  ███╗
 ██║     ██║     ██║   ██║██║╚██╗██║██║██║╚██╗██║██║   ██║
 ╚██████╗███████╗╚██████╔╝██║ ╚████║██║██║ ╚████║╚██████╔╝
  ╚═════╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝╚═╝  ╚═══╝ ╚═════╝ 

 ███████╗███╗   ██╗ ██████╗██████╗ ██╗   ██╗██████╗ ████████╗███████╗██████╗ 
 ██╔════╝████╗  ██║██╔════╝██╔══██╗╚██╗ ██╔╝██╔══██╗╚══██╔══╝██╔════╝██╔══██╗
 █████╗  ██╔██╗ ██║██║     ██████╔╝ ╚████╔╝ ██████╔╝   ██║   █████╗  ██║  ██║
 ██╔══╝  ██║╚██╗██║██║     ██╔══██╗  ╚██╔╝  ██╔═══╝    ██║   ██╔══╝  ██║  ██║
 ███████╗██║ ╚████║╚██████╗██║  ██║   ██║   ██║        ██║   ███████╗██████╔╝
 ╚══════╝╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═╝        ╚═╝   ╚══════╝╚═════╝ 

  ██████╗ ██╗   ██╗██████╗ ██╗████████╗███████╗
 ██╔═══██╗██║   ██║██╔══██╗██║╚══██╔══╝██╔════╝
 ██║   ██║██║   ██║██████╔╝██║   ██║   ███████╗
 ██║▄▄ ██║██║   ██║██╔══██╗██║   ██║   ╚════██║
 ╚██████╔╝╚██████╔╝██████╔╝██║   ██║   ███████║
  ╚══▀▀═╝  ╚═════╝ ╚═════╝ ╚═╝   ╚═╝   ╚══════╝

  Encrypted Qubit Cloning — Security Analysis & Live Demonstration
  Faithful implementation of Yamaguchi & Kempf (PRL 2026) + adversarial extensions
  arXiv:2501.02757  ·  arXiv:2602.10695
```

<div align="center">

[![Talk](https://img.shields.io/badge/CryptoRave%202026-Talk%20DYKJPZ-02470d?style=for-the-badge&logo=slides&logoColor=white)](https://cpa.cryptorave.org/cryptorave-2026/talk/DYKJPZ/)
[![Talk](https://img.shields.io/badge/BSidesSP%202026-Quantum%20Village-0A2540?style=for-the-badge&logo=slides&logoColor=white)](https://securitybsides.com.br/2026/quantum-village-br/)
[![arXiv theory](https://img.shields.io/badge/arXiv-2501.02757-b31b1b?style=for-the-badge&logo=arxiv&logoColor=white)](https://arxiv.org/abs/2501.02757)
[![arXiv hardware](https://img.shields.io/badge/arXiv-2602.10695-b31b1b?style=for-the-badge&logo=arxiv&logoColor=white)](https://arxiv.org/abs/2602.10695)
[![IBM Quantum](https://img.shields.io/badge/IBM%20Quantum-Verified-1e49be?style=for-the-badge&logo=ibm&logoColor=white)](https://quantum.ibm.com)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776ab?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

**"You can't clone a qubit — unless you encrypt it first."**

*Presented at [CryptoRave 2026](https://cpa.cryptorave.org/cryptorave-2026/talk/DYKJPZ/) · May 9, 2026*

*Presented at [BSidesSP 2026](https://securitybsides.com.br/2026/quantum-village-br/) · May 17, 2026*

</div>

---

## Table of Contents

- [The One-Sentence Idea](#the-one-sentence-idea)
- [Why This Matters for Security](#why-this-matters-for-security)
- [The Physics — Concisely](#the-physics--concisely)
- [What This Repository Contains](#what-this-repository-contains)
- [Quick Start](#quick-start)
- [Environment Setup (Windows)](#environment-setup-windows)
- [Environment Setup (Linux / macOS)](#environment-setup-linux--macos)
- [IBM Quantum Credentials](#ibm-quantum-credentials)
- [Running the Experiments](#running-the-experiments)
  - [Group 0 — Verification & Export](#group-0--verification--export)
  - [Group 1 — Ideal Simulation](#group-1--ideal-simulation-permanent-baselines)
  - [Group 2 — NISQ Simulation](#group-2--nisq-simulation-noise-realistic)
  - [Group 3 — Real IBM Hardware](#group-3--real-ibm-hardware)
  - [Group 4 — Backend Comparison Plots](#group-4--backend-comparison-plots)
  - [Group 5 — Live Demo Commands](#group-5--live-demo-commands)
- [Experiment Descriptions](#experiment-descriptions)
- [Security Attack Scenarios](#security-attack-scenarios)
- [Provenance & Reproducibility](#provenance--reproducibility)
- [Repository Structure](#repository-structure)
- [Results Summary](#results-summary)
- [References](#references)
- [About the Author](#about-the-author)

---

## The One-Sentence Idea

The no-cloning theorem forbids copying an unknown quantum state — but it says nothing about creating *encrypted* copies, each individually indistinguishable from random noise, yet each perfectly recoverable by whoever holds the complete noise-qubit key.

---

## Why This Matters for Security

The no-cloning theorem is treated as an **axiom of security** by every QKD protocol ever deployed. Encrypted cloning does not break that theorem — it demonstrates that the theorem can be made to work *against* the legitimate user by whoever performs the encryption.

This repository models and demonstrates four concrete attack scenarios that follow directly from this observation:

| # | Scenario | Adversary | Key Property Exploited |
|---|----------|-----------|----------------------|
| 5 | **Quantum Ransomware** | Malicious quantum cloud | `ρ_Si = I/2` is indistinguishable from hardware decoherence |
| 6 | **Harvest Now, Decrypt Later** | Nation-state / APT | Quantum memory + unprotected classical key channel |
| 7 | **Quantum Dead Drop** | Intelligence asset | Holevo bound: zero extractable bits from `ρ = I/2` |
| 8 | **Partial Key Threshold** | Any adversary | `k < n` noise qubits → channel capacity = 0, exactly |

Every attack reduces to the same root cause: **the classical channel used to deliver the noise qubits `{N_i}` is the sole attack surface**. The quantum channel carrying the encrypted clones `{S_i}` is unconditionally secure by the Holevo bound — no adversary, classical or quantum, extracts information from it.

---

## The Physics — Concisely

### Protocol (Yamaguchi & Kempf, PRL 2026)

**Setup:** *n* Bell pairs `(S_i, N_i)` initialised as `|φ⟩ = (|00⟩+|11⟩)/√2`. Qubit `A` holds the unknown state `|ψ⟩`.

**Encryption** (`U_enc` acts on `A` and all `S_i`; `N_i` are never touched):

```
U_enc = exp(-πi/4 · σ₁^(A) ⊗ ⊗ᵢσ₁^(Sᵢ)) · exp(-πi/4 · σ₃^(A) ⊗ ⊗ᵢσ₃^(Sᵢ))
```

After `U_enc`, the state of the full system is:

```
U_enc |ψ⟩_A ⊗ |φ⟩^⊗n = (1/2) Σ_{μ=0}^{3} α_μ⁻¹ σ_μ^(A)|ψ⟩ ⊗ |φ_μ⟩^⊗n
```

**Each encrypted clone is maximally mixed:**

```
ρ_{S_j} = (1/4) Σ_μ |φ_μ^{S_j}⟩⟨φ_μ^{S_j}| = I/2   (independent of |ψ⟩)
```

By the **Holevo bound**: zero classical bits about `|ψ⟩` are extractable from `S_j` by any quantum measurement.

**Decryption** (`U_dec` on chosen clone `S_j` and all `{N_i}`):

```
U_dec(S_j, N_1...N_n) → |ψ⟩ on S_j    with Fe = 1, exactly
```

The noise qubits are **consumed** — only one decryption is possible, consistent with no-cloning.

**All-or-nothing key property:**  For `k < n` noise qubits, `ρ_{S_j, N_1,...,N_k}` is still independent of `|ψ⟩` — the quantum channel capacity drops to exactly zero. Missing a single noise qubit is mathematically identical to having none.

### Gate count (linear in n)

| Operation | 2-qubit gates | Depth |
|-----------|---------------|-------|
| `U_enc` | `4n` | `2n` |
| `U_dec` | `15n + 7` | `~5n` |
| Total | `~21n + 11` | `~7n` |

---

## What This Repository Contains

```
encrypted_qubit_cloning/
├── enc_qubit_cloning.py   ← Main script: all 9 experiments + CLI
├── requirements.txt                ← Pinned dependencies
├── .env.example                    ← Template for IBM Quantum credentials
├── .gitignore
├── LICENSE
│
├── circuits/                       ← Circuit exports (QPY + QASM2)
│   ├── circuits_n2.qpy             ← QPY bundle (4 circuits, lossless)
│   ├── circuits_n3.qpy
│   ├── circuits_n4.qpy
│   ├── enc_dec_n2.qasm             ← Human-readable OpenQASM 2.0
│   ├── enc_only_n2.qasm
│   ├── dec_only_n2.qasm
│   └── ransomware_victim_n2.qasm
│
├── data/
│   ├── ideal/                      ← Deterministic simulator baselines [SIM]
│   │   ├── exp1_sweep_ideal.json
│   │   ├── exp5_n2_ideal.json      ← Ransomware: Fe_honest=1.000, Fe_victim=0.254
│   │   ├── exp8_n4_ideal.json      ← Partial key: step function at k=n
│   │   └── ...
│   ├── nisq/                       ← Depolarizing noise model [NISQ]
│   │   └── ...
│   └── real/                       ← Real IBM hardware [HW] ← IBM job IDs here
│       ├── exp1_n2_real.json       ← job_id verifiable at quantum.ibm.com
│       ├── exp5_n2_real.json
│       └── ...
│
└── figures/                        ← All publication-quality PNG figures
    ├── exp5_ransomware_n2.png
    ├── exp6_harvest_n3.png
    ├── exp7_dead_drop_n2.png
    ├── exp8_partial_key_n4.png
    ├── exp9_threat_model.png
    ├── compare_exp5_backends.png   ← ideal vs NISQ vs real hardware
    └── ...
```

---

## Quick Start

```bash
# Clone
git clone https://github.com/jullyanolino/encrypted_qubit_cloning.git
cd encrypted_qubit_cloning

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate          # Linux/macOS
# .venv\Scripts\Activate.ps1       # Windows PowerShell

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify everything works (no IBM account needed)
python enc_qubit_cloning.py --verify
```

Expected output:
```
Protocol verification  n=2  → PASSED  ✓ U_enc unitary  ✓ U_dec unitary  ✓ Fe=1.0000
Protocol verification  n=3  → PASSED
Protocol verification  n=4  → PASSED
All checks passed.
```

**To reproduce the talk's central demonstration in 30 seconds:**

```bash
python enc_qubit_cloning.py -e 5 --n 2 --backend ideal --no-verify
```

```
  A · Honest (enc + dec)          Fe = 1.0000  ✓ normal operation
  B · Victim (enc, no key)        Fe = 0.2539  ✗ RANSOMWARE VICTIM
  C · Adversary (with key)        Fe = 1.0000  ⚠ attacker profits
  Δ Fe (victim vs honest): -0.7461
```

---

## Environment Setup (Windows)

### Prerequisites

Verify Python 3.11 or 3.12 is installed:
```powershell
python --version
python -m pip --version
```

If `python` is not found, install from [python.org](https://python.org) and check **"Add Python to PATH"** during setup.

### Create virtual environment

```powershell
cd C:\path\to\encrypted_qubit_cloning
python -m venv .venv
```

### Activate

```powershell
# PowerShell (one-time policy unlock if needed):
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Activate:
.\.venv\Scripts\Activate.ps1
```

For **Command Prompt**:
```cmd
.venv\Scripts\activate.bat
```

Your prompt will show `(.venv)` when active.

### Install

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Verify

```powershell
python -c "
import qiskit, qiskit_aer, qiskit_ibm_runtime, numpy, matplotlib
print('qiskit            ', qiskit.__version__)
print('qiskit-aer        ', qiskit_aer.__version__)
print('qiskit-ibm-runtime', qiskit_ibm_runtime.__version__)
print('numpy             ', numpy.__version__)
print('matplotlib        ', matplotlib.__version__)
print('All OK.')
"
```

### Deactivate / reactivate

```powershell
deactivate                          # when done
.\.venv\Scripts\Activate.ps1       # when returning
```

---

## Environment Setup (Linux / macOS)

```bash
cd /path/to/encrypted_qubit_cloning
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python enc_qubit_cloning.py --verify
```

---

## IBM Quantum Credentials

Required only for `--backend real`. Create a `.env` file in the project root:

```bash
cp .env.example .env
# Edit .env with your token and instance
```

`.env` contents:

```
IBM_QUANTUM_TOKEN=your_api_token_here
IBM_QUANTUM_INSTANCE=ibm-q/open/main
```

> **Instance format:** `ibm-q/open/main` is the legacy format, still accepted by most accounts. If your IBM Quantum dashboard shows a Cloud Resource Name (CRN) starting with `crn:v1:bluemix:...`, use that value instead. Both formats are supported by the script.

Obtain your token at [quantum.ibm.com](https://quantum.ibm.com) → Account → API token.

> **Note:** `.env` is in `.gitignore` and is never committed. Each real-hardware job produces a `job_id` in the output JSON, verifiable at `quantum.ibm.com/jobs/<job_id>`.

> **Transient errors (9701):** IBM Quantum occasionally returns error code 9701 ("Temporary Internal Error"). The script handles this automatically with exponential-backoff retry: up to 5 attempts, starting with a 10-second wait and doubling each time. No action is needed — if all 5 attempts fail, the script prints a diagnostic message with the error code and a link to IBM's error documentation.

You can also pass credentials as flags:

```bash
python enc_qubit_cloning.py --token <tok> --instance ibm-q/open/main ...
```

---

## Running the Experiments

### Experiment numbering

| # | Name | Type | IBM needed |
|---|------|------|-----------|
| 1 | Fe vs n sweep (core protocol) | Physics | Optional |
| 2 | CHSH violation under interleaving | Physics | Optional |
| 3 | Iterated cloning (series) | Physics | Optional |
| 4 | GHZ parallel cloning | Physics | Optional |
| 5 | **Quantum Ransomware** | Security | Optional |
| 6 | **Harvest Now, Decrypt Later** | Security | Optional |
| 7 | **Quantum Dead Drop** | Security | Optional |
| 8 | **Partial Key Attack** | Security | Optional |
| 9 | **Classical Channel Reduction** | Analysis | No circuits |

---

### Group 0 — Verification & Export

No backend or IBM account required.

```bash
# Protocol self-verification (n=2, 3, 4) — run this first on every machine
python enc_qubit_cloning.py --verify

# List available IBM backends (requires .env)
python enc_qubit_cloning.py --list-backends

# Export circuits to circuits/ (QPY bundle + QASM2 text)
python enc_qubit_cloning.py --export-circuits --n 2 --no-verify
python enc_qubit_cloning.py --export-circuits --n 3 --no-verify
python enc_qubit_cloning.py --export-circuits --n 4 --no-verify

# Draw circuit diagrams as PNG — no IBM account needed
# Produces 12 PNG files: U_enc, U_dec, Exp1-4, Exp5-8 security variants
python enc_qubit_cloning.py --draw-circuits --n 2 --figures-dir figures

# Black-and-white, 300 dpi (for print or LaTeX)
python enc_qubit_cloning.py --draw-circuits --n 2 --draw-style bw --draw-dpi 300 --figures-dir figures

# With decomposed primitive gates (H, CX, Rz) — for Methods slides
python enc_qubit_cloning.py --draw-circuits --n 2 --draw-decompose --figures-dir figures
```

---

### Group 1 — Ideal Simulation (Permanent Baselines)

Deterministic (seeded). Run once, commit, never re-run. These are the `[SIM]` reference values in all figures.

```bash
# ── Core protocol (Experiments 1-4) ──────────────────────────────────────

python enc_qubit_cloning.py \
  -e 1 --backend ideal --sweep --shots 4096 --plot --no-verify \
  --figures-dir figures \
  --save-json data/ideal/exp1_sweep_ideal.json

python enc_qubit_cloning.py \
  -e 2 --backend ideal --n 2 --shots 4096 --no-verify \
  --save-json data/ideal/exp2_n2_ideal.json

python enc_qubit_cloning.py \
  -e 2 --backend ideal --n 3 --shots 4096 --no-verify \
  --save-json data/ideal/exp2_n3_ideal.json

python enc_qubit_cloning.py \
  -e 3 --backend ideal --sweep --shots 4096 --plot --no-verify \
  --figures-dir figures \
  --save-json data/ideal/exp3_sweep_ideal.json

python enc_qubit_cloning.py \
  -e 4 --backend ideal --sweep --shots 4096 --no-verify \
  --save-json data/ideal/exp4_sweep_ideal.json

# ── Security experiments (Experiments 5-9) ──────────────────────────────

python enc_qubit_cloning.py \
  -e 5 --backend ideal --n 2 --shots 4096 --plot --no-verify \
  --figures-dir figures \
  --save-json data/ideal/exp5_n2_ideal.json

python enc_qubit_cloning.py \
  -e 5 --backend ideal --n 3 --shots 4096 --plot --no-verify \
  --figures-dir figures \
  --save-json data/ideal/exp5_n3_ideal.json

python enc_qubit_cloning.py \
  -e 5 --backend ideal --n 4 --shots 4096 --plot --no-verify \
  --figures-dir figures \
  --save-json data/ideal/exp5_n4_ideal.json

python enc_qubit_cloning.py \
  -e 6 --backend ideal --n 2 --shots 4096 --plot --no-verify \
  --figures-dir figures \
  --save-json data/ideal/exp6_n2_ideal.json

python enc_qubit_cloning.py \
  -e 6 --backend ideal --n 3 --shots 4096 --plot --no-verify \
  --figures-dir figures \
  --save-json data/ideal/exp6_n3_ideal.json

python enc_qubit_cloning.py \
  -e 7 --backend ideal --n 2 --n-drops 4 --activate-drop 1 \
  --shots 4096 --plot --no-verify \
  --figures-dir figures \
  --save-json data/ideal/exp7_n2_ideal.json

python enc_qubit_cloning.py \
  -e 8 --backend ideal --n 2 --shots 4096 --plot --no-verify \
  --figures-dir figures \
  --save-json data/ideal/exp8_n2_ideal.json

python enc_qubit_cloning.py \
  -e 8 --backend ideal --n 3 --shots 4096 --plot --no-verify \
  --figures-dir figures \
  --save-json data/ideal/exp8_n3_ideal.json

python enc_qubit_cloning.py \
  -e 8 --backend ideal --n 4 --shots 4096 --plot --no-verify \
  --figures-dir figures \
  --save-json data/ideal/exp8_n4_ideal.json

python enc_qubit_cloning.py \
  -e 9 --plot --no-verify \
  --figures-dir figures \
  --save-json data/ideal/exp9_threat_model.json

# ── Full security suite in one pass ─────────────────────────────────────

python enc_qubit_cloning.py \
  -e security --backend ideal --n 2 --n-drops 4 --activate-drop 1 \
  --shots 4096 --plot --no-verify \
  --figures-dir figures
```

---

### Group 2 — NISQ Simulation (Noise-Realistic)

Depolarizing noise model: 1-qubit error 0.1%, 2-qubit error 1.0%. Approximates current IBM Eagle R3 hardware.

```bash
python enc_qubit_cloning.py \
  -e 1 --backend nisq --sweep --shots 4096 --plot --no-verify \
  --figures-dir figures \
  --save-json data/nisq/exp1_sweep_nisq.json

python enc_qubit_cloning.py \
  -e 5 --backend nisq --n 2 --shots 4096 --plot --no-verify \
  --figures-dir figures \
  --save-json data/nisq/exp5_n2_nisq.json

python enc_qubit_cloning.py \
  -e 5 --backend nisq --n 3 --shots 4096 --plot --no-verify \
  --figures-dir figures \
  --save-json data/nisq/exp5_n3_nisq.json

python enc_qubit_cloning.py \
  -e 6 --backend nisq --n 2 --shots 4096 --plot --no-verify \
  --figures-dir figures \
  --save-json data/nisq/exp6_n2_nisq.json

python enc_qubit_cloning.py \
  -e 6 --backend nisq --n 3 --shots 4096 --plot --no-verify \
  --figures-dir figures \
  --save-json data/nisq/exp6_n3_nisq.json

python enc_qubit_cloning.py \
  -e 7 --backend nisq --n 2 --n-drops 4 --activate-drop 1 \
  --shots 4096 --plot --no-verify \
  --figures-dir figures \
  --save-json data/nisq/exp7_n2_nisq.json

python enc_qubit_cloning.py \
  -e 8 --backend nisq --n 2 --shots 4096 --plot --no-verify \
  --figures-dir figures \
  --save-json data/nisq/exp8_n2_nisq.json

python enc_qubit_cloning.py \
  -e 8 --backend nisq --n 3 --shots 4096 --plot --no-verify \
  --figures-dir figures \
  --save-json data/nisq/exp8_n3_nisq.json
```

---

### Group 3 — Real IBM Hardware

Requires `.env` with valid credentials. Each command produces a JSON in `data/real/` containing IBM `job_id` fields verifiable at `quantum.ibm.com/jobs/<job_id>`.

> **Open Plan budget:** ~24–48 seconds of quantum time for all experiments. Well within the 10-minute monthly limit. Queue wait time is 2–48 hours — **submit these days before your presentation, not on the day.**

```bash
# ── Experiment 1: Control run — verifies the backend is functional ───────
# If Fe_BSM < 0.5 for n=2, the backend is too noisy. Request another.

python enc_qubit_cloning.py \
  -e 1 --backend real --n 2 --shots 8192 --plot --no-verify \
  --figures-dir figures \
  --save-json data/real/exp1_n2_real.json

python enc_qubit_cloning.py \
  -e 1 --backend real --n 3 --shots 8192 --no-verify \
  --save-json data/real/exp1_n3_real.json

python enc_qubit_cloning.py \
  -e 1 --backend real --n 4 --shots 8192 --no-verify \
  --save-json data/real/exp1_n4_real.json

# ── Experiment 5: Quantum Ransomware ────────────────────────────────────
# Critical: Fe_victim must be ≈ 0.25 regardless of backend quality.
# Fe_honest is the control — expected ~0.70–0.82 on Eagle R3.

python enc_qubit_cloning.py \
  -e 5 --backend real --n 2 --shots 8192 --plot --no-verify \
  --figures-dir figures \
  --save-json data/real/exp5_n2_real.json

python enc_qubit_cloning.py \
  -e 5 --backend real --n 3 --shots 4096 --no-verify \
  --save-json data/real/exp5_n3_real.json

# ── Experiment 6: Harvest Now, Decrypt Later ─────────────────────────────

python enc_qubit_cloning.py \
  -e 6 --backend real --n 2 --shots 8192 --plot --no-verify \
  --figures-dir figures \
  --save-json data/real/exp6_n2_real.json

# ── Experiment 7: Quantum Dead Drop ─────────────────────────────────────

python enc_qubit_cloning.py \
  -e 7 --backend real --n 2 --n-drops 4 --activate-drop 1 \
  --shots 8192 --plot --no-verify \
  --figures-dir figures \
  --save-json data/real/exp7_n2_real.json

# ── Experiment 8: Partial Key Attack ────────────────────────────────────
# n=2: k ∈ {0, 1, 2}. Three circuits. Fits in Open Plan budget.

python enc_qubit_cloning.py \
  -e 8 --backend real --n 2 --shots 8192 --plot --no-verify \
  --figures-dir figures \
  --save-json data/real/exp8_n2_real.json
```

---

### Group 4 — Backend Comparison Plots

Run after `data/real/` JSON files are collected. Produces the `compare_*.png` figures used in the talk.

```bash
# Exp 5: ideal vs NISQ vs real — the "money plot"
python enc_qubit_cloning.py \
  --load-json \
    data/ideal/exp5_n2_ideal.json \
    data/nisq/exp5_n2_nisq.json \
    data/real/exp5_n2_real.json \
  --plot --no-verify \
  --figures-dir figures

# Exp 6: ideal vs real
python enc_qubit_cloning.py \
  --load-json \
    data/ideal/exp6_n2_ideal.json \
    data/real/exp6_n2_real.json \
  --plot --no-verify \
  --figures-dir figures

# Exp 8: ideal vs NISQ vs real
python enc_qubit_cloning.py \
  --load-json \
    data/ideal/exp8_n2_ideal.json \
    data/nisq/exp8_n2_nisq.json \
    data/real/exp8_n2_real.json \
  --plot --no-verify \
  --figures-dir figures

# Exp 1: Fe vs n comparison across backends
python enc_qubit_cloning.py \
  --load-json \
    data/ideal/exp1_sweep_ideal.json \
    data/real/exp1_n2_real.json \
  --plot --no-verify \
  --figures-dir figures
```

---

### Group 5 — Live Demo Commands

These are the exact commands used on stage at CryptoRave 2026. No IBM connection required during the talk.

```bash
# 1. Protocol self-check (~30 s)
python enc_qubit_cloning.py --verify

# 2. Ransomware attack — the central demonstration (~20 s)
python enc_qubit_cloning.py \
  -e 5 --n 2 --backend ideal --no-verify

# 3. All-or-nothing key threshold (~20 s)
python enc_qubit_cloning.py \
  -e 8 --n 4 --backend ideal --no-verify

# 4. Pre-collected hardware result — no IBM needed (~5 s)
python enc_qubit_cloning.py \
  --load-json data/real/exp5_n2_real.json \
  --plot --no-verify \
  --figures-dir figures

# 5. Comparison: ideal vs hardware side-by-side (~5 s)
python enc_qubit_cloning.py \
  --load-json \
    data/ideal/exp5_n2_ideal.json \
    data/real/exp5_n2_real.json \
  --plot --no-verify \
  --figures-dir figures
```

---

## Experiment Descriptions

### Experiments 1–4 (Physics — Yamaguchi et al. 2026)

These reproduce the four hardware experiments from the published paper.

| Exp | Measures | Key result |
|-----|---------|------------|
| **1** | Entanglement fidelity `Fe` vs clone count `n` | Fe degrades with circuit depth, **not** with `n` → protocol does not dilute quantum information |
| **2** | CHSH parameter `S` under three measurement orderings | `S > 2` (CHSH violation) for `n = 2, 3` on real hardware → recovered state is genuinely quantum |
| **3** | Iterated cloning: `Fe` after `l` rounds | 27 clones with `Fe > 0.5` (entanglement witnessed); 77 clones above noise floor |
| **4** | GHZ state fidelity `Fr` with parallel cloning | Multipartite entanglement preserved through enc + dec for `r` up to 4 |

### Experiments 5–9 (Security — This Work)

| Exp | Scenario | What is measured | Expected result |
|-----|---------|-----------------|-----------------|
| **5** | Quantum Ransomware | `Fe_honest`, `Fe_victim`, `Fe_adversary` | `Fe_victim ≈ 0.25` on any backend — indistinguishable from decoherence |
| **6** | Harvest Now, Decrypt Later | `Fe_no_key`, `Fe_with_key` | Phase 1: `Fe ≈ 0.25`; Phase 2: `Fe ≈ Fe_honest` |
| **7** | Quantum Dead Drop | `Fe_activated`, `Fe_inactive` | All inactive drops: `Fe ≈ 0.25`; activated: `Fe ≈ Fe_honest` |
| **8** | Partial Key Attack | `Fe(k)` for `k = 0, ..., n` | Step function: `Fe = 0.25` for all `k < n`; `Fe = 1.00` at `k = n` |
| **9** | Classical Channel Reduction | Threat model (no circuits) | Formal reduction: total security = security of `{N_i}` delivery channel |

---

## Security Attack Scenarios

### Scenario 5 — Quantum Ransomware

A malicious quantum cloud provider applies `U_enc` silently to the client's qubit before returning it, retaining `{N_i}`. The returned clone has `ρ_{S_i} = I/2` — **indistinguishable from hardware decoherence** without an out-of-band control circuit.

**Detection:** Requires a same-session control run with known input. Without it, `Fe ≈ 0.25` is consistent with both attack and natural noise.

**Mitigation:** Apply `U_enc` locally before any qubit leaves the client's hardware. The provider receives `ρ = I/2` and cannot usefully re-encrypt. Analogue: Intel TDX / AMD SEV for classical cloud data.

---

### Scenario 6 — Harvest Now, Decrypt Later (Quantum Variant)

Unlike classical HNDL (which requires Shor's algorithm), the quantum variant requires only:
- Quantum memory with coherence ≥ gap between capture `T₁` and key intercept `T₂`
- Read access to the classical `{N_i}` delivery channel

**Current state:** NV-center diamond memories achieve ~1 hour coherence at ambient temperature (2025). No algorithmic advance is required.

**Mitigation:** TLS 1.3 with ECDHE + ML-KEM-768 (NIST FIPS 203). Forward secrecy closes the retroactive key-intercept window.

---

### Scenario 7 — Quantum Dead Drop

Deposited clones `S_i` satisfy `ρ_{S_i} = I/2`. By the Holevo bound, zero bits about `|ψ⟩` are extractable by any POVM, making the drop physically indistinguishable from an uninitialized qubit. Classical steganography can be detected by entropy analysis; quantum dead drops cannot.

---

### Scenario 8 — All-or-Nothing Key Threshold

For any `k < n` noise qubits, the reduced state `ρ_{S_j, N_1,...,N_k}` is independent of `|ψ⟩` — quantum channel capacity is exactly zero. The threshold is discontinuous: `k = n − 1` gives the same zero information as `k = 0`. This is stronger than any classical key-hardening scheme, where each additional bit strictly increases an adversary's information.

---

### Scenario 9 — Classical Channel Reduction

The security of the total system reduces to the security of the classical channel delivering `{N_i}`:

```
Adv^{EC}[A] ≤ Adv^{key_channel}[A']
```

The quantum channel `{S_i}` is unconditionally secure (Holevo bound — no assumptions). The classical key channel is the exclusive attack surface. Protecting it with ML-KEM-768 is sufficient for post-quantum security.

**Mitigations by adversary class:**

| Adversary | Capability | Mitigation |
|-----------|-----------|------------|
| Classical | Eavesdrop | AES-256 on key channel |
| Quantum (Shor) | Break RSA | ML-KEM-768 (NIST FIPS 203) |
| Quantum memory + classical | HNDL | ML-KEM-768 + ECDHE ephemeral |
| Malicious cloud | Ransomware | Local `U_enc` enforcement |

---

## Provenance & Reproducibility

Every result in this repository is one of three types, clearly labelled in all JSON files and figures:

| Label | Source | Verifiable by |
|-------|--------|---------------|
| `[SIM]` | `AerSimulator` ideal, deterministic seed | Re-running the command |
| `[NISQ]` | `AerSimulator` with depolarizing noise model | Re-running the command |
| `[HW]` | Real IBM quantum processor | IBM `job_id` at `quantum.ibm.com/jobs/<id>` |

Each `data/real/*.json` file contains a `jobs` array. Each entry includes:

```json
{
  "job_id": "cXXXXXXXXXXXXXXXXXXXX",
  "circuit_name": "Ransomware_victim_n2",
  "shots": 8192,
  "backend": "ibm_brisbane",
  "counts": { "00": 2087, "01": 1996, "10": 2044, "11": 2065 }
}
```

Any person with an IBM Quantum account can independently verify the raw counts.

**To reproduce from scratch:**

```bash
git clone https://github.com/jullyanolino/encrypted_qubit_cloning.git
cd encrypted_qubit_cloning
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python enc_qubit_cloning.py --verify
python enc_qubit_cloning.py -e 5 --backend ideal --n 2 --no-verify
```

All ideal and NISQ results should match exactly (seeded). Hardware results will vary by backend calibration date.
---

## Drawing circuits

``` bash
# Standard (slides) — colour-coded, 150 dpi, goes to figures\
python enc_qubit_cloning.py --draw-circuits --n 2 --figures-dir figures

# Print / LaTeX — black-and-white, 300 dpi
python enc_qubit_cloning.py --draw-circuits --n 2 --draw-style bw --draw-dpi 300 --figures-dir figures

# With decomposed primitives — adds *_decomposed.png for each circuit
# Use for the Methods section or circuit-depth analysis slides
python enc_qubit_cloning.py --draw-circuits --n 2 --draw-decompose --figures-dir figures

# n=3 version for the slide comparing circuit depth with n=2
python enc_qubit_cloning.py --draw-circuits --n 3 --figures-dir figures
```

---

## Repository Structure

```
encrypted_qubit_cloning/
├── enc_qubit_cloning.py   Main CLI (~3060 lines, 9 experiments)
├── requirements.txt                Pinned Python dependencies
├── .env.example                    Credential template (never commit .env)
├── .gitignore
├── LICENSE                         MIT
│
├── circuits/                       Circuit definitions — import into any Qiskit project
│   ├── circuits_n{2,3,4}.qpy      QPY bundles (lossless, recommended)
│   ├── enc_dec_n{2,3}.qasm        Full protocol QASM2
│   ├── enc_only_n{2,3}.qasm       Encryption unitary alone
│   ├── dec_only_n{2,3}.qasm       Decryption unitary alone
│   └── ransomware_victim_n2.qasm  Attack circuit (enc, no dec)
│
├── data/
│   ├── ideal/                      Simulator baselines (seeded, deterministic)
│   ├── nisq/                       Noisy simulator results
│   └── real/                       IBM hardware results with job IDs ← audit trail
│
└── figures/                        PNG figures (150–300 dpi)
    ├── exp5_ransomware_n{2,3,4}.png
    ├── exp6_harvest_n{2,3}.png
    ├── exp7_dead_drop_n2.png
    ├── exp8_partial_key_n{2,3,4}.png
    ├── exp9_threat_model.png
    └── compare_exp{5,6,8}_backends.png
```

---

## Results Summary

### Core Protocol (Exp 1) — IBM Heron R2, Published

| n | Fe BSM | Fe POM | Entanglement witnessed |
|---|--------|--------|----------------------|
| 2 | 0.823 ± 0.004 | 0.875 ± 0.008 | ✓ |
| 3 | 0.839 ± 0.004 | 0.810 ± 0.008 | ✓ |
| 7 | 0.548 ± 0.005 | 0.551 ± 0.009 | ✓ (last) |
| 13 | 0.289 ± 0.005 | 0.295 ± 0.009 | · (above floor) |

### Security Experiments — Ideal Simulation

| Exp | Scenario | Measured Fe | Theory |
|-----|---------|------------|--------|
| 5 | Honest (enc+dec) | 1.0000 ± 0.0000 | 1.000 |
| 5 | Victim (no key) | 0.2539 ± 0.0068 | 0.250 |
| 6 | Phase 1 (no key) | 0.252 ± 0.007 | 0.250 |
| 6 | Phase 2 (key seized) | 1.000 ± 0.000 | 1.000 |
| 8 | k=0,1,2,3 of n=4 | 0.249 ± 0.007 | 0.250 |
| 8 | k=4 of n=4 | 1.000 ± 0.000 | 1.000 |

### Key Physical Property (All Backends)

**`Fe_victim ≈ 0.25` is hardware-independent.** It is governed by `ρ_{S_i} = I/2` (a protocol property), not by gate error rates. This is the central claim of the security analysis, and it holds on ideal simulators, NISQ simulators, and real IBM processors alike.

---

## References

```bibtex
@article{yamaguchi2026encrypted,
  title   = {Encrypted Qubits can be Cloned},
  author  = {Yamaguchi, Koji and Kempf, Achim},
  journal = {Physical Review Letters},
  volume  = {136},
  pages   = {010801},
  year    = {2026},
  doi     = {10.1103/PhysRevLett.136.010801},
  eprint  = {2501.02757}
}

@misc{yamaguchi2026experimental,
  title         = {Experimental demonstration that qubits can be cloned at will,
                   if encrypted with a single-use decryption key},
  author        = {Yamaguchi, Koji and Rullk{\"o}tter, Leon and Shehzad, Ibrahim
                   and Wagner, Sean J. and Tutschku, Christian and Kempf, Achim},
  year          = {2026},
  eprint        = {2602.10695},
  archivePrefix = {arXiv}
}
```

**NIST PQC:**
- FIPS 203 — ML-KEM (CRYSTALS-Kyber). August 2024. [csrc.nist.gov/pubs/fips/203/final](https://csrc.nist.gov/pubs/fips/203/final)

**Implementation:**
- IBM Qiskit. [github.com/Qiskit/qiskit](https://github.com/Qiskit/qiskit)
- Open Quantum Safe / liboqs. [github.com/open-quantum-safe/liboqs](https://github.com/open-quantum-safe/liboqs)

---

## About the Author

**Jullyano Lino** — Computer Science (UFPI), Quantum Communication post-graduate (SENAI/CIMATEC), Mathematics (Uninter).

Author of papers on quantum sensing (RADAR/LIDAR) for national defence (ITA 2023, IEEE Spectrum Magazine 2025). Quantum cybersecurity speaker at MindTheSec 2023, IBM Qiskit Fall Fest 2024 and 2025, HNWD 2026. Official translator of IBM Qiskit documentation. Quantum challenge participant (IBM, QWorld, Venturus, C.E.S.A.R.).

**Talk:** [You Can't Clone a Qubit — Unless You Encrypt it First!](https://cpa.cryptorave.org/cryptorave-2026/talk/DYKJPZ/)
CryptoRave 2026 · May 9, 2026 · Tula Pilar room

**Talk:** [You Can't Clone a Qubit — Unless You Encrypt it First!](https://securitybsides.com.br/2026/quantum-village-br/)
BSides SP 2026 · May 17, 2026 · Quantum Village · i02C room


---

<div align="center">

*"Cryptography surprisingly makes cloning possible — and the resulting security is information-theoretic, not computational."*

[![CryptoRave 2026](https://img.shields.io/badge/CryptoRave%202026-Talk%20DYKJPZ-02470d?style=flat-square)](https://cpa.cryptorave.org/cryptorave-2026/talk/DYKJPZ/)
[![IBM Quantum](https://img.shields.io/badge/Verified%20on-IBM%20Quantum-1e49be?style=flat-square&logo=ibm)](https://quantum.ibm.com)
[![MIT License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

</div>
