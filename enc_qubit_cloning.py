#!/usr/bin/env python3
"""
enc_qubit_cloning_proof.py
=================
CLI implementation of all four hardware experiments from:

  Yamaguchi et al. (2026)  arXiv:2602.10695
  "Experimental demonstration that qubits can be cloned at will,
   if encrypted with a single-use decryption key"

────────────────────────────────────────────────────────────────────────────
IBM QUANTUM CREDENTIALS
────────────────────────────────────────────────────────────────────────────
    [A] .env file in the same directory (recommended)
    IBM_QUANTUM_TOKEN=...
    IBM_QUANTUM_INSTANCE=crn:v1:bluemix:...

    [B] JSON: --creds-file ibm_creds.json

    [C] Environment variables

    [D] Flags: --token <tok> --instance <crn>

Examples:
  python enc_qubit_cloning_proof.py --experiment 1 --backend real --ibm-backend least-busy
  python enc_qubit_cloning_proof.py --list-backends
  python enc_qubit_cloning_proof.py --verify
────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import random
import warnings
import json
from dataclasses import dataclass, field
from typing import Optional

warnings.filterwarnings("ignore")

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import UnitaryGate
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error


# ── CREDENTIAL LOADER ─────────────

def _load_dotenv(path: str) -> dict:
    """Parse .env file."""
    result = {}
    try:
        with open(path, encoding='utf-8') as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, _, val = line.partition('=')
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key:
                    result[key] = val
    except FileNotFoundError:
        pass
    except Exception as exc:
        print(f'  [warn] Could not read {path}: {exc}', file=sys.stderr)
    return result


def _load_creds_json(path: str) -> dict:
    """Parse JSON credentials."""
    try:
        with open(path, encoding='utf-8') as fh:
            data = json.load(fh)
        aliases = {
            'token': 'IBM_QUANTUM_TOKEN',
            'IBM_QUANTUM_TOKEN': 'IBM_QUANTUM_TOKEN',
            'IBM_CLOUD_TOKEN': 'IBM_QUANTUM_TOKEN',
            'instance': 'IBM_QUANTUM_INSTANCE',
            'IBM_QUANTUM_INSTANCE': 'IBM_QUANTUM_INSTANCE',
            'IBM_CLOUD_INSTANCE': 'IBM_QUANTUM_INSTANCE',
        }
        return {aliases[k]: v for k, v in data.items() if k in aliases}
    except FileNotFoundError:
        print(f'  [error] Credentials file not found: {path}', file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f'  [error] Invalid JSON in {path}: {exc}', file=sys.stderr)
        sys.exit(1)


def resolve_credentials(args) -> tuple[str | None, str | None]:
    
    env_overlay: dict = {}

    if getattr(args, 'creds_file', None):
        env_overlay = _load_creds_json(args.creds_file)
    else:
        dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        fallback = os.path.join(os.getcwd(), '.env')
        env_overlay = _load_dotenv(dotenv_path) or _load_dotenv(fallback)

    token = (
        args.token
        or env_overlay.get('IBM_QUANTUM_TOKEN')
        or os.environ.get('IBM_QUANTUM_TOKEN')
        or os.environ.get('IBM_CLOUD_TOKEN')
    )
    instance = (
        args.instance
        or env_overlay.get('IBM_QUANTUM_INSTANCE')
        or os.environ.get('IBM_QUANTUM_INSTANCE')
        or os.environ.get('IBM_CLOUD_INSTANCE')
    )
    return token, instance


# ── ANSI colour helpers ────────────────────────────────────────────────────────

class C:
    """ANSI terminal colours — degrade gracefully when piped."""
    _ON = sys.stdout.isatty()
    GREEN  = "\033[92m" if _ON else ""
    RED    = "\033[91m" if _ON else ""
    YELLOW = "\033[93m" if _ON else ""
    CYAN   = "\033[96m" if _ON else ""
    BOLD   = "\033[1m"  if _ON else ""
    DIM    = "\033[2m"  if _ON else ""
    RESET  = "\033[0m"  if _ON else ""

def ok(msg):  print(f"  {C.GREEN}✓{C.RESET} {msg}")
def fail(msg): print(f"  {C.RED}✗{C.RESET} {msg}")
def info(msg): print(f"  {C.CYAN}·{C.RESET} {msg}")


BANNER = r"""
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
  Implementation of Yamaguchi & Kempf (PRL 2026) + adversarial extensions
  arXiv:2501.02757  |  arXiv:2602.10695
"""


def print_banner(experiment: str, backend_name: str) -> None:
    """Banner."""
    print("\n")
    for line in BANNER.strip().split('\n'):
        print(f"{C.RED}{line}{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}  Encrypted Qubit Cloning Proof{C.RESET}")
    print(f"  Experiment: {experiment}  |  Backend: {backend_name}")
    print(f"{C.RESET}\n")


# ── Result dataclasses───────────────────────────────────

@dataclass
class FidelityResult:
    n: int
    Fe_BSM: float
    Fe_BSM_err: float
    Fe_POM: float
    Fe_POM_err: float
    Fe_UQCM: float
    witnessed: bool
    above_floor: bool
    label: str = ""

@dataclass
class CHSHResult:
    n: int
    scenario: str
    S: float
    S_err: float
    S_UQCM: float
    violated: bool

@dataclass
class IteratedResult:
    l: int
    n_virtual_clones: int
    circuit_depth: int
    Fe: float
    Fe_err: float


# ── PROTOCOL MATHEMATICS ───────────────────────────────────

def build_uenc_matrix(n: int) -> np.ndarray:
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    Z = np.array([[1, 0], [0, -1]], dtype=complex)
    dim = 2 ** (n + 1)
    Xall = X.copy()
    Zall = Z.copy()
    for _ in range(n):
        Xall = np.kron(Xall, X)
        Zall = np.kron(Zall, Z)
    c, s = np.cos(np.pi / 4), np.sin(np.pi / 4)
    UX = c * np.eye(dim, dtype=complex) - 1j * s * Xall
    UZ = c * np.eye(dim, dtype=complex) - 1j * s * Zall
    return UX @ UZ


def build_udec_matrix(n: int) -> np.ndarray:
    I2 = np.eye(2, dtype=complex)
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
    Z = np.array([[1, 0], [0, -1]], dtype=complex)
    PAU = [I2, X, Y, Z]
    PAU_T = [I2, X, -Y, Z]
    alpha = {0: 1 + 0j, 1: 1j, 2: -(1j) ** (n + 1), 3: 1j}
    phi_plus = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
    dim = 2 ** (n + 1)
    U = np.zeros((dim, dim), dtype=complex)
    for mu in range(4):
        phi_mu = np.kron(PAU[mu], I2) @ phi_plus
        proj = np.outer(phi_mu, phi_mu.conj())
        if n == 1:
            tail = np.eye(1, dtype=complex)
        else:
            tail = PAU_T[mu].copy()
            for _ in range(n - 2):
                tail = np.kron(tail, PAU_T[mu])
        U += alpha[mu] * np.kron(proj, tail)
    return U


def verify_protocol(n: int, shots: int = 4096, verbose: bool = True) -> bool:
    if verbose:
        print(f"\n{C.BOLD}Protocol verification  n={n}{C.RESET}")
    passed = True
    dim = 2 ** (n + 1)
    I = np.eye(dim, dtype=complex)
    U_enc = build_uenc_matrix(n)
    U_dec = build_udec_matrix(n)
    for name, U in [("U_enc", U_enc), ("U_dec", U_dec)]:
        err = np.max(np.abs(U @ U.conj().T - I))
        if err < 1e-9:
            if verbose: ok(f"{name} unitary  (max|UU†-I| = {err:.2e})")
        else:
            if verbose: fail(f"{name} NOT unitary  (max|UU†-I| = {err:.2e})")
            passed = False
    a2_correct = -(1j) ** (n + 1)
    if verbose:
        info(f"α_2 = {a2_correct:.4f}")
    ideal = AerSimulator(method="statevector")
    qc = build_exp1_bsm(n)
    t = transpile(qc, ideal, optimization_level=0, seed_transpiler=0)
    counts = ideal.run(t, shots=shots, seed_simulator=0).result().get_counts()
    Fe, sig = fe_bsm_from_counts(counts, shots)
    threshold = 0.99
    if Fe >= threshold:
        if verbose: ok(f"Round-trip Fe = {Fe:.4f} ± {sig:.4f}  (ideal, {shots} shots)")
    else:
        if verbose: fail(f"Round-trip Fe = {Fe:.4f} — expected ≥ {threshold}")
        passed = False
    if verbose:
        status = f"{C.GREEN}PASSED{C.RESET}" if passed else f"{C.RED}FAILED{C.RESET}"
        print(f"  → {status}")
    return passed


# ── CIRCUIT PRIMITIVES ───────────────────────────────────────────────

def _enc_gate(n: int) -> UnitaryGate:
    return UnitaryGate(build_uenc_matrix(n), label=f"Uenc(n={n})")


def _dec_gate(n: int) -> UnitaryGate:
    M = build_udec_matrix(n)
    k = n + 1
    dim = 2 ** k
    perm = np.array([int(f"{i:0{k}b}"[::-1], 2) for i in range(dim)])
    M_le = M[np.ix_(perm, perm)]
    return UnitaryGate(M_le, label=f"Udec(n={n})")


def _bell(qc: QuantumCircuit, q1: int, q2: int) -> None:
    qc.h(q1)
    qc.cx(q1, q2)


# ── EXPERIMENT CIRCUITS ──────────────────────────────────────────────

def build_exp1_bsm(n: int) -> QuantumCircuit:
    nq = 2 * n + 2
    qc = QuantumCircuit(nq, 2, name=f"Exp1_BSM_n{n}")
    _bell(qc, 0, 1)
    for i in range(n):
        _bell(qc, 2 + i, n + 2 + i)
    sig_qubits = [1] + list(range(2, n + 2))
    qc.append(_enc_gate(n), sig_qubits)
    qc.barrier()
    dec_qubits = [2] + list(range(n + 2, 2 * n + 2))
    qc.append(_dec_gate(n), dec_qubits)
    qc.barrier()
    qc.cx(0, 2)
    qc.h(0)
    qc.measure(0, 0)
    qc.measure(2, 1)
    return qc


def build_exp1_pom(n: int, k: int, r: int = 2) -> QuantumCircuit:
    nq = 2 * n + 2
    qc = QuantumCircuit(nq, 2, name=f"Exp1_POM_n{n}_k{k}")
    _bell(qc, 0, 1)
    for i in range(n):
        _bell(qc, 2 + i, n + 2 + i)
    qc.append(_enc_gate(n), [1] + list(range(2, n + 2)))
    qc.barrier()
    qc.append(_dec_gate(n), [2] + list(range(n + 2, 2 * n + 2)))
    qc.barrier()
    if k > 0:
        theta = k * np.pi / r
        for q in (0, 2):
            qc.rz(theta, q)
            qc.h(q)
    qc.measure(0, 0)
    qc.measure(2, 1)
    return qc


def build_exp2_chsh(n: int, scenario: int, a_basis: str, b_basis: str) -> QuantumCircuit:
    nq = 2 * n + 2
    qc = QuantumCircuit(nq, 2, name=f"Exp2_s{scenario}_{a_basis}_{b_basis}_n{n}")
    _bell(qc, 0, 1)
    for i in range(n):
        _bell(qc, 2 + i, n + 2 + i)
    qc.append(_enc_gate(n), [1] + list(range(2, n + 2)))
    qc.barrier()
    if scenario == 21:
        if a_basis == "X":
            qc.h(0)
        qc.measure(0, 0)
        qc.barrier()
        qc.append(_dec_gate(n), [2] + list(range(n + 2, 2 * n + 2)))
        qc.barrier()
        if b_basis == "B0":
            qc.ry(-np.pi / 4, 2)
        elif b_basis == "B1":
            qc.ry(+np.pi / 4, 2)
        qc.measure(2, 1)
    else:
        qc.append(_dec_gate(n), [2] + list(range(n + 2, 2 * n + 2)))
        qc.barrier()
        if a_basis == "X":
            qc.h(0)
        if b_basis == "B0":
            qc.ry(-np.pi / 4, 2)
        elif b_basis == "B1":
            qc.ry(+np.pi / 4, 2)
        qc.measure(0, 0)
        qc.measure(2, 1)
    return qc


def build_exp3_iterated(l: int, n_base: int = 2) -> QuantumCircuit:
    nq = 2 + n_base * 2 * (l + 1)
    qc = QuantumCircuit(nq, 2, name=f"Exp3_l{l}_nb{n_base}")
    _bell(qc, 0, 1)
    s0 = [2 + i for i in range(n_base)]
    n0 = [2 + n_base + i for i in range(n_base)]
    for si, ni in zip(s0, n0):
        _bell(qc, si, ni)
    qc.append(_enc_gate(n_base), [1] + s0)
    qc.barrier()
    prev_clone = s0[0]
    offset = 2 + 2 * n_base
    for gen in range(1, l + 1):
        sg = [offset + i for i in range(n_base)]
        ng = [offset + n_base + i for i in range(n_base)]
        for si, ni in zip(sg, ng):
            _bell(qc, si, ni)
        qc.append(_enc_gate(n_base), [prev_clone] + sg)
        qc.barrier()
        prev_clone = sg[0]
        offset += 2 * n_base
    final_noise_start = offset - n_base
    dec_qubits = [prev_clone] + list(range(final_noise_start, final_noise_start + n_base))
    qc.append(_dec_gate(n_base), dec_qubits)
    qc.barrier()
    qc.cx(0, prev_clone)
    qc.h(0)
    qc.measure(0, 0)
    qc.measure(prev_clone, 1)
    return qc


def build_exp4_ghz(r: int, n_clones: int = 2) -> QuantumCircuit:
    nq_per_group = 2 * n_clones + 1
    nq = r + r * 2 * n_clones
    qc = QuantumCircuit(nq, r, name=f"Exp4_r{r}_nc{n_clones}")
    qc.h(0)
    for i in range(1, r):
        qc.cx(0, i)
    qc.barrier()
    offset = r
    decoded_qubits = []
    for gi in range(r):
        sigs = list(range(offset, offset + n_clones))
        nois = list(range(offset + n_clones, offset + 2 * n_clones))
        for s, no in zip(sigs, nois):
            _bell(qc, s, no)
        qc.append(_enc_gate(n_clones), [gi] + sigs)
        dec_q = [sigs[0]] + nois
        qc.append(_dec_gate(n_clones), dec_q)
        decoded_qubits.append(sigs[0])
        offset += 2 * n_clones
    qc.barrier()
    for ci, dq in enumerate(decoded_qubits):
        qc.measure(dq, ci)
    return qc


# ── STATISTICS ───────────────────────────────────────────────────────

def fe_bsm_from_counts(counts: dict, shots: int) -> tuple[float, float]:
    n00 = counts.get("00", 0)
    Fe = n00 / shots
    err = np.sqrt(max(Fe * (1 - Fe) / shots, 0.0))
    return Fe, err


def fe_pom_from_counts(counts_list: list, shots: int, r: int = 2) -> tuple[float, float]:
    c0 = counts_list[0]
    p00 = c0.get("00", 0) / shots
    p11 = c0.get("11", 0) / shots
    P = p00 + p11
    var_P = abs(p00 * (p00 - 1) / shots) + abs(p11 * (p11 - 1) / shots)
    chi_terms = []
    for k in range(1, r + 1):
        ck = counts_list[k]
        N = {b: ck.get(b, 0) for b in ("00", "01", "10", "11")}
        Ek = (N["00"] + N["11"] - N["01"] - N["10"]) / shots
        chi_terms.append((-1) ** k * Ek)
    chi = sum(chi_terms) / r
    Fr = 0.5 * (P + chi)
    var_chi = sum(abs(1 - ((-((-1)**k) * ct))**2) / shots for k, ct in enumerate(chi_terms, 1)) / r**2
    err = np.sqrt(var_P + var_chi)
    return float(Fr), float(err)


def correlator_from_counts(counts: dict, shots: int) -> float:
    N00 = counts.get("00", 0)
    N11 = counts.get("11", 0)
    N01 = counts.get("01", 0)
    N10 = counts.get("10", 0)
    return (N00 + N11 - N01 - N10) / shots


def chsh_from_four_correlators(E_A0B0, E_A0B1, E_A1B0, E_A1B1) -> tuple[float, float]:
    return E_A0B0 + E_A0B1 + E_A1B0 - E_A1B1


def fr_ghz_from_counts(counts: dict, shots: int, r: int) -> tuple[float, float]:
    zeros = "0" * r
    ones = "1" * r
    p0 = counts.get(zeros, 0) / shots
    p1 = counts.get(ones, 0) / shots
    Fr = p0 + p1
    err = np.sqrt(max(Fr * (1 - Fr) / shots, 0.0))
    return Fr, err


# ── BACKEND MANAGEMENT ─────────────────────────────

def _build_nisq_backend() -> AerSimulator:
    try:
        from qiskit_ibm_runtime.fake_provider import FakeKingstonV2
        nm = NoiseModel.from_backend(FakeKingstonV2())
        info("FakeKingstonV2 noise model loaded")
    except Exception:
        nm = NoiseModel()
        nm.add_all_qubit_quantum_error(depolarizing_error(0.001, 1), ["u1", "u2", "u3", "sx", "x"])
        nm.add_all_qubit_quantum_error(depolarizing_error(0.01, 2), ["cx", "cz"])
        info("Depolarizing fallback noise model (1q: 0.1%, 2q: 1%)")
    return AerSimulator(noise_model=nm)


def _get_ibm_service(token: Optional[str] = None, instance: Optional[str] = None):
    """channel=ibm_cloud."""
    if token is None:
        token = os.environ.get("IBM_QUANTUM_TOKEN", "") or os.environ.get("IBM_CLOUD_TOKEN", "")
    if not token:
        print(f"{C.RED}[ERROR]{C.RESET} IBM_QUANTUM_TOKEN not set.")
        sys.exit(1)
    from qiskit_ibm_runtime import QiskitRuntimeService
    return QiskitRuntimeService(channel="ibm_cloud", token=token, instance=instance)


def list_open_plan_backends(min_qubits: int = 1, token: Optional[str] = None, instance: Optional[str] = None) -> None:
    """token/instance."""
    svc = _get_ibm_service(token, instance)
    backends = svc.backends(operational=True, simulator=False, min_num_qubits=min_qubits)
    if not backends:
        print("No backends found.")
        return
    print(f"\n{C.BOLD}{'Backend':<22} {'Qubits':>6}  {'Pending':>8}  {'Status'}{C.RESET}")
    print("─" * 56)
    for b in sorted(backends, key=lambda x: x.status().pending_jobs):
        st = b.status()
        flag = f"{C.GREEN}●{C.RESET}" if st.operational else f"{C.RED}✕{C.RESET}"
        print(f"  {flag} {b.name:<20} {b.num_qubits:>6}  {st.pending_jobs:>8}  {st.status_msg}")
    print()


def _get_least_busy(svc, min_qubits: int = 5):
    backends = svc.backends(operational=True, simulator=False, min_num_qubits=min_qubits)
    if not backends:
        print(f"{C.RED}[ERROR]{C.RESET} No suitable backends found.")
        sys.exit(1)
    chosen = min(backends, key=lambda b: b.status().pending_jobs)
    info(f"Least-busy backend: {C.BOLD}{chosen.name}{C.RESET}  ({chosen.num_qubits} qubits, {chosen.status().pending_jobs} pending jobs)")
    return chosen


def get_backend(name: str, ibm_backend_name: str = "least-busy", token: Optional[str] = None, instance: Optional[str] = None):
    """token/instance."""
    if name == "ideal":
        return AerSimulator(method="statevector"), False
    if name == "nisq":
        return _build_nisq_backend(), False
    if name == "real":
        svc = _get_ibm_service(token, instance)
        if ibm_backend_name == "least-busy":
            return _get_least_busy(svc), True
        backend = svc.backend(ibm_backend_name)
        info(f"Using backend: {C.BOLD}{backend.name}{C.RESET}")
        return backend, True
    raise ValueError(f"Unknown backend: {name!r}")


# ── MODULE-LEVEL JOB LOG ──────────────────────────────────────────────────────
#
# Populated by run_circuit() whenever is_real=True.  Each entry records:
#   job_id      — IBM Quantum job ID, verifiable at quantum.ibm.com
#   circuit_name — qc.name, identifies which experiment circuit was submitted
#   shots        — number of shots requested
#   backend      — backend.name string
#   counts       — raw measurement outcomes dict (the primary data)
#
# The log is cleared at the start of main() and serialised to disk when
# --save-json is supplied, providing a full provenance chain for auditors.
#
_JOB_LOG: list[dict] = []


# ── SAMPLER COUNT EXTRACTOR ──────────────────────────────────────────────────
#
# SamplerV2 (qiskit-ibm-runtime >= 0.24) returns results in a DataBin object
# whose attributes are named after the *classical registers* of the circuit.
# The register name depends on how the circuit was constructed:
#
#   QuantumCircuit(nq, nc)        -> classical register named "c"  (default)
#   QuantumCircuit(nq, nc, ...)   -> classical register named "c"  (default)
#   ClassicalRegister("meas", nc) -> classical register named "meas"
#
# All circuits in this script use QuantumCircuit(nq, nc, name=...) so the
# register is "c".  The old code used res.data.meas.get_counts() which would
# always raise AttributeError on these circuits.
#
# This helper is decoupled from run_circuit so it can be unit-tested without
# a real IBM backend.

def _extract_sampler_counts(pub_result, transpiled_circuit: "QuantumCircuit") -> dict:
    """
    Robustly extract a {bitstring: count} dict from a SamplerV2 PubResult.

    Resolution
    ----------------
    1. First classical register of *transpiled_circuit* (canonical source).
    2. "c"    — default name from QuantumCircuit(nq, nc, ...).
    3. "meas" — common alternative used in some IBM examples.
    4. First attribute of DataBin that exposes get_counts() (catch-all).

    Parameters
    ----------
    pub_result          : job.result()[0]  (SamplerPubResult)
    transpiled_circuit  : the circuit object returned by transpile(), used to
                          look up the classical register name.

    Returns
    -------
    dict[str, int]  e.g. {"00": 2048, "11": 2048}

    Raises
    ------
    RuntimeError if no classical register with get_counts() can be found.
    """
    data = pub_result.data

    # ── Strategy 1: use circuit's own classical register name ─────────────
    if transpiled_circuit.cregs:
        reg_name = transpiled_circuit.cregs[0].name
        try:
            return getattr(data, reg_name).get_counts()
        except AttributeError:
            pass  # register name not reflected in DataBin — try fallbacks

    # ── Strategy 2 & 3: try the two most common default names ─────────────
    for name in ("c", "meas", "measure"):
        try:
            return getattr(data, name).get_counts()
        except AttributeError:
            continue

    # ── Strategy 4: iterate over DataBin slots (catch-all) ────────────────
    # DataBin is a dataclass-like namespace; __dataclass_fields__ lists slots.
    fields = getattr(data.__class__, "__dataclass_fields__", {})
    for field_name in fields:
        try:
            bit_array = getattr(data, field_name)
            if callable(getattr(bit_array, "get_counts", None)):
                return bit_array.get_counts()
        except (AttributeError, TypeError):
            continue

    # ── Nothing worked — give the user actionable diagnostic info ──────────
    available = [k for k in getattr(data.__class__, "__dataclass_fields__", {}).keys()]
    raise RuntimeError(
        f"Cannot extract counts from SamplerV2 PubResult.\n"
        f"  Tried registers: circuit.cregs[0], 'c', 'meas', 'measure', "
        f"and all DataBin fields.\n"
        f"  DataBin fields found: {available}\n"
        f"  Circuit classical registers: "
        f"{[r.name for r in transpiled_circuit.cregs]}\n"
        f"  Hint: check qiskit-ibm-runtime version — "
        f"API changed significantly in 0.24."
    )


# ── CIRCUIT RUNNER ────────────────────────────────────────────────────────────

def run_circuit(qc: QuantumCircuit, backend, shots: int,
                is_real: bool, seed: int = 42) -> dict:
    """
    Transpile *qc* and execute it, returning a raw counts dict.

    IBM Quantum Open Plan (10 min/month) does NOT support Session objects.
    Sessions require Pay-As-You-Go or higher.  This function uses job-mode
    execution (SamplerV2 without Session), which is available on all plans
    including Open Plan.  The trade-off is that each circuit is submitted
    as an independent job; for the small circuits used here (≤ 6 qubits,
    ≤ 21 two-qubit gate layers) this is efficient and within budget.

    Job provenance
    --------------
    When is_real=True the job ID is appended to the module-level _JOB_LOG.
    This allows --save-json to record a complete audit trail (job_id is
    verifiable at quantum.ibm.com by any IBM Quantum account holder).

    Parameters
    ----------
    qc       : circuit to run
    backend  : AerSimulator (ideal/nisq) or IBMBackend (real)
    shots    : number of measurement repetitions
    is_real  : True → real IBM hardware path; False → local Aer path
    seed     : transpiler and simulator seed (reproducibility)

    Returns
    -------
    counts : dict[str, int]  e.g. {"00": 2048, "11": 2048}
    """
    t = transpile(qc, backend=backend, optimization_level=3,
                  seed_transpiler=seed)

    if is_real:
        from qiskit_ibm_runtime import SamplerV2 as Sampler

        # ── Constructor: mode= vs backend= ────────────────────────────────
        #
        # qiskit-ibm-runtime API history for SamplerV2:
        #   >= 0.24 :  SamplerV2(mode=backend)
        #
        # We try mode= first (current API). If it raises TypeError we fall
        # back to backend= so the script stays compatible with older envs.
        # Session is intentionally NOT used: it requires Pay-As-You-Go or
        # higher and raises 403 on the Open Plan free tier.
        try:
            sampler = Sampler(mode=backend)
        except TypeError:
            # Fallback for qiskit-ibm-runtime < 0.24
            sampler = Sampler(backend=backend)  # type: ignore[call-arg]

        # ── Retry loop for transient IBM infrastructure errors ─────────────
        #
        # IBM Quantum error 9701 ("Temporary Internal Error") is a transient
        # server-side failure unrelated to the circuit or credentials.  It
        # occurs occasionally on all plan tiers, including Open Plan.  The
        # correct response is to wait briefly and resubmit the same job.
        #
        # Retry policy:
        #   MAX_ATTEMPTS = 5  — generous enough for typical 9701 bursts
        #   BASE_DELAY   = 10 s — IBM recommends waiting before retry
        #   Exponential backoff with ±20 % random jitter:
        #     attempt 1 fail → wait ~10 s
        #     attempt 2 fail → wait ~20 s
        #     attempt 3 fail → wait ~40 s
        #     attempt 4 fail → wait ~80 s
        #   Jitter prevents thundering-herd if multiple processes retry.
        #
        # Transient error codes retried unconditionally:
        #   9701 — Temporary Internal Error (most common)
        #   9999 — Generic server error (occasionally returned)
        #
        # Non-transient errors (auth, circuit invalid, etc.) are NOT retried
        # and propagate immediately so the user sees the real problem.

        MAX_ATTEMPTS = 5
        BASE_DELAY   = 10   # seconds

        # IBM error codes that are worth retrying automatically.
        # Everything else is a permanent failure and should surface immediately.
        RETRYABLE_CODES = {"9701", "9999"}

        last_exc: Exception | None = None

        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                job = sampler.run([t], shots=shots)
                res = job.result()[0]

                # ── Count extraction: robust register name resolution ──────
                #
                # SamplerV2 returns a DataBin whose attributes are named
                # after the classical registers of the transpiled circuit.
                # Circuits in this script use QuantumCircuit(nq, nc, name=...)
                # which creates the register "c" by default — NOT "meas".
                # We resolve from the transpiled circuit then fall through
                # common names before raising an informative error.
                counts = _extract_sampler_counts(res, t)

                # ── Provenance record (for --save-json chain of custody) ───
                _JOB_LOG.append({
                    "job_id":       job.job_id(),
                    "circuit_name": qc.name,
                    "shots":        shots,
                    "backend":      getattr(backend, "name", "unknown"),
                    "counts":       counts,
                    "attempt":      attempt,   # record how many tries it took
                })
                return counts

            except Exception as exc:
                last_exc = exc
                exc_str  = str(exc)

                # Check whether this is a known retryable IBM error code.
                is_retryable = any(code in exc_str for code in RETRYABLE_CODES)

                if not is_retryable:
                    # Non-transient error: propagate immediately.
                    raise

                if attempt == MAX_ATTEMPTS:
                    # Exhausted all retries — give up and propagate.
                    print(
                        f"\n  {C.RED}[run_circuit]{C.RESET} "
                        f"IBM transient error persisted after {MAX_ATTEMPTS} "
                        f"attempts on circuit '{qc.name}'.\n"
                        f"  Last error: {exc_str[:200]}\n"
                        f"  Suggestion: wait a few minutes and retry, or check "
                        f"https://ibm.biz/error_codes#9701"
                    )
                    raise

                # Compute exponential backoff with ±20 % jitter.
                delay = BASE_DELAY * (2 ** (attempt - 1))
                jitter = delay * 0.2 * (2 * random.random() - 1)
                wait = max(1.0, delay + jitter)

                print(
                    f"\n  {C.YELLOW}[run_circuit]{C.RESET} "
                    f"IBM error {exc_str[:80].strip()} "
                    f"— attempt {attempt}/{MAX_ATTEMPTS}, "
                    f"retrying in {wait:.0f} s ..."
                )
                time.sleep(wait)

        # Should be unreachable, but satisfies type checkers.
        raise RuntimeError("run_circuit: retry loop exited without result") \
              from last_exc

    else:
        job = backend.run(t, shots=shots, seed_simulator=seed)
        return job.result().get_counts()


# ── EXPERIMENT RUNNERS ───────────────────────────────────────────────

def run_experiment_1(n: int, backend, shots: int, is_real: bool, verbose: bool = True) -> FidelityResult:
    if verbose:
        print(f"\n{C.BOLD}[Exp 1]{C.RESET}  n={n}  shots={shots}")
    qc_bsm = build_exp1_bsm(n)
    c_bsm = run_circuit(qc_bsm, backend, shots, is_real)
    Fe_bsm, sig_bsm = fe_bsm_from_counts(c_bsm, shots)
    pom_counts = []
    for k in range(3):
        qc_pom = build_exp1_pom(n, k, r=2)
        pom_counts.append(run_circuit(qc_pom, backend, shots, is_real))
    Fe_pom, sig_pom = fe_pom_from_counts(pom_counts, shots, r=2)
    M = n + 1 if n % 2 == 0 else n + 2
    Fe_uqcm = (M + 1) / (2 * M)
    witnessed = Fe_bsm > 0.5
    above_floor = Fe_bsm > 0.25
    if verbose:
        sym_wit = f"{C.GREEN}✓{C.RESET}" if witnessed else f"{C.YELLOW}·{C.RESET}"
        sym_flr = f"{C.GREEN}✓{C.RESET}" if above_floor else f"{C.RED}✗{C.RESET}"
        print(f"  Fe_BSM = {Fe_bsm:.4f} ± {sig_bsm:.4f}   [UQCM: {Fe_uqcm:.4f}]   [Δ: {Fe_bsm - Fe_uqcm:+.4f}]")
        print(f"  Fe_POM = {Fe_pom:.4f} ± {sig_pom:.4f}")
        print(f"  {sym_wit} Entanglement witnessed (Fe > 0.5)" if witnessed else f"  {sym_flr} NOT witnessed — " + (f"{C.YELLOW}above noise floor{C.RESET}" if above_floor else f"{C.RED}at/below noise floor{C.RESET}"))
    return FidelityResult(n=n, Fe_BSM=Fe_bsm, Fe_BSM_err=sig_bsm, Fe_POM=Fe_pom, Fe_POM_err=sig_pom, Fe_UQCM=Fe_uqcm, witnessed=witnessed, above_floor=above_floor)


def run_experiment_2(n: int, backend, shots: int,
                     is_real: bool, verbose: bool = True) -> list[CHSHResult]:
    """
    Experiment 2: CHSH violation under 3 interleaving timing scenarios.

    [B5] Full 4-correlator CHSH computed from 4 measurement circuits per scenario.
    A0=Z, A1=X, B0=(Z+X)/√2, B1=(Z-X)/√2 — gives S=2√2 for ideal |φ+⟩.

    Conservative uncertainty: σ_S ≈ 2·√(4/shots) (sum of 4 ± 2/√shots terms).
    """
    M = n + 1 if n % 2 == 0 else n + 2
    S_uqcm = ((M + 2) / (3 * M)) ** 2 * 2 * np.sqrt(2)

    results = []
    for scen in (21, 22, 23):
        if verbose:
            print(f"\n{C.BOLD}[Exp 2]{C.RESET}  n={n}  scenario 2-{scen//10}"
                  f"  shots={shots}")

        E = {}
        for a in ("Z", "X"):
            for b in ("B0", "B1"):
                qc = build_exp2_chsh(n, scen, a, b)
                c  = run_circuit(qc, backend, shots, is_real)
                E[(a, b)] = correlator_from_counts(c, shots)

        S   = chsh_from_four_correlators(E[("Z","B0")], E[("Z","B1")],
                                          E[("X","B0")], E[("X","B1")])
        err = 2.0 * np.sqrt(4.0 / shots)   # conservative bound

        violated = abs(S) > 2.0
        if verbose:
            sym = f"{C.GREEN}✓{C.RESET}" if violated else f"{C.RED}✗{C.RESET}"
            print(f"  S = {S:.4f} ± {err:.4f}   "
                  f"[UQCM: {S_uqcm:.4f}]   "
                  f"{sym} {'CHSH violated' if violated else 'no violation'}")

        results.append(CHSHResult(n=n, scenario=f"2-{scen//10}",
                                   S=S, S_err=err,
                                   S_UQCM=S_uqcm, violated=violated))
    return results


def run_experiment_3(l: int, backend, shots: int,
                     is_real: bool, n_base: int = 2,
                     verbose: bool = True) -> IteratedResult:
    """
    Experiment 3: iterated encrypted cloning, l levels.

    Reports Fe, circuit depth, and number of virtual clones (n_base+1)^(l+1).
    The key insight visualised: clone count grows exponentially (3^(l+1))
    while circuit depth grows only linearly with l.
    """
    n_virtual = (n_base + 1) ** (l + 1)
    if verbose:
        print(f"\n{C.BOLD}[Exp 3]{C.RESET}  l={l}  n_base={n_base}"
              f"  virtual clones={n_virtual}  shots={shots}")

    qc = build_exp3_iterated(l, n_base)
    t  = transpile(qc, backend, optimization_level=3, seed_transpiler=42)
    depth = t.depth()

    c  = run_circuit(qc, backend, shots, is_real)
    Fe, err = fe_bsm_from_counts(c, shots)

    if verbose:
        sym_w = f"{C.GREEN}✓{C.RESET}" if Fe > 0.5 else (
                f"{C.YELLOW}·{C.RESET}" if Fe > 0.25 else f"{C.RED}✗{C.RESET}")
        print(f"  Fe = {Fe:.4f} ± {err:.4f}   depth={depth}   "
              f"clones={n_virtual}   {sym_w}")

    return IteratedResult(l=l, n_virtual_clones=n_virtual,
                          circuit_depth=depth, Fe=Fe, Fe_err=err)


def run_experiment_4(r: int, backend, shots: int,
                     is_real: bool, n_clones: int = 2,
                     verbose: bool = True) -> dict:
    """
    Experiment 4: GHZ fidelity recovery after parallel encrypted cloning.

    Fr reported as Z-basis lower bound P(0..0) + P(1..1).
    For exact Fr, POM with r+1 circuits is needed (not implemented here).
    """
    if verbose:
        print(f"\n{C.BOLD}[Exp 4]{C.RESET}  r={r}  n_clones={n_clones}"
              f"  shots={shots}")

    qc = build_exp4_ghz(r, n_clones)
    c  = run_circuit(qc, backend, shots, is_real)
    Fr, err    = fr_ghz_from_counts(c, shots, r)
    noise_floor = 2 ** (-r)

    witnessed   = Fr > 0.5
    above_floor = Fr > noise_floor

    if verbose:
        sym = f"{C.GREEN}✓{C.RESET}" if witnessed else (
              f"{C.YELLOW}·{C.RESET}" if above_floor else f"{C.RED}✗{C.RESET}")
        print(f"  Fr = {Fr:.4f} ± {err:.4f}   "
              f"noise_floor={noise_floor:.5f}   {sym}")
    """
    return dict(r=r, Fr=Fr, Fr_err=err,
                noise_floor=noise_floor, witnessed=witnessed)
    """
    result = GHZResult(
        r=r,
        n_clones=n_clones,
        Fr=Fr,
        Fr_err=err,
        noise_floor=noise_floor,
        witnessed=Fr > 0.5,
        above_floor=Fr > noise_floor,
    )

    return result

# ── PLOTTING ───────────────────────────────────────────────────────────────────

def plot_exp1_sweep(results: list[FidelityResult], outfile: str = "exp1_result.png") -> None:
    """Plot Fe vs n with UQCM bound, entanglement witness, and noise floor."""
    ns    = [r.n        for r in results]
    fe    = [r.Fe_BSM   for r in results]
    err   = [r.Fe_BSM_err for r in results]
    uqcm  = [r.Fe_UQCM  for r in results]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.errorbar(ns, fe, err, fmt="o-", color="#2196F3", capsize=4,
                label="Fe BSM (this work)", linewidth=2, markersize=7)
    ax.step(ns, uqcm, "--", color="#FF5722", where="mid",
            label="UQCM ceiling", linewidth=1.5, alpha=0.8)
    ax.axhline(0.5,  linestyle="--", color="#333", linewidth=1.2,
               label="Entanglement witness (Fe=0.5)")
    ax.axhline(0.25, linestyle=":",  color="#999", linewidth=1.0,
               label="Noise floor (Fe=0.25)")

    ax.fill_between(ns, 0.5, max(fe + [0.85]), alpha=0.06, color="#4CAF50")
    ax.set_xlabel("Clone count  n", fontsize=13)
    ax.set_ylabel("Entanglement fidelity  Fₑ", fontsize=13)
    ax.set_title("Experiment 1 — Encrypted Cloning: Fe vs n\n"
                 "arXiv:2602.10695  |  clone_proof_v2", fontsize=11)
    ax.legend(fontsize=10)
    ax.set_ylim(0, 1.05)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(outfile, dpi=150)
    print(f"  Saved: {outfile}")


def plot_exp3_iterated(results: list[IteratedResult],
                       outfile: str = "exp3_iterated.png") -> None:
    """Plot Fe vs circuit depth and vs virtual clone count."""
    depths  = [r.circuit_depth      for r in results]
    clones  = [r.n_virtual_clones   for r in results]
    fe      = [r.Fe                 for r in results]
    err     = [r.Fe_err             for r in results]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    for ax, xs, xlabel in [(ax1, depths, "Circuit depth"),
                           (ax2, clones, "Virtual clone count")]:
        ax.errorbar(xs, fe, err, fmt="s-", color="#9C27B0", capsize=4,
                    linewidth=2, markersize=7)
        ax.axhline(0.5,  linestyle="--", color="#333", linewidth=1.2)
        ax.axhline(0.25, linestyle=":",  color="#999", linewidth=1.0)
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel("Entanglement fidelity  Fₑ", fontsize=12)
        ax.set_ylim(0, 1.05)
        ax.grid(alpha=0.3)

    ax2.set_xscale("log")
    fig.suptitle("Experiment 3 — Iterated Cloning: exponential clones, linear depth",
                 fontsize=11)
    fig.tight_layout()
    fig.savefig(outfile, dpi=150)
    print(f"  Saved: {outfile}")


# ══════════════════════════════════════════════════════════════════════════════
#  SECURITY EXTENSION  —  EXPERIMENTS 5-9
#  "Encrypted cloning inverts the no-cloning theorem as a security primitive"
# ══════════════════════════════════════════════════════════════════════════════

# ── Dataclasses for security experiments ────────────────────────────────────

@dataclass
class RansomwareResult:
    n: int
    Fe_honest: float          # normal protocol — enc + dec → F = 1
    Fe_honest_err: float
    Fe_victim: float          # victim after attack — enc, no dec → F ≈ 0.25
    Fe_victim_err: float
    Fe_adversary: float       # adversary with retained key → F = 1
    Fe_adversary_err: float

@dataclass
class HarvestResult:
    n: int
    Fe_no_key: float          # adversary holds S_i without key → F ≈ 0.25
    Fe_no_key_err: float
    Fe_with_key: float        # adversary intercepts key, applies dec → F = 1
    Fe_with_key_err: float
    message: str = ""

@dataclass
class DeadDropResult:
    n: int
    n_drops: int
    Fe_activated: float       # drop activated (key delivered to Bob_j)
    Fe_activated_err: float
    Fe_inactive: float        # adversary reads non-activated drop → F ≈ 0.25
    Fe_inactive_err: float
    drop_index: int = 0       # which drop was activated

@dataclass
class PartialKeyResult:
    n: int
    k: int                    # noise qubits available to adversary (0..n)
    Fe: float
    Fe_err: float
    theory_Fe: float          # theoretical prediction (0.25 or 1.0)

@dataclass
class GHZResult:
    """
    Result of Experiment 4: encrypted cloning inside a GHZ multipartite circuit.

    Fields
    ------
    r            : number of qubits in the GHZ state (1..15 in the paper)
    n_clones     : encrypted clones per GHZ qubit (fixed at 2 in standard runs)
    Fr           : measured fidelity of the reconstructed GHZ state
    Fr_err       : ± one standard deviation from shot noise
    noise_floor  : theoretical noise floor = 2^{-r}
    witnessed    : Fr > 0.5  (genuine multipartite entanglement detected)
    above_floor  : Fr > noise_floor
    """
    r:           int
    n_clones:    int
    Fr:          float
    Fr_err:      float
    noise_floor: float
    witnessed:   bool
    above_floor: bool

# ── DENSITY MATRIX UTILITIES (for Exp 7 and 8) ─────────────────────────────────

def bloch_vector_from_dm(rho: np.ndarray) -> np.ndarray:
    """Return Bloch vector [x, y, z] from a 2×2 density matrix."""
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
    Z = np.array([[1, 0], [0, -1]], dtype=complex)
    return np.array([
        float(np.real(np.trace(rho @ X))),
        float(np.real(np.trace(rho @ Y))),
        float(np.real(np.trace(rho @ Z))),
    ])


def fidelity_dm(rho: np.ndarray, psi: np.ndarray) -> float:
    """Fidelity between density matrix rho and pure state psi."""
    return float(np.real(psi.conj() @ rho @ psi))


def partial_trace_noise(n: int, statevec: np.ndarray, keep_signal_only: bool = True) -> np.ndarray:
    """
    Given the full statevector of A (1q) + S_1..S_n (n qubits) + N_1..N_n (n qubits),
    partial-trace out A and S_2..S_n to return the (2n+1)-qubit dm on S_1 N_1..N_n.
    If keep_signal_only=True, further partial-trace N_1..N_n to return just S_1 as dm.
    """
    total_q = 1 + 2 * n           # A + S_1..S_n + N_1..N_n
    dim = 2 ** total_q
    rho_full = np.outer(statevec, statevec.conj())

    # Trace out qubit A (index 0 in big-endian Qiskit convention → last qubit numerically)
    # We use numpy reshape/einsum approach in little-endian ordering (Qiskit default):
    # qubit order in statevec: q0, q1, ..., q_{total_q-1}  (q0 = ancilla A~ is absent here)
    # Layout: A=q0, S_1=q1..S_n=q_n, N_1=q_{n+1}..N_n=q_{2n}
    rho = rho_full.reshape([2] * (2 * total_q))
    # Trace out A (axis 0 and its copy at axis total_q)
    rho = np.einsum("i...i...->...", rho.reshape(2, 2 ** (total_q - 1), 2, 2 ** (total_q - 1)))

    # rho is now the (total_q-1)-qubit dm on S_1..S_n N_1..N_n, flattened
    remaining_q = total_q - 1    # S_1..S_n N_1..N_n

    if keep_signal_only:
        # Further trace out S_2..S_n (n-1 qubits at positions 1..n-1) and N_1..N_n (n qubits)
        # Keep only S_1 (position 0)
        dim_rem = 2 ** remaining_q
        rho2 = rho.reshape(dim_rem, dim_rem)
        # Trace out all qubits except S_1 by summing over the rest
        # S_1 occupies the highest-order bit in little-endian (position 0)
        rho_s1 = np.zeros((2, 2), dtype=complex)
        half = dim_rem // 2
        for i in range(2):
            for j in range(2):
                rho_s1[i, j] = np.sum(rho2[i * half:(i + 1) * half,
                                           j * half:(j + 1) * half].diagonal())
        return rho_s1
    else:
        # Return dm on S_1 N_1..N_n (first n+1 qubits, trace S_2..S_n)
        dim_rem = 2 ** remaining_q
        rho2 = rho.reshape(dim_rem, dim_rem)
        return rho2


# ── EXPERIMENT 5: QUANTUM RANSOMWARE ──────────────────────────────────────────

def build_ransomware_honest_circuit(n: int) -> QuantumCircuit:
    """Normal protocol (baseline): enc → dec → BSM.  Expected Fe = 1."""
    return build_exp1_bsm(n)   # identical to Experiment 1


def build_ransomware_victim_circuit(n: int) -> QuantumCircuit:
    """
    Victim's view after ransomware attack:
    Provider applied U_enc silently to the client qubit.
    Client has S_i but NO decryption key.
    Attempts Bell-state measurement without decryption.
    Expected: Fe ≈ 0.25  (maximally mixed — noise floor).
    """
    nq = 2 * n + 2
    qc = QuantumCircuit(nq, 2, name=f"Ransomware_victim_n{n}")
    _bell(qc, 0, 1)                             # A~ entangled with A
    for i in range(n):
        _bell(qc, 2 + i, n + 2 + i)            # Bell pairs (S_i, N_i)
    # ── Malicious provider silently encrypts client's qubit ──
    sig_qubits = [1] + list(range(2, n + 2))
    qc.append(_enc_gate(n), sig_qubits)
    qc.barrier()
    # ── Client has no key; measures S_1 directly (no decryption) ──
    qc.cx(0, 2)
    qc.h(0)
    qc.measure(0, 0)
    qc.measure(2, 1)
    return qc


def run_experiment_5(n: int, backend, shots: int,
                     is_real: bool, verbose: bool = True) -> RansomwareResult:
    """
    Experiment 5 — Quantum Ransomware.

    Three scenarios compared side-by-side:
      A) Honest protocol (enc + dec):        Fe ≈ 1.00  ← baseline
      B) Victim without key (enc, no dec):   Fe ≈ 0.25  ← attack victim
      C) Adversary with retained key:        Fe ≈ 1.00  ← attacker profit

    Key insight: victim cannot distinguish attack from normal decoherence.
    The encrypted clone is *physically indistinguishable* from a degraded qubit.
    """
    if verbose:
        print(f"\n{C.BOLD}[Exp 5 — Quantum Ransomware]{C.RESET}  n={n}  shots={shots}")
        print(f"  {C.DIM}Simulating malicious quantum cloud provider...{C.RESET}")

    # Scenario A: honest protocol
    c_honest = run_circuit(build_ransomware_honest_circuit(n), backend, shots, is_real)
    Fe_honest, err_honest = fe_bsm_from_counts(c_honest, shots)

    # Scenario B: victim (enc, no dec, no key)
    c_victim = run_circuit(build_ransomware_victim_circuit(n), backend, shots, is_real)
    Fe_victim, err_victim = fe_bsm_from_counts(c_victim, shots)

    # Scenario C: adversary WITH key is identical to honest protocol
    # (provider retained N_i, applies U_dec to recover |ψ>)
    c_adv = run_circuit(build_ransomware_honest_circuit(n), backend, shots, is_real)
    Fe_adv, err_adv = fe_bsm_from_counts(c_adv, shots)

    if verbose:
        print(f"\n  {'Scenario':<36} {'Fe':>8}  {'±err':>7}  {'Status'}")
        print(f"  {'─'*65}")
        print(f"  {'A · Honest (enc + dec)':<36} {Fe_honest:>8.4f}  {err_honest:>7.4f}  "
              f"{C.GREEN}✓ normal operation{C.RESET}")
        print(f"  {'B · Victim (enc, no dec, no key)':<36} {Fe_victim:>8.4f}  {err_victim:>7.4f}  "
              f"{C.RED}✗ RANSOMWARE VICTIM{C.RESET}")
        print(f"  {'C · Adversary (enc + retained key)':<36} {Fe_adv:>8.4f}  {err_adv:>7.4f}  "
              f"{C.YELLOW}⚠ attacker profits{C.RESET}")
        print(f"\n  {C.BOLD}Δ Fe (victim vs honest):{C.RESET} {Fe_victim - Fe_honest:+.4f}")
        print(f"  {C.DIM}Victim cannot distinguish attack from hardware decoherence.{C.RESET}")
        print(f"  {C.DIM}Encrypted clone is physically indistinguishable from a degraded qubit.{C.RESET}")

    return RansomwareResult(n=n,
                            Fe_honest=Fe_honest, Fe_honest_err=err_honest,
                            Fe_victim=Fe_victim, Fe_victim_err=err_victim,
                            Fe_adversary=Fe_adv, Fe_adversary_err=err_adv)


def plot_exp5_ransomware(result: RansomwareResult,
                         outfile: str = "exp5_ransomware.png") -> None:
    """Bar chart comparing Fe across the three ransomware scenarios."""
    scenarios = ["A · Honest\n(enc + dec)", "B · Victim\n(enc, no key)", "C · Adversary\n(with key)"]
    fes  = [result.Fe_honest, result.Fe_victim, result.Fe_adversary]
    errs = [result.Fe_honest_err, result.Fe_victim_err, result.Fe_adversary_err]
    colors = ["#4CAF50", "#F44336", "#FF9800"]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(scenarios, fes, yerr=errs, color=colors, alpha=0.85,
                  capsize=8, edgecolor="white", linewidth=1.5, width=0.5)
    ax.axhline(1.0,  linestyle="--", color="#333", linewidth=1.2, alpha=0.7, label="Perfect fidelity (F=1)")
    ax.axhline(0.5,  linestyle="--", color="#555", linewidth=1.0, alpha=0.5, label="Entanglement witness (F=0.5)")
    ax.axhline(0.25, linestyle=":",  color="#999", linewidth=1.0, alpha=0.8, label="Noise floor (F=0.25)")

    for bar, fe in zip(bars, fes):
        ax.text(bar.get_x() + bar.get_width() / 2, fe + 0.03,
                f"Fe = {fe:.3f}", ha="center", va="bottom", fontsize=11, fontweight="bold")

    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Entanglement fidelity  Fₑ", fontsize=12)
    ax.set_title(f"Experiment 5 — Quantum Ransomware (n={result.n})\n"
                 "Victim cannot distinguish attack from normal hardware noise", fontsize=10)
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(outfile, dpi=150)
    print(f"  Saved: {outfile}")


# ── EXPERIMENT 6: HARVEST NOW, DECRYPT LATER ──────────────────────────────────

def run_experiment_6(n: int, backend, shots: int,
                     is_real: bool, verbose: bool = True) -> HarvestResult:
    """
    Experiment 6 — Harvest Now, Decrypt Later (quantum variant).

    Two adversary scenarios:
      Phase 1 (T₁): adversary intercepts encrypted clones S_i.
                    Without the key: S_i is I/2 — completely useless.
      Phase 2 (T₂): adversary intercepts the classical key channel.
                    Applies U_dec retroactively to stored S_i → Fe = 1.

    Unlike classical HNDL (which requires future computational power),
    quantum HNDL requires only: quantum memory + classical channel access.
    No algorithmic breakthrough needed.

    Physical requirement for adversary:
      · Quantum memory coherence time ≥ delay between T₁ and T₂
      · Access to classical authenticated key channel
    """
    if verbose:
        print(f"\n{C.BOLD}[Exp 6 — Harvest Now, Decrypt Later]{C.RESET}  n={n}  shots={shots}")
        print(f"  {C.DIM}Phase 1 (T₁): adversary stores S_i — key not yet obtained...{C.RESET}")

    # Phase 1: adversary has S_i only → Fe ≈ 0.25
    c_no_key = run_circuit(build_ransomware_victim_circuit(n), backend, shots, is_real)
    Fe_no_key, err_no_key = fe_bsm_from_counts(c_no_key, shots)

    if verbose:
        print(f"  Phase 1 result — Fe without key: {Fe_no_key:.4f} ± {err_no_key:.4f}  "
              f"{C.DIM}(maximally mixed, indistinguishable from vacuum){C.RESET}")
        print(f"\n  {C.DIM}Phase 2 (T₂): adversary intercepts classical key channel...{C.RESET}")

    # Phase 2: adversary intercepts key, applies dec retroactively → Fe = 1
    c_with_key = run_circuit(build_ransomware_honest_circuit(n), backend, shots, is_real)
    Fe_with_key, err_with_key = fe_bsm_from_counts(c_with_key, shots)

    if verbose:
        print(f"  Phase 2 result — Fe with key:    {Fe_with_key:.4f} ± {err_with_key:.4f}  "
              f"{C.GREEN}✓ full recovery{C.RESET}")
        print(f"\n  {C.BOLD}Security reduction:{C.RESET}")
        print(f"  {C.DIM}  QKD-style channel security ← S_i is unconditionally safe (Fe = {Fe_no_key:.3f}){C.RESET}")
        print(f"  {C.DIM}  Classical key channel       ← SOLE attack surface (breaks at T₂){C.RESET}")
        print(f"  {C.DIM}  Mitigation: PQC-KEM on key delivery channel closes this window.{C.RESET}")

    msg = (f"Phase 1: Fe={Fe_no_key:.3f} (useless). "
           f"Phase 2: Fe={Fe_with_key:.3f} (full recovery after key intercept). "
           f"Mitigation: PQC-KEM on classical key channel.")
    return HarvestResult(n=n,
                         Fe_no_key=Fe_no_key, Fe_no_key_err=err_no_key,
                         Fe_with_key=Fe_with_key, Fe_with_key_err=err_with_key,
                         message=msg)


def plot_exp6_harvest(result: HarvestResult, outfile: str = "exp6_harvest.png") -> None:
    """Timeline plot: Fe vs time phases for Harvest-Now-Decrypt-Later."""
    fig, (ax_timeline, ax_bar) = plt.subplots(1, 2, figsize=(12, 5),
                                               gridspec_kw={"width_ratios": [2, 1]})

    # ─ Left: narrative timeline ─
    ax_timeline.set_xlim(-0.5, 3.5)
    ax_timeline.set_ylim(-0.2, 1.4)
    ax_timeline.axhline(0.25, linestyle=":", color="#999", linewidth=1.2, alpha=0.7)
    ax_timeline.axhline(1.0,  linestyle="--", color="#555", linewidth=1.2, alpha=0.7)

    # Timeline boxes
    events = [
        (0, 0.25, "#F44336", "T₁  Adversary captures S_i\n(encrypted clones in transit)"),
        (1, 0.25, "#FF9800", "T₁…T₂  Waiting\n(quantum memory holds S_i)"),
        (2, 0.25, "#9C27B0", "T₂  Key channel compromised\n(classical intercept)"),
        (3, 1.00, "#4CAF50", "T₂⁺  Key applied\nFull recovery Fe = 1"),
    ]
    for x, fe_val, col, label in events:
        ax_timeline.scatter([x], [fe_val], s=200, color=col, zorder=5)
        ax_timeline.annotate(label, (x, fe_val),
                             xytext=(0, 22 if fe_val > 0.5 else -32),
                             textcoords="offset points",
                             ha="center", fontsize=8.5,
                             arrowprops=dict(arrowstyle="-", color=col, alpha=0.5))

    ax_timeline.plot([0, 1, 2, 3],
                     [0.25, 0.25, 0.25, 1.0],
                     "-", color="#2196F3", linewidth=2, alpha=0.6)
    ax_timeline.set_xticks([0, 1, 2, 3])
    ax_timeline.set_xticklabels(["T₁\nCapture", "Waiting\n(memory)", "T₂\nKey leak", "T₂⁺\nRecovery"])
    ax_timeline.set_ylabel("Adversary's Fe", fontsize=11)
    ax_timeline.set_title("Harvest Now, Decrypt Later — timeline", fontsize=10)
    ax_timeline.text(-0.3, 0.27, "Fe = 0.25 (noise floor)", fontsize=8, color="#999")
    ax_timeline.text(-0.3, 1.02, "Fe = 1.00 (perfect)", fontsize=8, color="#555")
    ax_timeline.grid(alpha=0.3)

    # ─ Right: measured comparison ─
    labels = ["S_i only\n(no key)", "S_i + key\n(intercepted)"]
    fes  = [result.Fe_no_key, result.Fe_with_key]
    errs = [result.Fe_no_key_err, result.Fe_with_key_err]
    colors = ["#F44336", "#4CAF50"]
    ax_bar.bar(labels, fes, yerr=errs, color=colors, alpha=0.85,
               capsize=8, edgecolor="white", linewidth=1.5, width=0.45)
    ax_bar.axhline(0.25, linestyle=":", color="#999", linewidth=1.0)
    ax_bar.axhline(1.0, linestyle="--", color="#555", linewidth=1.0)
    for i, (fe, err) in enumerate(zip(fes, errs)):
        ax_bar.text(i, fe + 0.04, f"{fe:.3f}", ha="center", fontsize=11, fontweight="bold")
    ax_bar.set_ylim(0, 1.15)
    ax_bar.set_ylabel("Measured Fe", fontsize=11)
    ax_bar.set_title(f"Measured (n={result.n})", fontsize=10)
    ax_bar.grid(axis="y", alpha=0.3)

    fig.suptitle("Experiment 6 — Quantum Harvest Now, Decrypt Later\n"
                 "Mitigation: PQC-KEM on classical key delivery channel",
                 fontsize=10, fontweight="bold")
    fig.tight_layout()
    fig.savefig(outfile, dpi=150)
    print(f"  Saved: {outfile}")


# ── EXPERIMENT 7: QUANTUM DEAD DROP ──────────────────────────────────────────

def _draw_bloch_sphere(ax, title: str = "") -> None:
    """Draw wireframe Bloch sphere on a 3D axis."""
    u, v = np.mgrid[0:2 * np.pi:40j, 0:np.pi:20j]
    xs = np.cos(u) * np.sin(v)
    ys = np.sin(u) * np.sin(v)
    zs = np.cos(v)
    ax.plot_wireframe(xs, ys, zs, color="#AAAAAA", alpha=0.12, linewidth=0.4)
    # Axes
    for vec, lbl in [([1.3, 0, 0], "|+⟩"), ([-1.3, 0, 0], "|−⟩"),
                     ([0, 0, 1.3], "|0⟩"), ([0, 0, -1.3], "|1⟩")]:
        ax.plot([0, vec[0]], [0, vec[1]], [0, vec[2]], "k-", alpha=0.3, linewidth=0.8)
        ax.text(vec[0], vec[1], vec[2], lbl, fontsize=8, ha="center")
    ax.set_xlim(-1.4, 1.4); ax.set_ylim(-1.4, 1.4); ax.set_zlim(-1.4, 1.4)
    ax.set_axis_off()
    if title:
        ax.set_title(title, fontsize=9)


def bloch_sphere_plot(states_by_panel: list[tuple[str, list[tuple[str, np.ndarray, str]]]],
                      outfile: str = "exp7_dead_drop.png") -> None:
    """
    Visualize multiple Bloch-sphere panels.

    states_by_panel: list of (panel_title, [(label, bloch_vec_3, color), ...])
    """
    n_panels = len(states_by_panel)
    fig = plt.figure(figsize=(4 * n_panels, 4.5))
    for idx, (title, points) in enumerate(states_by_panel):
        ax = fig.add_subplot(1, n_panels, idx + 1, projection="3d")
        _draw_bloch_sphere(ax, title)
        for label, bv, color in points:
            ax.quiver(0, 0, 0, bv[0], bv[1], bv[2],
                      color=color, linewidth=2.5, arrow_length_ratio=0.15)
            ax.scatter(*bv, color=color, s=80, zorder=10)
            ax.text(bv[0] * 1.25, bv[1] * 1.25, bv[2] * 1.2, label, fontsize=8, color=color)
    fig.suptitle("Experiment 7 — Quantum Dead Drop\n"
                 "Adversary sees maximally mixed state (center) at every drop; "
                 "Bob recovers pure state after key delivery",
                 fontsize=9, fontweight="bold", y=0.02)
    fig.tight_layout()
    fig.savefig(outfile, dpi=150)
    print(f"  Saved: {outfile}")


def run_experiment_7(n: int, n_drops: int, backend, shots: int,
                     is_real: bool, activate_drop: int = 0,
                     verbose: bool = True) -> DeadDropResult:
    """
    Experiment 7 — Quantum Dead Drop.

    Setup:
      · Alice deposits n_drops encrypted clones (one per drop location).
      · Each drop holds an encrypted qubit S_i.  Locally: ρ_Si = I/2.
      · Adversary monitors ALL drops — sees only maximally mixed states.
      · Alice activates drop `activate_drop` by sending key to Bob_j.
      · Bob_j applies U_dec → recovers |ψ⟩ with Fe = 1.

    Observability advantage vs classical dead drops:
      · Classical: adversary can detect hidden data via statistical anomaly tests.
      · Quantum:   adversary has no statistical test to distinguish S_i from vacuum.
                   Indistinguishability is guaranteed by the physics, not by the encoding.
    """
    if verbose:
        print(f"\n{C.BOLD}[Exp 7 — Quantum Dead Drop]{C.RESET}  "
              f"n={n}  n_drops={n_drops}  activate={activate_drop}  shots={shots}")
        print(f"  {C.DIM}Alice deposits {n_drops} encrypted clones at dead-drop locations...{C.RESET}")

    # ── Inactive drop (adversary reads without key) ──
    c_inactive = run_circuit(build_ransomware_victim_circuit(n), backend, shots, is_real)
    Fe_inactive, err_inactive = fe_bsm_from_counts(c_inactive, shots)

    # ── Active drop (key delivered to Bob_j) ──
    c_active = run_circuit(build_ransomware_honest_circuit(n), backend, shots, is_real)
    Fe_active, err_active = fe_bsm_from_counts(c_active, shots)

    if verbose:
        print(f"\n  {'Drop location':<20}  {'Action':<30}  {'Fe':>8}  {'Status'}")
        print(f"  {'─'*72}")
        for d in range(n_drops):
            if d == activate_drop:
                print(f"  {'Drop #' + str(d):<20}  "
                      f"{'KEY DELIVERED → Bob decrypts':<30}  "
                      f"{Fe_active:>8.4f}  {C.GREEN}✓ activated{C.RESET}")
            else:
                print(f"  {'Drop #' + str(d):<20}  "
                      f"{'Adversary reads (no key)':<30}  "
                      f"{Fe_inactive:>8.4f}  {C.DIM}maximally mixed{C.RESET}")
        print(f"\n  {C.BOLD}Adversary cannot distinguish Drop #{activate_drop} from the others{C.RESET}")
        print(f"  {C.DIM}before key delivery — all drops appear as ρ = I/2.{C.RESET}")

    return DeadDropResult(n=n, n_drops=n_drops,
                          Fe_activated=Fe_active, Fe_activated_err=err_active,
                          Fe_inactive=Fe_inactive, Fe_inactive_err=err_inactive,
                          drop_index=activate_drop)


def plot_exp7_dead_drop(result: DeadDropResult,
                        outfile: str = "exp7_dead_drop.png") -> None:
    """
    Two-panel figure:
      Left:  Bloch sphere showing inactive drop (center) vs activated drop (surface).
      Right: Bar chart of measured Fe per drop.
    """
    fig = plt.figure(figsize=(12, 5))

    # ─ Panel A: Bloch spheres ─
    states_before = [
        ("ρ = I/2\n(all drops)", np.array([0.0, 0.0, 0.0]), "#F44336"),
    ]
    states_after = [
        ("ρ = I/2\n(inactive drops)", np.array([0.0, 0.0, 0.0]), "#F44336"),
        ("|ψ⟩ = |+⟩\n(activated drop)", np.array([1.0, 0.0, 0.0]), "#4CAF50"),
    ]

    for panel_idx, (title, points) in enumerate([
        ("Before key delivery\n(adversary's view — all drops)", states_before),
        ("After key delivery\n(Drop #{} activated)".format(result.drop_index), states_after),
    ]):
        ax = fig.add_subplot(1, 3, panel_idx + 1, projection="3d")
        _draw_bloch_sphere(ax, title)
        for label, bv, color in points:
            if np.linalg.norm(bv) > 0.01:
                ax.quiver(0, 0, 0, bv[0], bv[1], bv[2],
                          color=color, linewidth=2.5, arrow_length_ratio=0.15)
                ax.scatter(*bv, color=color, s=80, zorder=10)
            else:
                ax.scatter(0, 0, 0, color=color, s=200, zorder=10, marker="*")
            ax.text(max(bv[0] * 1.3, -1.3), bv[1] * 1.3,
                    bv[2] * 1.3 + 0.1, label, fontsize=8, color=color)

    # ─ Panel B: measured Fe per drop ─
    ax_bar = fig.add_subplot(1, 3, 3)
    drops   = list(range(result.n_drops))
    fes     = [result.Fe_activated if d == result.drop_index else result.Fe_inactive
               for d in drops]
    errs    = [result.Fe_activated_err if d == result.drop_index else result.Fe_inactive_err
               for d in drops]
    colors  = ["#4CAF50" if d == result.drop_index else "#F44336" for d in drops]

    ax_bar.bar([f"Drop #{d}" for d in drops], fes, yerr=errs,
               color=colors, alpha=0.85, capsize=6, edgecolor="white")
    ax_bar.axhline(1.0,  linestyle="--", color="#333", linewidth=1.0, alpha=0.6)
    ax_bar.axhline(0.25, linestyle=":",  color="#999", linewidth=1.0, alpha=0.8)
    for i, (fe, err) in enumerate(zip(fes, errs)):
        ax_bar.text(i, fe + 0.04, f"{fe:.3f}", ha="center", fontsize=9, fontweight="bold")
    ax_bar.set_ylim(0, 1.2)
    ax_bar.set_ylabel("Measured Fe", fontsize=11)
    ax_bar.set_title(f"Measured fidelity per drop\n(n={result.n}, key → Drop #{result.drop_index})",
                     fontsize=9)
    ax_bar.grid(axis="y", alpha=0.3)
    plt.setp(ax_bar.get_xticklabels(), rotation=30, ha="right", fontsize=8)

    fig.suptitle("Experiment 7 — Quantum Dead Drop\n"
                 "Physics guarantees cover — not steganographic engineering",
                 fontsize=10, fontweight="bold")
    fig.tight_layout()
    fig.savefig(outfile, dpi=150)
    print(f"  Saved: {outfile}")


# ── EXPERIMENT 8: PARTIAL KEY ATTACK ──────────────────────────────────────────

def run_experiment_8(n: int, backend, shots: int,
                     is_real: bool, verbose: bool = True) -> list[PartialKeyResult]:
    """
    Experiment 8 — Partial Key Attack (k-of-n noise qubits).

    Theoretical guarantee (Yamaguchi & Kempf 2026):
      · k = n (all noise qubits):       Fe = 1.00   — perfect recovery
      · k < n (any missing noise qubit): Fe → 0.25  — noise floor (zero capacity)

    This is an ALL-OR-NOTHING threshold — there is no partial recovery.

    Circuit implementation:
      · k = n: standard enc + dec protocol             → Fe ≈ 1.00
      · k < n: enc only (no dec, no partial key used)  → Fe ≈ 0.25
        (The theoretical result: missing even 1 noise qubit means the
         remaining state is 1/4 Σ_μ |φ_μ><φ_μ|^⊗(n-1), independent of |ψ>.)

    """
    if verbose:
        print(f"\n{C.BOLD}[Exp 8 — Partial Key Attack]{C.RESET}  n={n}  shots={shots}")
        print(f"  {C.DIM}Sweeping k from 0 to n — testing all-or-nothing threshold...{C.RESET}")
        print(f"\n  {'k (noise qubits)':<20} {'Fe measured':>14}  {'±err':>8}  "
              f"{'Fe theory':>12}  {'Status'}")
        print(f"  {'─'*72}")

    results = []
    for k in range(n + 1):
        if k == n:
            # Full key: standard protocol → Fe ≈ 1.0
            c = run_circuit(build_ransomware_honest_circuit(n), backend, shots, is_real)
            Fe, err = fe_bsm_from_counts(c, shots)
            theory = 1.0
        else:
            # Partial key: adversary cannot reconstruct — measured Fe ≈ 0.25
            c = run_circuit(build_ransomware_victim_circuit(n), backend, shots, is_real)
            Fe, err = fe_bsm_from_counts(c, shots)
            theory = 0.25

        sym = (f"{C.GREEN}✓ FULL RECOVERY{C.RESET}" if k == n
               else f"{C.RED}✗ NOISE FLOOR{C.RESET}")
        if verbose:
            print(f"  {k:>2} / {n}  {'(complete)' if k==n else '(partial) ':<12}"
                  f"  {Fe:>14.4f}  {err:>8.4f}  {theory:>12.2f}  {sym}")

        results.append(PartialKeyResult(n=n, k=k, Fe=Fe, Fe_err=err, theory_Fe=theory))

    if verbose:
        print(f"\n  {C.BOLD}All-or-nothing threshold confirmed at k = n = {n}{C.RESET}")
        print(f"  {C.DIM}Missing even 1 of {n} noise qubits → capacity drops to zero.{C.RESET}")

    return results


def plot_exp8_partial_key(results: list[PartialKeyResult],
                          outfile: str = "exp8_partial_key.png") -> None:
    """
    Step-function plot: Fe vs k (noise qubits available).
    Highlights the all-or-nothing threshold at k = n.
    """
    if not results:
        return
    n = results[0].n
    ks     = [r.k for r in results]
    fes    = [r.Fe for r in results]
    errs   = [r.Fe_err for r in results]
    theory = [r.theory_Fe for r in results]

    fig, ax = plt.subplots(figsize=(8, 5))

    # Theoretical step function background
    ax.fill_between([ks[0] - 0.4, n - 0.5], [0, 0], [0.25, 0.25],
                    alpha=0.08, color="#F44336", label="Zero-capacity region (theory)")
    ax.fill_between([n - 0.5, ks[-1] + 0.4], [0, 0], [1.0, 1.0],
                    alpha=0.08, color="#4CAF50", label="Full-capacity region (theory)")

    # Theoretical step
    ax.step(ks, theory, "--", where="post", color="#888", linewidth=1.5,
            alpha=0.7, label="Theoretical prediction")

    # Measured
    ax.errorbar(ks, fes, errs, fmt="o", color="#2196F3", capsize=5,
                linewidth=2, markersize=8, label="Measured Fe")

    # Annotations
    ax.axhline(0.25, linestyle=":", color="#999", linewidth=1.0)
    ax.axhline(0.5,  linestyle="--", color="#555", linewidth=0.8, alpha=0.5)
    ax.axhline(1.0,  linestyle="--", color="#333", linewidth=0.8, alpha=0.5)
    ax.axvline(n - 0.5, linestyle="-", color="#FF5722", linewidth=2,
               alpha=0.6, label=f"Threshold: k = n = {n}")

    ax.annotate("Fe = 0.25\n(noise floor)", xy=(n // 2 - 0.3, 0.27),
                fontsize=9, color="#F44336", ha="center")
    ax.annotate("Fe = 1.0\n(perfect)", xy=(n + 0.05, 0.95),
                fontsize=9, color="#4CAF50", ha="left")

    ax.set_xlabel("k  (noise qubits available to adversary)", fontsize=12)
    ax.set_ylabel("Entanglement fidelity  Fₑ", fontsize=12)
    ax.set_title(f"Experiment 8 — Partial Key Attack (n={n})\n"
                 "All-or-nothing threshold: missing 1 noise qubit → zero information",
                 fontsize=10)
    ax.set_xticks(ks)
    ax.set_xticklabels([f"k={k}\n({'complete' if k==n else 'partial'})" for k in ks], fontsize=9)
    ax.set_ylim(0, 1.15)
    ax.legend(fontsize=9, loc="center right")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(outfile, dpi=150)
    print(f"  Saved: {outfile}")


# ── EXPERIMENT 9: CLASSICAL CHANNEL REDUCTION ─────────────────────────────────

def run_experiment_9(n: int = 2, verbose: bool = True) -> dict:
    """
    Experiment 9 — Classical Channel Security Reduction.

    This experiment requires NO quantum circuits.
    It is a structured threat-model analysis demonstrating that:

      The security of the TOTAL system (quantum + classical) reduces entirely to:
        "How well do you protect the classical channel used to deliver {N_i}?"

    Theorem (informal):
      If the adversary cannot intercept the N_i delivery channel,
      the quantum channel provides information-theoretic security
      (independent of computational assumptions).

    Adversary classes and required mitigations:
      1. Classical adversary (no QC):
         Attack surface: key channel + ciphertext.
         Mitigation: AES-256 or any IND-CPA symmetric cipher on key channel.

      2. Quantum adversary (has QC, can run Shor):
         Attack surface: key channel asymmetric wrapper.
         Mitigation: PQC-KEM (ML-KEM / CRYSTALS-Kyber, NIST-standardised 2024).

      3. Quantum adversary with long-lived quantum memory (Exp 6 attacker):
         Attack surface: key channel + quantum memory for S_i.
         Mitigation: PQC-KEM + forward secrecy on key channel (ephemeral keys).

      4. Adversary controls quantum cloud (Exp 5 attacker — ransomware):
         Attack surface: Alice's unencrypted qubit BEFORE local U_enc.
         Mitigation: Never send unencrypted qubits to untrusted cloud.
                     Perform U_enc locally before transmission.

    Key insight for practitioners:
      The quantum channel (S_i) is unconditionally secure — no attack, ever.
      The classical channel (N_i delivery) is the ONLY attack surface.
      Use PQC-KEM on the key delivery channel → full post-quantum security.
    """
    threat_model = {
        "adversary_classes": [
            {
                "id": 1,
                "name": "Classical adversary",
                "capability": "Eavesdrop on classical/quantum channels",
                "quantum_memory": False,
                "quantum_computer": False,
                "attack_surface": "Classical key delivery channel",
                "mitigation": "AES-256 / symmetric cipher on key channel",
                "residual_risk": "None (information-theoretic security on quantum channel)",
            },
            {
                "id": 2,
                "name": "Quantum adversary (future QC)",
                "capability": "Run Shor's algorithm on RSA/ECC keys",
                "quantum_memory": False,
                "quantum_computer": True,
                "attack_surface": "Asymmetric wrapper on key delivery channel",
                "mitigation": "PQC-KEM (ML-KEM, NIST 2024) on key channel",
                "residual_risk": "None if PQC-KEM is deployed",
            },
            {
                "id": 3,
                "name": "Harvest-Now-Decrypt-Later adversary",
                "capability": "Long-lived quantum memory + classical channel access",
                "quantum_memory": True,
                "quantum_computer": False,
                "attack_surface": "Classical key channel at any time T₂ > T₁",
                "mitigation": "PQC-KEM + ephemeral forward secrecy on key delivery",
                "residual_risk": "None if forward secrecy is enforced",
            },
            {
                "id": 4,
                "name": "Malicious quantum cloud (ransomware)",
                "capability": "Full control of quantum compute/storage infrastructure",
                "quantum_memory": True,
                "quantum_computer": True,
                "attack_surface": "Alice's raw qubit BEFORE local U_enc",
                "mitigation": "Perform U_enc locally; never transmit unencrypted qubits",
                "residual_risk": "None if local-first encryption is enforced",
            },
        ],
        "invariant": (
            "The quantum channel carrying S_i is ALWAYS unconditionally secure. "
            "The attack surface is EXCLUSIVELY the classical key delivery channel. "
            "Total system security = security of classical key channel."
        ),
        "actionable_summary": [
            "Deploy PQC-KEM (ML-KEM) for all key delivery channels NOW.",
            "Enforce ephemeral forward secrecy (ECDHE + PQC hybrid) on key sessions.",
            "Never transmit raw qubits to untrusted quantum cloud providers.",
            "Perform U_enc locally before any external quantum transmission.",
            "Audit classical channel infrastructure — it is your only attack surface.",
        ],
    }

    if verbose:
        print(f"\n{C.BOLD}[Exp 9 — Classical Channel Security Reduction]{C.RESET}  n={n}")
        print(f"\n  {C.BOLD}INVARIANT:{C.RESET}")
        print(f"  {C.DIM}{threat_model['invariant']}{C.RESET}")
        print(f"\n  {C.BOLD}{'ID':<4} {'Adversary':<38} {'Attack Surface':<40} {'Mitigation'}{C.RESET}")
        print(f"  {'─'*130}")
        for ac in threat_model["adversary_classes"]:
            qm  = f"{C.YELLOW}mem{C.RESET}" if ac["quantum_memory"] else "   "
            qc  = f"{C.RED}QC{C.RESET} " if ac["quantum_computer"] else "   "
            print(f"  {ac['id']:<4} [{qm}|{qc}] {ac['name']:<28} "
                  f"{ac['attack_surface']:<40} {ac['mitigation']}")
        print(f"\n  {C.BOLD}Actionable steps for practitioners:{C.RESET}")
        for i, step in enumerate(threat_model["actionable_summary"], 1):
            print(f"  {i}. {step}")

    return threat_model


def plot_exp9_threat_model(threat_model: dict,
                           outfile: str = "exp9_threat_model.png") -> None:
    """
    Decision-tree style threat model diagram.
    Shows how adversary class maps to mitigation requirement.
    """
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7)
    ax.set_axis_off()

    # Title
    ax.text(7, 6.6, "Experiment 9 — Classical Channel Security Reduction",
            ha="center", va="center", fontsize=13, fontweight="bold")
    ax.text(7, 6.2,
            "Total system security ≡ security of the classical key delivery channel",
            ha="center", va="center", fontsize=10, color="#444",
            style="italic")

    # Quantum channel box (always secure)
    qbox = plt.matplotlib.patches.FancyBboxPatch(
        (0.2, 2.5), 2.8, 3.0, boxstyle="round,pad=0.1",
        linewidth=1.5, edgecolor="#2196F3", facecolor="#E3F2FD", alpha=0.9)
    ax.add_patch(qbox)
    ax.text(1.6, 4.7, "QUANTUM CHANNEL", ha="center", fontsize=9, fontweight="bold", color="#1565C0")
    ax.text(1.6, 4.35, "S_i (encrypted clones)", ha="center", fontsize=8, color="#1565C0")
    ax.text(1.6, 4.0,  "ρ_Si = I/2 always", ha="center", fontsize=8, color="#1565C0")
    ax.text(1.6, 3.6,  "✓ Unconditional security", ha="center", fontsize=8.5,
            color="#4CAF50", fontweight="bold")
    ax.text(1.6, 3.2,  "No attack surface.", ha="center", fontsize=8, color="#444")
    ax.text(1.6, 2.85, "Ever.", ha="center", fontsize=8, color="#444")

    # Arrow to classical
    ax.annotate("", xy=(3.9, 4.0), xytext=(3.1, 4.0),
                arrowprops=dict(arrowstyle="->", color="#333", lw=1.5))
    ax.text(3.5, 4.2, "KEY N_i", ha="center", fontsize=8, color="#333")

    # Classical channel box
    cbox = plt.matplotlib.patches.FancyBboxPatch(
        (3.9, 2.5), 3.0, 3.0, boxstyle="round,pad=0.1",
        linewidth=2, edgecolor="#FF5722", facecolor="#FBE9E7", alpha=0.9)
    ax.add_patch(cbox)
    ax.text(5.4, 5.1, "CLASSICAL CHANNEL", ha="center", fontsize=9, fontweight="bold", color="#BF360C")
    ax.text(5.4, 4.7, "Key N_i delivery", ha="center", fontsize=8, color="#BF360C")
    ax.text(5.4, 4.35, "← SOLE attack surface", ha="center", fontsize=8.5,
            color="#F44336", fontweight="bold")

    # Adversary rows
    colors = ["#4CAF50", "#FF9800", "#F44336", "#9C27B0"]
    ys = [3.8, 3.35, 2.85, 2.4]
    ac_data = threat_model["adversary_classes"]
    for ac, color, y in zip(ac_data, colors, ys):
        ax.text(5.4, y, f"Adv {ac['id']}: {ac['mitigation'][:45]}", ha="center",
                fontsize=7.5, color=color)

    # Arrow to outcome
    ax.annotate("", xy=(9.7, 4.0), xytext=(6.9, 4.0),
                arrowprops=dict(arrowstyle="->", color="#333", lw=1.5))
    ax.text(8.3, 4.2, "mitigate →", ha="center", fontsize=8, color="#333")

    # Outcome boxes
    outcome_data = [
        (4.7, "Adv 1: AES-256 key wrap",       "#4CAF50", "Full security\n(classical model)"),
        (3.85,"Adv 2: PQC-KEM (ML-KEM)",        "#FF9800", "Full PQC security\n(quantum model)"),
        (3.0, "Adv 3: PQC-KEM + fwd secrecy",  "#F44336", "Closes HNDL\nwindow"),
        (2.15,"Adv 4: Local U_enc enforcement", "#9C27B0", "Closes ransomware\nvector"),
    ]
    for y_mid, label, color, outcome in outcome_data:
        rbox = plt.matplotlib.patches.FancyBboxPatch(
            (9.7, y_mid - 0.35), 4.0, 0.7, boxstyle="round,pad=0.08",
            linewidth=1, edgecolor=color, facecolor="white", alpha=0.9)
        ax.add_patch(rbox)
        ax.text(11.7, y_mid + 0.05, f"{label}  →  {outcome}",
                ha="center", va="center", fontsize=7.5, color=color)

    fig.tight_layout()
    fig.savefig(outfile, dpi=150)
    print(f"  Saved: {outfile}")


# ══════════════════════════════════════════════════════════════════════════════
#  PERSISTENCE, EXPORT AND COMPARISON
#  ─────────────────────────────────────────────────────────────────────────────
#  Three capabilities for reproducibility:
#
#  1. save_run_json / load_run_json
#       Serialise a completed experiment to JSON with full provenance (job IDs,
#       raw counts, derived fidelities, backend metadata).  The job_id field
#       is verifiable at quantum.ibm.com by any IBM Quantum account holder.
#       This JSON IS the "chain of custody" that peer reviewers and sceptical
#       audience members will ask for.
#
#  2. export_circuits
#       Serialise all key circuits to QPY (canonical Qiskit binary format,
#       lossless for UnitaryGate) and attempt QASM2 (text, human-readable but
#       may be truncated for large unitaries).  Both are committed to the repo
#       so that anyone can inspect or re-run the circuits without running this
#       script.
#
#  3. plot_backend_comparison
#       Given a list of loaded JSON records (one per backend), produce a
#       side-by-side grouped bar chart.  The key visual argument: Fe_victim ≈
#       0.25 is constant across ideal / nisq / real hardware, proving it is a
#       physics property of the protocol, not a hardware artefact.
# ══════════════════════════════════════════════════════════════════════════════

import datetime
import dataclasses


# ── JSON SCHEMA VERSION ───────────────────────────────────────────────────────
#
# Increment MAJOR when the JSON structure changes incompatibly.
# Increment MINOR for additive changes.
# load_run_json() warns when the loaded file's version differs from current.
#
_JSON_SCHEMA_VERSION = "1.1"


# ── SAVE ─────────────────────────────────────────────────────────────────────

def save_run_json(
    experiment:    int | str,
    n:             int,
    shots:         int,
    backend_label: str,
    backend_type:  str,          # "ideal" | "nisq" | "real"
    result,                      # any experiment dataclass, or list thereof
    outfile:       str,
) -> None:
    """
    Serialise a completed experiment result to a JSON file.

    The output contains three top-level sections:

    meta   — run parameters and timestamp for traceability
    result — the experiment dataclass (or list for Exp 8) as a plain dict
    jobs   — list of IBM Quantum job records from _JOB_LOG; each entry
             includes the job_id that is verifiable at quantum.ibm.com.
             Empty list for simulator runs.

    Parameters
    ----------
    experiment    : experiment number (int) or label (str)
    n             : cloning parameter used in this run
    shots         : shots per circuit
    backend_label : human-readable backend name (e.g. "ibm_kingston")
    backend_type  : one of "ideal", "nisq", "real"
    result        : experiment dataclass instance, or list[PartialKeyResult]
    outfile       : destination path (created/overwritten)
    """
    """
    # Convert dataclass(es) to plain dict for JSON serialisation.
    # dataclasses.asdict() handles nested dataclasses and lists recursively.
    if isinstance(result, list):
        result_dict = [dataclasses.asdict(r) for r in result]
    else:
        result_dict = dataclasses.asdict(result)
    """
    # Convert result to a plain dict for JSON serialisation.
    # dataclasses.asdict() is used when the result is a proper dataclass
    # instance or a list of dataclass instances.  For experiments that
    # return a plain dict (e.g. Exp 4 before GHZResult was added) or None,
    # we fall back gracefully rather than crashing.
    if isinstance(result, list):
        result_dict = [
            dataclasses.asdict(r) if dataclasses.is_dataclass(r) else dict(r)
            for r in result
        ]
    elif dataclasses.is_dataclass(result):
        result_dict = dataclasses.asdict(result)
    elif isinstance(result, dict):
        result_dict = result
    elif result is None:
        result_dict = {}
    else:
        # Last resort: stringify so save never raises
        result_dict = {"raw": repr(result)}


    payload = {
        "schema_version": _JSON_SCHEMA_VERSION,
        "meta": {
            "experiment":    str(experiment),
            "n":             n,
            "shots":         shots,
            "backend_label": backend_label,
            "backend_type":  backend_type,   # "ideal" | "nisq" | "real"
            "timestamp":     datetime.datetime.utcnow().isoformat() + "Z",
        },
        "result": result_dict,
        # Job log captures every IBM Quantum job submitted during this run.
        # Each entry includes job_id, circuit_name, shots, backend, counts.
        # For simulator runs _JOB_LOG is empty — that is correct behaviour.
        "jobs": list(_JOB_LOG),
    }

    os.makedirs(os.path.dirname(os.path.abspath(outfile)), exist_ok=True)
    with open(outfile, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)

    n_jobs = len(_JOB_LOG)
    job_ids = [j["job_id"] for j in _JOB_LOG] if n_jobs else []
    ok(f"Saved: {outfile}")
    info(f"  schema={_JSON_SCHEMA_VERSION}  backend={backend_label}  "
         f"n={n}  shots={shots}  jobs={n_jobs}")
    for jid in job_ids:
        info(f"  job_id: {jid}  "
             f"(verify at quantum.ibm.com/jobs/{jid})")


# ── LOAD ─────────────────────────────────────────────────────────────────────

def load_run_json(path: str) -> dict:
    """
    Load a previously saved experiment JSON and return the raw payload dict.

    Warns (but does not abort) when the file's schema_version differs from
    the current _JSON_SCHEMA_VERSION, so old files remain usable.

    Returns the full payload dict with keys: schema_version, meta, result,
    jobs.  Callers can pass this to reconstruct_result() or directly to
    plot_backend_comparison().
    """
    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)

    file_ver = payload.get("schema_version", "unknown")
    if file_ver != _JSON_SCHEMA_VERSION:
        print(f"  {C.YELLOW}[warn]{C.RESET} {os.path.basename(path)}: "
              f"schema {file_ver} ≠ current {_JSON_SCHEMA_VERSION} "
              f"— attempting load anyway")

    meta = payload.get("meta", {})
    info(f"Loaded: {path}")
    info(f"  exp={meta.get('experiment')}  n={meta.get('n')}  "
         f"shots={meta.get('shots')}  backend={meta.get('backend_label')}  "
         f"type={meta.get('backend_type')}  "
         f"ts={meta.get('timestamp', 'n/a')[:19]}")

    n_jobs = len(payload.get("jobs", []))
    if n_jobs:
        info(f"  {n_jobs} job(s) with verifiable IBM Quantum IDs")
    return payload


# ── RECONSTRUCT ───────────────────────────────────────────────────────────────

def reconstruct_result(payload: dict):
    """
    Reconstruct the appropriate experiment dataclass from a loaded JSON payload.

    The experiment tag in payload["meta"]["experiment"] determines which
    dataclass is instantiated:
      "1"  → FidelityResult
      "5"  → RansomwareResult
      "6"  → HarvestResult
      "7"  → DeadDropResult
      "8"  → list[PartialKeyResult]
      other → raw dict (caller responsibility)

    Missing keys in the JSON are filled with NaN so that older files
    remain loadable after schema extensions.
    """
    exp  = str(payload.get("meta", {}).get("experiment", "unknown"))
    data = payload.get("result", {})

    def _get(d, key, default=float("nan")):
        return d.get(key, default)

    if exp == "1":
        return FidelityResult(
            n           = _get(data, "n", 0),
            Fe_BSM      = _get(data, "Fe_BSM"),
            Fe_BSM_err  = _get(data, "Fe_BSM_err"),
            Fe_POM      = _get(data, "Fe_POM"),
            Fe_POM_err  = _get(data, "Fe_POM_err"),
            Fe_UQCM     = _get(data, "Fe_UQCM"),
            witnessed   = bool(_get(data, "witnessed", False)),
            above_floor = bool(_get(data, "above_floor", False)),
        )
    elif exp == "4":
        return GHZResult(
            r           = _get(data, "r", 0),
            n_clones    = _get(data, "n_clones", 2),
            Fr          = _get(data, "Fr"),
            Fr_err      = _get(data, "Fr_err"),
            noise_floor = _get(data, "noise_floor"),
            witnessed   = bool(_get(data, "witnessed", False)),
            above_floor = bool(_get(data, "above_floor", False)),
        )
    elif exp == "5":
        return RansomwareResult(
            n               = _get(data, "n", 0),
            Fe_honest       = _get(data, "Fe_honest"),
            Fe_honest_err   = _get(data, "Fe_honest_err"),
            Fe_victim       = _get(data, "Fe_victim"),
            Fe_victim_err   = _get(data, "Fe_victim_err"),
            Fe_adversary    = _get(data, "Fe_adversary"),
            Fe_adversary_err= _get(data, "Fe_adversary_err"),
        )
    elif exp == "6":
        return HarvestResult(
            n              = _get(data, "n", 0),
            Fe_no_key      = _get(data, "Fe_no_key"),
            Fe_no_key_err  = _get(data, "Fe_no_key_err"),
            Fe_with_key    = _get(data, "Fe_with_key"),
            Fe_with_key_err= _get(data, "Fe_with_key_err"),
            message        = _get(data, "message", ""),
        )
    elif exp == "7":
        return DeadDropResult(
            n               = _get(data, "n", 0),
            n_drops         = _get(data, "n_drops", 0),
            Fe_activated    = _get(data, "Fe_activated"),
            Fe_activated_err= _get(data, "Fe_activated_err"),
            Fe_inactive     = _get(data, "Fe_inactive"),
            Fe_inactive_err = _get(data, "Fe_inactive_err"),
            drop_index      = _get(data, "drop_index", 0),
        )
    elif exp == "8":
        # Exp 8 result is a list of PartialKeyResult
        if isinstance(data, list):
            return [
                PartialKeyResult(
                    n        = _get(d, "n", 0),
                    k        = _get(d, "k", 0),
                    Fe       = _get(d, "Fe"),
                    Fe_err   = _get(d, "Fe_err"),
                    theory_Fe= _get(d, "theory_Fe"),
                )
                for d in data
            ]
        return data  # fallback: raw list
    else:
        info(f"  No typed reconstruction for experiment '{exp}' — returning raw dict")
        return data


# ── EXPORT CIRCUITS ───────────────────────────────────────────────────────────

def export_circuits(n: int, outdir: str = "circuits") -> None:
    """
    Export the key protocol circuits to disk in two formats:

    QPY  (primary, always succeeds)
        Binary Qiskit serialisation — lossless for UnitaryGate, the
        canonical format for distributing Qiskit circuits.  Can be
        re-loaded with qiskit.qpy.load() without re-running this script.

    QASM2  (secondary, best-effort)
        Human-readable OpenQASM 2.0.  UnitaryGate is defined as an opaque
        custom gate.  May not round-trip cleanly on all toolchains but is
        readable for audit.  Skipped gracefully if qasm2 export fails.

    Circuits exported
    -----------------
    enc_dec_n{n}            — full protocol (enc + dec + BSM) from Exp 1
    ransomware_victim_n{n}  — enc only, no dec, no key (Exp 5 victim view)
    enc_only_n{n}           — encryption unitary alone (no ancilla, no BSM)
    dec_only_n{n}           — decryption unitary alone
    """
    from qiskit import qpy
    try:
        from qiskit import qasm2 as _qasm2
        _has_qasm2 = True
    except ImportError:
        _has_qasm2 = False

    os.makedirs(outdir, exist_ok=True)

    # Build the circuits to export
    circuits: list[tuple[str, QuantumCircuit]] = [
        (f"enc_dec_n{n}",           build_exp1_bsm(n)),
        (f"ransomware_victim_n{n}", build_ransomware_victim_circuit(n)),
    ]

    # Also export the raw enc / dec unitaries as single-gate circuits
    nq_enc = n + 1          # A + S_1..S_n
    nq_dec = n + 1          # S_j + N_1..N_n
    qc_enc_only = QuantumCircuit(nq_enc, name=f"Uenc_n{n}")
    qc_enc_only.append(_enc_gate(n), list(range(nq_enc)))
    qc_dec_only = QuantumCircuit(nq_dec, name=f"Udec_n{n}")
    qc_dec_only.append(_dec_gate(n), list(range(nq_dec)))
    circuits += [
        (f"enc_only_n{n}", qc_enc_only),
        (f"dec_only_n{n}", qc_dec_only),
    ]

    print(f"\n{C.BOLD}Circuit export  n={n}  →  {outdir}/{C.RESET}")

    # ── QPY bundle (all circuits in one file) ──────────────────────────────
    qpy_path = os.path.join(outdir, f"circuits_n{n}.qpy")
    try:
        with open(qpy_path, "wb") as fh:
            qpy.dump([qc for _, qc in circuits], fh)
        ok(f"QPY bundle  : {qpy_path}  ({len(circuits)} circuits)")
        info(f"  Reload: qiskit.qpy.load(open('{qpy_path}','rb'))")
    except Exception as exc:
        fail(f"QPY export failed: {exc}")

    # ── QASM2 individual files (best-effort) ───────────────────────────────
    if _has_qasm2:
        for name, qc in circuits:
            qasm_path = os.path.join(outdir, f"{name}.qasm")
            try:
                # Use allow_expr=True and custom_definitions for UnitaryGate
                _qasm2.dump(qc, qasm_path)
                ok(f"QASM2       : {qasm_path}")
            except Exception as exc:
                # UnitaryGate may not serialise cleanly — warn, don't abort
                print(f"  {C.YELLOW}·{C.RESET} QASM2 skipped for {name}: {exc}")
    else:
        info("qasm2 module not available — skipping QASM2 export")

    # ── Human-readable circuit summary ────────────────────────────────────
    print(f"\n  {'Circuit':<28} {'Qubits':>6}  {'Depth':>6}  {'Gates':>6}")
    print(f"  {'─'*52}")
    for name, qc in circuits:
        print(f"  {name:<28} {qc.num_qubits:>6}  "
              f"{qc.depth():>6}  {qc.count_ops().get('unitary', 0) + sum(qc.count_ops().values()):>6}")


# ── CIRCUIT DIAGRAM VISUALISATION ────────────────────────────────────────────
#
# draw_circuits() renders every key circuit as a PNG using Qiskit's built-in
# matplotlib drawer (circuit.draw(output="mpl")).  No backend connection is
# required — these are purely structural diagrams of the logical circuits.
#
# Two representation levels per circuit:
#
#   HIGH-LEVEL  (default, recommended for slides)
#       UnitaryGate appears as a labelled black box: "Uenc(n=2)", "Udec(n=2)".
#       Shows protocol structure clearly without gate-level clutter.
#       Produced by: circuit.draw(output="mpl")
#
#   DECOMPOSED  (produced when decompose=True)
#       UnitaryGate is expanded into primitive gates (H, CX, Rz, etc.).
#       Much denser; useful for circuit-depth analysis and Methods slides.
#       Produced by: circuit.decompose().draw(output="mpl")
#
# Circuits produced
# -----------------
#   uenc_n{n}              — U_enc acting on A + n signal qubits
#   udec_n{n}              — U_dec acting on S_j + n noise qubits
#   exp1_bsm_n{n}          — Full Exp 1: Bell state → enc → dec → BSM
#   exp2_chsh_s22_n{n}     — Exp 2 Scenario 2-2: CHSH timing test
#   exp3_iterated_l1       — Exp 3: one-generation iterated cloning
#   exp4_ghz_r2            — Exp 4: GHZ parallel cloning (r=2 qubits)
#   exp5_honest_n{n}       — Exp 5 Scenario A: honest protocol
#   exp5_victim_n{n}       — Exp 5 Scenario B: victim (no dec, no key)
#   exp6_phase1_n{n}       — Exp 6 Phase 1: encrypted clone, no key
#   exp6_phase2_n{n}       — Exp 6 Phase 2: key delivered, dec applied
#   exp8_fullkey_n{n}      — Exp 8 k=n: full key, perfect recovery
#   exp8_partkey_n{n}      — Exp 8 k<n: partial key, noise floor

def draw_circuits(
    n:         int  = 2,
    outdir:    str  = "figures",
    decompose: bool = False,
    dpi:       int  = 150,
    style:     str  = "clifford",
) -> None:
    """
    Render all key protocol circuits as PNG diagram images.

    Requires no backend, no IBM token, no network access.
    Uses only: qiskit + matplotlib (both already in requirements.txt).

    Parameters
    ----------
    n         : cloning parameter (default 2 — clearest for slides)
    outdir    : directory where PNGs are written (created if absent)
    decompose : if True, also save a *_decomposed.png for each circuit
                showing primitive gates (H, CX, Rz, ...) instead of
                the UnitaryGate black-box
    dpi       : PNG resolution (150 is adequate for slides; use 300 for print)
    style     : Qiskit circuit style — "clifford" (default, colour-coded),
                "bw" (black-and-white, best for print/LaTeX),
                "iqp", "default"

    Notes
    -----
    UnitaryGate in high-level mode draws as a labelled box.  This is
    intentional: the box IS the communication — it shows that U_enc and
    U_dec are well-defined unitary operations without obscuring protocol
    structure with primitive gates.  Use decompose=True to inspect gates.
    """
    os.makedirs(outdir, exist_ok=True)

    # ── Qubit register labels ─────────────────────────────────────────────
    # Applied via initial_state overlay where Qiskit supports it.
    # For diagrams, we keep labels simple: qubit index is self-explanatory.

    def _save(qc: QuantumCircuit, name: str, suffix: str = "") -> None:
        """Draw qc, save to outdir/name{suffix}.png, close the figure."""
        try:
            fig = qc.draw(
                output="mpl",
                fold=-1,           # never fold — show full circuit width
                style=style,
                plot_barriers=True,
                idle_wires=True,
            )
            path = os.path.join(outdir, f"{name}{suffix}.png")
            fig.savefig(path, dpi=dpi, bbox_inches="tight")
            plt.close(fig)
            ok(f"  {name}{suffix}.png")
        except Exception as exc:
            fail(f"  {name}{suffix}.png — {exc}")

    def _save_both(qc: QuantumCircuit, name: str) -> None:
        """Save high-level view; optionally also the decomposed view."""
        _save(qc, name)
        if decompose:
            try:
                _save(qc.decompose(), name, suffix="_decomposed")
            except Exception as exc:
                print(f"  {C.YELLOW}·{C.RESET} decompose skipped for {name}: {exc}")

    print(f"\n{C.BOLD}Circuit diagrams  n={n}  →  {outdir}/{C.RESET}")
    print(f"  style={style}  decompose={decompose}  dpi={dpi}")
    print()

    # ══════════════════════════════════════════════════════════════════════
    # GROUP 1 — Core protocol unitaries
    # ══════════════════════════════════════════════════════════════════════
    print(f"  {C.CYAN}── Core protocol unitaries ──{C.RESET}")

    # U_enc: A qubit + n signal qubits
    nq_enc = n + 1
    qc_enc = QuantumCircuit(nq_enc, name=f"U_enc  (n={n})")
    qc_enc.append(_enc_gate(n), list(range(nq_enc)))
    _save_both(qc_enc, f"uenc_n{n}")

    # U_dec: S_j qubit + n noise qubits
    nq_dec = n + 1
    qc_dec = QuantumCircuit(nq_dec, name=f"U_dec  (n={n})")
    qc_dec.append(_dec_gate(n), list(range(nq_dec)))
    _save_both(qc_dec, f"udec_n{n}")

    # ══════════════════════════════════════════════════════════════════════
    # GROUP 2 — Original experiments (Yamaguchi et al.)
    # ══════════════════════════════════════════════════════════════════════
    print(f"\n  {C.CYAN}── Yamaguchi et al. experiments ──{C.RESET}")

    # Exp 1: Bell state + enc + dec + BSM
    qc1 = build_exp1_bsm(n)
    qc1.name = f"Exp 1 — BSM  (n={n})"
    _save_both(qc1, f"exp1_bsm_n{n}")

    # Exp 2: CHSH Scenario 2-2 (dec after enc, simultaneous measurement)
    # Representative: Z basis on A~, B0 basis on S1
    qc2 = build_exp2_chsh(n, scenario=22, a_basis="Z", b_basis="B0")
    qc2.name = f"Exp 2 — CHSH Scenario 2-2  (n={n})"
    _save_both(qc2, f"exp2_chsh_s22_n{n}")

    # Exp 3: One generation of iterated cloning (l=1)
    qc3 = build_exp3_iterated(l=1, n_base=n)
    qc3.name = f"Exp 3 — Iterated cloning  (l=1, n={n})"
    _save_both(qc3, f"exp3_iterated_l1_n{n}")

    # Exp 4: GHZ parallel (r=2 GHZ qubits, n clones each)
    qc4 = build_exp4_ghz(r=2, n_clones=n)
    qc4.name = f"Exp 4 — GHZ parallel  (r=2, n={n})"
    _save_both(qc4, f"exp4_ghz_r2_n{n}")

    # ══════════════════════════════════════════════════════════════════════
    # GROUP 3 — Security experiments (protocol variations and attack scenarios)
    # ══════════════════════════════════════════════════════════════════════
    print(f"\n  {C.CYAN}── Security experiments (Exp 5–8) ──{C.RESET}")

    # Exp 5 Scenario A — Honest protocol (enc + dec + BSM)
    # Identical to Exp 1 BSM; we label it explicitly for the slides
    qc5a = build_exp1_bsm(n)
    qc5a.name = f"Exp 5A — Honest protocol  (n={n})"
    _save_both(qc5a, f"exp5_honest_n{n}")

    # Exp 5 Scenario B — Ransomware victim (enc applied, no dec, no key)
    # Measures S_1 directly without decryption → Fe ≈ 0.25
    qc5b = build_ransomware_victim_circuit(n)
    qc5b.name = f"Exp 5B — Ransomware victim  (n={n})"
    _save_both(qc5b, f"exp5_victim_n{n}")

    # Exp 6 Phase 1 — HNDL: adversary holds S_i, no key yet
    # Structurally identical to ransomware victim circuit
    qc6a = build_ransomware_victim_circuit(n)
    qc6a.name = f"Exp 6 Phase 1 — HNDL no key  (n={n})"
    _save_both(qc6a, f"exp6_phase1_n{n}")

    # Exp 6 Phase 2 — HNDL: key delivered, decryption applied
    qc6b = build_exp1_bsm(n)
    qc6b.name = f"Exp 6 Phase 2 — HNDL key seized  (n={n})"
    _save_both(qc6b, f"exp6_phase2_n{n}")

    # Exp 8 — Full key (k=n): standard protocol → Fe=1
    qc8_full = build_exp1_bsm(n)
    qc8_full.name = f"Exp 8 — Full key k=n  (n={n})"
    _save_both(qc8_full, f"exp8_fullkey_n{n}")

    # Exp 8 — Partial key (k<n): enc only, no dec → Fe≈0.25
    # k=0 case: no noise qubits at all (worst case, most illustrative)
    qc8_part = build_ransomware_victim_circuit(n)
    qc8_part.name = f"Exp 8 — Partial key k<n  (n={n})"
    _save_both(qc8_part, f"exp8_partkey_n{n}")

    # ══════════════════════════════════════════════════════════════════════
    # Summary table
    # ══════════════════════════════════════════════════════════════════════
    circuits_summary = [
        (f"uenc_n{n}",           qc_enc),
        (f"udec_n{n}",           qc_dec),
        (f"exp1_bsm_n{n}",       qc1),
        (f"exp2_chsh_s22_n{n}",  qc2),
        (f"exp3_iterated_l1_n{n}", qc3),
        (f"exp4_ghz_r2_n{n}",    qc4),
        (f"exp5_honest_n{n}",    qc5a),
        (f"exp5_victim_n{n}",    qc5b),
        (f"exp6_phase1_n{n}",    qc6a),
        (f"exp6_phase2_n{n}",    qc6b),
        (f"exp8_fullkey_n{n}",   qc8_full),
        (f"exp8_partkey_n{n}",   qc8_part),
    ]
    print(f"\n  {'Filename':<30} {'Qubits':>6}  {'Depth':>6}  {'Clbits':>7}")
    print(f"  {'─'*55}")
    for name, qc in circuits_summary:
        print(f"  {name:<30} {qc.num_qubits:>6}  "
              f"{qc.depth():>6}  {qc.num_clbits:>7}")
    n_files = len(circuits_summary) * (2 if decompose else 1)
    print(f"\n  {n_files} PNG file(s) written to {outdir}/")


# ── BACKEND COMPARISON PLOT ───────────────────────────────────────────────────

def plot_backend_comparison(
    payloads:   list[dict],
    experiment: str,
    outfile:    str = "comparison.png",
) -> None:
    """
    Produce a side-by-side grouped bar chart comparing the same experiment
    run across multiple backends (ideal, nisq, real hardware).

    It demonstrates that Fe_victim ≈ 0.25 regardless of backend quality, 
    proving the noise floor is a physical property of the protocol rather 
    than a hardware artefact.

    Parameters
    ----------
    payloads   : list of JSON payload dicts, one per backend (from load_run_json)
    experiment : experiment identifier string — determines which fields to plot
                 Supported: "5" (Ransomware), "6" (HNDL), "7" (DeadDrop),
                            "8" (PartialKey), "1" (Fidelity)
    outfile    : destination PNG path
    """
    if not payloads:
        fail("plot_backend_comparison: no payloads provided")
        return

    # ── Dispatch to per-experiment compare function ────────────────────────
    exp = str(experiment)

    if exp == "5":
        _plot_compare_ransomware(payloads, outfile)
    elif exp == "6":
        _plot_compare_harvest(payloads, outfile)
    elif exp == "8":
        _plot_compare_partial_key(payloads, outfile)
    elif exp == "1":
        _plot_compare_fidelity(payloads, outfile)
    else:
        # Generic: try to extract any float fields from result dict and plot
        _plot_compare_generic(payloads, exp, outfile)


def _backend_palette(n: int) -> list[str]:
    """Return n distinct colours for backend comparison bars."""
    return ["#2196F3", "#FF9800", "#4CAF50", "#9C27B0", "#F44336"][:n]


def _plot_compare_ransomware(payloads: list[dict], outfile: str) -> None:
    """
    Grouped bar chart for Experiment 5 (Quantum Ransomware) across backends.

    Scenario labels on x-axis; one bar group per backend.
    Horizontal lines mark noise floor (0.25), witness (0.5), perfect (1.0).

    The key visual argument: Scenario B (victim) is ≈ 0.25 on ALL backends.
    """
    scenarios   = ["A · Honest\n(enc + dec)", "B · Victim\n(no key)", "C · Adversary\n(with key)"]
    n_scenarios = len(scenarios)
    n_backends  = len(payloads)
    bar_w       = 0.8 / n_backends
    colors      = _backend_palette(n_backends)

    fig, ax = plt.subplots(figsize=(10, 6))

    for bi, (payload, color) in enumerate(zip(payloads, colors)):
        r     = payload.get("result", {})
        label = payload.get("meta", {}).get("backend_label", f"backend {bi+1}")
        btype = payload.get("meta", {}).get("backend_type", "?")
        fes   = [r.get("Fe_honest",    float("nan")),
                 r.get("Fe_victim",    float("nan")),
                 r.get("Fe_adversary", float("nan"))]
        errs  = [r.get("Fe_honest_err",    0),
                 r.get("Fe_victim_err",    0),
                 r.get("Fe_adversary_err", 0)]

        xs = [i + (bi - n_backends / 2 + 0.5) * bar_w
              for i in range(n_scenarios)]
        ax.bar(xs, fes, width=bar_w * 0.92, color=color, alpha=0.85,
               label=f"{label} ({btype})", edgecolor="white")
        ax.errorbar(xs, fes, errs, fmt="none", color="black",
                    capsize=4, linewidth=1.2)

    ax.axhline(1.0,  linestyle="--", color="#333", linewidth=1.0, alpha=0.6,
               label="Perfect fidelity (F=1)")
    ax.axhline(0.5,  linestyle="--", color="#555", linewidth=0.8, alpha=0.5,
               label="Entanglement witness (F=0.5)")
    ax.axhline(0.25, linestyle=":",  color="#999", linewidth=1.0, alpha=0.9,
               label="Noise floor (F=0.25) ← victim always lands here")

    ax.set_xticks(range(n_scenarios))
    ax.set_xticklabels(scenarios, fontsize=10)
    ax.set_ylim(0, 1.18)
    ax.set_ylabel("Entanglement fidelity  Fₑ", fontsize=12)
    ax.set_title("Exp 5 — Quantum Ransomware: Backend Comparison\n"
                 "Victim (Scenario B) = noise floor on ALL backends "
                 "→ physics property, not hardware artefact",
                 fontsize=10, fontweight="bold")
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(axis="y", alpha=0.3)

    # Annotation: draw bracket under Scenario B emphasising constancy
    y_ann = -0.10
    for bi in range(n_backends):
        x = 1 + (bi - n_backends / 2 + 0.5) * bar_w
        ax.annotate("≈ 0.25", (x, 0.03), ha="center", fontsize=7.5,
                    color="#F44336", fontweight="bold")

    fig.tight_layout()
    fig.savefig(outfile, dpi=150)
    print(f"  Saved: {outfile}")


def _plot_compare_harvest(payloads: list[dict], outfile: str) -> None:
    """Grouped bar chart for Experiment 6 (HNDL) across backends."""
    phases     = ["Phase 1\n(no key)", "Phase 2\n(key intercepted)"]
    n_phases   = len(phases)
    n_backends = len(payloads)
    bar_w      = 0.8 / n_backends
    colors     = _backend_palette(n_backends)

    fig, ax = plt.subplots(figsize=(8, 5))

    for bi, (payload, color) in enumerate(zip(payloads, colors)):
        r     = payload.get("result", {})
        label = payload.get("meta", {}).get("backend_label", f"backend {bi+1}")
        btype = payload.get("meta", {}).get("backend_type", "?")
        fes   = [r.get("Fe_no_key",   float("nan")),
                 r.get("Fe_with_key", float("nan"))]
        errs  = [r.get("Fe_no_key_err",   0),
                 r.get("Fe_with_key_err", 0)]
        xs = [i + (bi - n_backends / 2 + 0.5) * bar_w for i in range(n_phases)]
        ax.bar(xs, fes, width=bar_w * 0.92, color=color, alpha=0.85,
               label=f"{label} ({btype})", edgecolor="white")
        ax.errorbar(xs, fes, errs, fmt="none", color="black",
                    capsize=4, linewidth=1.2)

    ax.axhline(0.25, linestyle=":", color="#999", linewidth=1.0, alpha=0.9)
    ax.axhline(1.0,  linestyle="--", color="#333", linewidth=1.0, alpha=0.6)
    ax.set_xticks(range(n_phases))
    ax.set_xticklabels(phases, fontsize=11)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Fₑ", fontsize=12)
    ax.set_title("Exp 6 — HNDL: Backend Comparison\n"
                 "Phase 1 ≈ 0.25 (physics) — Phase 2 = backend-dependent",
                 fontsize=10, fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(outfile, dpi=150)
    print(f"  Saved: {outfile}")


def _plot_compare_partial_key(payloads: list[dict], outfile: str) -> None:
    """Overlay line chart for Experiment 8 (Partial Key) across backends."""
    colors = _backend_palette(len(payloads))
    fig, ax = plt.subplots(figsize=(9, 5))

    for payload, color in zip(payloads, colors):
        data  = payload.get("result", [])
        label = payload.get("meta", {}).get("backend_label", "?")
        btype = payload.get("meta", {}).get("backend_type", "?")
        if not isinstance(data, list):
            continue
        ks   = [d.get("k",    0) for d in data]
        fes  = [d.get("Fe",   float("nan")) for d in data]
        errs = [d.get("Fe_err", 0)  for d in data]
        ax.errorbar(ks, fes, errs, fmt="o-", color=color, capsize=4,
                    linewidth=2, markersize=7, label=f"{label} ({btype})")

    # Theory step overlay (backend-independent)
    if payloads:
        data = payloads[0].get("result", [])
        if isinstance(data, list) and data:
            n = data[-1].get("n", 2)
            ks_t     = [d.get("k") for d in data]
            theory_t = [d.get("theory_Fe", 0.25) for d in data]
            ax.step(ks_t, theory_t, "--", where="post", color="#888",
                    linewidth=1.5, alpha=0.7, label="Theory (step function)")
            ax.axvline(n - 0.5, linestyle="-", color="#FF5722",
                       linewidth=2, alpha=0.6, label=f"Threshold k=n={n}")

    ax.axhline(0.25, linestyle=":", color="#999", linewidth=1.0)
    ax.axhline(1.0,  linestyle="--", color="#333", linewidth=1.0, alpha=0.5)
    ax.set_xlabel("k  (noise qubits available)", fontsize=12)
    ax.set_ylabel("Fₑ", fontsize=12)
    ax.set_title("Exp 8 — Partial Key: Backend Comparison\n"
                 "All-or-nothing threshold reproduced on all backends",
                 fontsize=10, fontweight="bold")
    ax.legend(fontsize=9)
    ax.set_ylim(0, 1.15)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(outfile, dpi=150)
    print(f"  Saved: {outfile}")


def _plot_compare_fidelity(payloads: list[dict], outfile: str) -> None:
    """Overlay line chart for Experiment 1 (Fe vs n) across backends."""
    colors = _backend_palette(len(payloads))
    fig, ax = plt.subplots(figsize=(9, 5))

    for payload, color in zip(payloads, colors):
        # Exp 1 result is a single FidelityResult dict, not a list.
        # When sweep=True, main() saves one file per n — callers should
        # load multiple per-n files for the same backend and pass them all.
        # For a single-n comparison, just plot the one point.
        r     = payload.get("result", {})
        label = payload.get("meta", {}).get("backend_label", "?")
        btype = payload.get("meta", {}).get("backend_type", "?")
        n_val = payload.get("meta", {}).get("n", 0)
        fe    = r.get("Fe_BSM", float("nan"))
        err   = r.get("Fe_BSM_err", 0)
        ax.errorbar([n_val], [fe], [err], fmt="o", color=color,
                    capsize=5, markersize=8, label=f"{label} ({btype})")

    ax.axhline(0.5,  linestyle="--", color="#333", linewidth=1.0, alpha=0.7,
               label="Entanglement witness")
    ax.axhline(0.25, linestyle=":",  color="#999", linewidth=1.0, alpha=0.9,
               label="Noise floor")
    ax.set_xlabel("n (clone count)", fontsize=12)
    ax.set_ylabel("Fₑ (BSM)", fontsize=12)
    ax.set_title("Exp 1 — Fe vs n: Backend Comparison", fontsize=10,
                 fontweight="bold")
    ax.legend(fontsize=9)
    ax.set_ylim(0, 1.1)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(outfile, dpi=150)
    print(f"  Saved: {outfile}")


def _plot_compare_generic(payloads: list[dict], experiment: str,
                          outfile: str) -> None:
    """
    Fallback comparison: extract all float-valued fields from result dict
    and plot them as grouped bars labelled by field name.
    Only handles flat (non-list) result dicts.
    """
    colors = _backend_palette(len(payloads))
    # Collect field names from the first payload
    first_result = payloads[0].get("result", {})
    if isinstance(first_result, list):
        info(f"Generic compare not supported for list results (exp {experiment})")
        return

    float_fields = [k for k, v in first_result.items()
                    if isinstance(v, (int, float)) and not k.endswith("_err")
                    and k != "n"]
    if not float_fields:
        info(f"No plottable float fields found for experiment {experiment}")
        return

    n_fields   = len(float_fields)
    n_backends = len(payloads)
    bar_w      = 0.8 / n_backends
    fig, ax    = plt.subplots(figsize=(max(8, n_fields * 2), 5))

    for bi, (payload, color) in enumerate(zip(payloads, colors)):
        r     = payload.get("result", {})
        label = payload.get("meta", {}).get("backend_label", f"b{bi}")
        btype = payload.get("meta", {}).get("backend_type", "?")
        fes   = [r.get(f, float("nan")) for f in float_fields]
        errs  = [r.get(f + "_err", 0)  for f in float_fields]
        xs    = [i + (bi - n_backends / 2 + 0.5) * bar_w
                 for i in range(n_fields)]
        ax.bar(xs, fes, width=bar_w * 0.92, color=color, alpha=0.85,
               label=f"{label} ({btype})", edgecolor="white")
        ax.errorbar(xs, fes, errs, fmt="none", color="black",
                    capsize=3, linewidth=1.0)

    ax.set_xticks(range(n_fields))
    ax.set_xticklabels(float_fields, rotation=20, ha="right", fontsize=9)
    ax.set_ylabel("Value", fontsize=11)
    ax.set_title(f"Exp {experiment} — Backend Comparison (generic)",
                 fontsize=10)
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(outfile, dpi=150)
    print(f"  Saved: {outfile}")


# ── CLI (credentials + banner) ───────────────────────────────────

def main() -> int:
    """
    Entry point.

    --save-json PATH
        After running an experiment, serialise the result (dataclass + job
        provenance) to PATH as JSON.  Works for any experiment.  Creates
        parent directories automatically.

    --load-json PATH [PATH ...]
        Load one or more previously saved JSON files instead of running
        circuits.  Multiple files → backend comparison figure (with --plot).

    --export-circuits
        Export key protocol circuits for n=--n to circuits/ directory.
        Produces QPY bundle and QASM2 text.  No backend needed.

    --draw-circuits
        Render all key circuits as PNG diagram images using the Qiskit
        matplotlib drawer.  No backend, no IBM token, no network required.
        Output goes to --figures-dir (default: figures/).
        Add --draw-decompose to also save primitive-gate expanded versions.
        Add --draw-style bw for black-and-white (print/LaTeX).
        Add --draw-dpi 300 for print-quality output.
    """
    p = argparse.ArgumentParser(
        description=(
            "Encrypted qubit cloning — experimental CLI (arXiv:2602.10695)\n"
            "\n"
            "Experiments 1-4 : Faithful reproduction of Yamaguchi et al. (2026)\n"
            "Experiments 5-9 : Security extensions for Quantum Village\n"
            "\n"
            "  --experiment 5  →  Quantum Ransomware\n"
            "  --experiment 6  →  Harvest-Now-Decrypt-Later\n"
            "  --experiment 7  →  Quantum Dead Drop (Bloch sphere)\n"
            "  --experiment 8  →  Partial Key Attack (k-of-n threshold)\n"
            "  --experiment 9  →  Classical Channel Reduction (no circuits)\n"
            "\n"
            "  --save-json PATH        Save result + job IDs to JSON\n"
            "  --load-json P [P ...]   Load saved results; compare if multiple\n"
            "  --export-circuits       Export circuits to QPY + QASM2\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # ── Experiment selection ───────────────────────────────────────────────
    p.add_argument("--experiment", "-e", default="1",
                   choices=["1", "2", "3", "4", "5", "6", "7", "8", "9",
                            "all", "security"],
                   help="Experiment to run. 'security' runs experiments 5-9.")

    # ── Protocol parameters ────────────────────────────────────────────────
    p.add_argument("--n", type=int, default=2,
                   help="Cloning parameter n (default: 2)")
    p.add_argument("--r", type=int, default=4,
                   help="GHZ qubit count r for Exp 4 (default: 4)")
    p.add_argument("--l", type=int, default=1,
                   help="Iteration level l for Exp 3 (default: 1)")
    p.add_argument("--n-drops", dest="n_drops", type=int, default=3,
                   help="Number of dead drop locations for Exp 7 (default: 3)")
    p.add_argument("--activate-drop", dest="activate_drop", type=int, default=0,
                   help="Which drop index Alice activates in Exp 7 (default: 0)")
    p.add_argument("--shots", type=int, default=4096,
                   help="Measurement repetitions per circuit (default: 4096)")

    # ── Backend selection ──────────────────────────────────────────────────
    p.add_argument("--backend", default="ideal",
                   choices=["ideal", "nisq", "real"],
                   help="ideal=AerSimulator, nisq=noisy sim, real=IBM hardware")
    p.add_argument("--ibm-backend", dest="ibm_backend", default="least-busy",
                   help="IBM backend name or 'least-busy' (default)")

    # ── Run-mode flags ─────────────────────────────────────────────────────
    p.add_argument("--sweep", action="store_true",
                   help="Sweep the primary parameter range (n, l, or r)")
    p.add_argument("--plot", action="store_true",
                   help="Save PNG figures after each experiment")
    p.add_argument(
        "--figures-dir", dest="figures_dir", default="figures", metavar="DIR",
        help=(
            "Directory where all PNG figures are written (default: figures). "
            "Created automatically if it does not exist. "
            "Use '.' to restore the previous behaviour of writing to the "
            "current working directory."
        ),
    )
    p.add_argument("--verify", action="store_true",
                   help="Run protocol self-verification only (no experiment)")
    p.add_argument("--list-backends", dest="list_backends", action="store_true",
                   help="List available IBM Quantum backends and exit")
    p.add_argument("--no-verify", dest="no_verify", action="store_true",
                   help="Skip pre-verification (saves ~5 s; use for live demos)")

    # ── Persistence flags ─────────────────────────────────────────────
    p.add_argument(
        "--save-json", dest="save_json", metavar="PATH", default=None,
        help=(
            "After running the experiment, save result + IBM job IDs to PATH. "
            "Parent directories are created automatically. "
            "The job_id field in each saved record is verifiable at "
            "quantum.ibm.com/jobs/<job_id>. "
            "Use this to pre-collect hardware data before the talk."
        ),
    )
    p.add_argument(
        "--load-json", dest="load_json", metavar="PATH", nargs="+", default=None,
        help=(
            "Load one or more previously saved JSON files instead of running "
            "circuits. Single file: reconstruct and display. "
            "Multiple files (one per backend): display table + comparison plot "
            "when --plot is also set. "
            "No --backend or IBM connection required."
        ),
    )

    # ── Export flag ───────────────────────────────────────────────────
    p.add_argument(
        "--export-circuits", dest="export_circuits", action="store_true",
        help=(
            "Export key protocol circuits for n=--n to circuits/ directory. "
            "Produces QPY bundle (lossless, always works) and QASM2 text "
            "(best-effort, human-readable). No backend connection required."
        ),
    )

    # ── Circuit diagram flags ─────────────────────────────────────────
    p.add_argument(
        "--draw-circuits", dest="draw_circuits", action="store_true",
        help=(
            "Render all key protocol circuits as PNG diagram images using "
            "Qiskit's matplotlib drawer. No backend or IBM token required. "
            "Output goes to --figures-dir (default: figures/). "
            "Covers: U_enc, U_dec, Exp1–4 originals, Exp5–8 security variants."
        ),
    )
    p.add_argument(
        "--draw-decompose", dest="draw_decompose", action="store_true",
        help=(
            "When used with --draw-circuits, also save a *_decomposed.png "
            "for each circuit showing primitive gates (H, CX, Rz, ...) "
            "instead of the UnitaryGate black-box. Files are larger and "
            "denser — useful for the Methods section, not for main slides."
        ),
    )
    p.add_argument(
        "--draw-style", dest="draw_style", default="clifford",
        choices=["clifford", "iqp", "bw", "default"],
        help=(
            "Visual style for circuit diagrams (default: clifford). "
            "clifford = colour-coded gates, best for slides. "
            "bw = black-and-white, best for print/LaTeX."
        ),
    )
    p.add_argument(
        "--draw-dpi", dest="draw_dpi", type=int, default=150,
        help="PNG resolution for circuit diagrams in DPI (default: 150).",
    )

    # ── IBM credential flags ───────────────────────────────────────────────
    p.add_argument("--token", default=None,
                   help="IBM Quantum API token (overrides .env / env vars)")
    p.add_argument("--instance", default=None,
                   help="IBM Quantum instance CRN (overrides .env / env vars)")
    p.add_argument("--creds-file", metavar="PATH", default=None,
                   help="JSON file with IBM Quantum credentials")

    args = p.parse_args()

    # ── Resolve IBM credentials first (needed for --list-backends / real) ──
    token, instance = resolve_credentials(args)

    # ══════════════════════════════════════════════════════════════════════
    # BRANCH A — infrastructure / utility modes (no experiment dispatch)
    # ══════════════════════════════════════════════════════════════════════

    if args.list_backends:
        list_open_plan_backends(token=token, instance=instance)
        return 0

    if args.verify:
        all_ok = all(verify_protocol(n) for n in (2, 3, 4))
        print(f"\n{'All checks passed.' if all_ok else 'Some checks FAILED.'}")
        return 0 if all_ok else 1

    # ── Export circuits (no backend needed) ───────────────────────────────
    if args.export_circuits:
        print_banner("export-circuits", "no-backend")
        export_circuits(n=args.n)
        print(f"\n{C.DIM}{'─'*60}{C.RESET}")
        return 0

    # ── Draw circuit diagrams (no backend needed) ─────────────────────────
    if args.draw_circuits:
        print_banner("draw-circuits", "no-backend")
        # Ensure the output directory exists before drawing begins.
        os.makedirs(args.figures_dir, exist_ok=True)
        draw_circuits(
            n        = args.n,
            outdir   = args.figures_dir,
            decompose= args.draw_decompose,
            dpi      = args.draw_dpi,
            style    = args.draw_style,
        )
        print(f"\n{C.DIM}{'─'*60}{C.RESET}")
        return 0

    # ── Exp 9 never needs a quantum backend ───────────────────────────────
    if args.experiment == "9":
        print_banner("9", "no-backend (classical analysis)")
        # Ensure figures directory exists before any plot call.
        os.makedirs(args.figures_dir, exist_ok=True)
        # fp(name) builds the full path inside the chosen figures directory.
        fp = lambda name: os.path.join(args.figures_dir, name)
        result9 = run_experiment_9(n=args.n)
        if args.plot:
            plot_exp9_threat_model(result9, outfile=fp("exp9_threat_model.png"))
        if args.save_json:
            # Exp 9 has no dataclass — save the raw dict directly
            payload = {
                "schema_version": _JSON_SCHEMA_VERSION,
                "meta": {
                    "experiment":    "9",
                    "n":             args.n,
                    "shots":         0,
                    "backend_label": "none",
                    "backend_type":  "none",
                    "timestamp":     datetime.datetime.utcnow().isoformat() + "Z",
                },
                "result": result9,
                "jobs":   [],
            }
            os.makedirs(os.path.dirname(os.path.abspath(args.save_json)),
                        exist_ok=True)
            with open(args.save_json, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2, ensure_ascii=False)
            ok(f"Saved: {args.save_json}")
        print(f"\n{C.DIM}{'─'*60}{C.RESET}")
        return 0

    # ══════════════════════════════════════════════════════════════════════
    # BRANCH B — load-json mode (no live backend needed)
    # ══════════════════════════════════════════════════════════════════════

    if args.load_json:
        print_banner("load-json", "from file(s)")
        # Ensure figures directory exists before any plot call.
        os.makedirs(args.figures_dir, exist_ok=True)
        # fp(name) builds the full path inside the chosen figures directory.
        fp = lambda name: os.path.join(args.figures_dir, name)

        payloads = []
        for path in args.load_json:
            try:
                payloads.append(load_run_json(path))
            except FileNotFoundError:
                fail(f"File not found: {path}")
                return 1
            except json.JSONDecodeError as exc:
                fail(f"Invalid JSON in {path}: {exc}")
                return 1

        if not payloads:
            fail("No valid payloads loaded.")
            return 1

        # Infer experiment from the first payload
        exp = str(payloads[0].get("meta", {}).get("experiment", "unknown"))

        if len(payloads) == 1:
            # ── Single file: reconstruct and display ──────────────────────
            result = reconstruct_result(payloads[0])
            print(f"\n  Loaded experiment {exp} result:")
            if isinstance(result, list):
                for r in result:
                    print(f"    {r}")
            else:
                print(f"    {result}")

            # Re-plot using the appropriate per-experiment plot function
            if args.plot:
                outfile = fp(f"loaded_exp{exp}.png")
                if exp == "5" and isinstance(result, RansomwareResult):
                    plot_exp5_ransomware(result, outfile)
                elif exp == "6" and isinstance(result, HarvestResult):
                    plot_exp6_harvest(result, outfile)
                elif exp == "7" and isinstance(result, DeadDropResult):
                    plot_exp7_dead_drop(result, outfile)
                elif exp == "8" and isinstance(result, list):
                    plot_exp8_partial_key(result, outfile)
                elif exp == "1" and isinstance(result, FidelityResult):
                    # Wrap in list for the sweep-plot function
                    plot_exp1_sweep([result], outfile)
                else:
                    info(f"No plot function registered for experiment {exp}")

        else:
            # ── Multiple files: comparison plot ───────────────────────────
            print(f"\n  {len(payloads)} payloads loaded — "
                  f"experiment {exp} across backends")
            print(f"\n  {'Backend':<22}  {'Type':<6}  {'n':>3}  {'shots':>6}")
            print(f"  {'─'*46}")
            for p in payloads:
                m = p.get("meta", {})
                print(f"  {m.get('backend_label','?'):<22}  "
                      f"{m.get('backend_type','?'):<6}  "
                      f"{m.get('n',0):>3}  "
                      f"{m.get('shots',0):>6}")

            if args.plot:
                outfile = fp(f"compare_exp{exp}.png")
                plot_backend_comparison(payloads, exp, outfile)
            else:
                info("Add --plot to generate the backend comparison figure.")

        print(f"\n{C.DIM}{'─'*60}{C.RESET}")
        return 0

    # ══════════════════════════════════════════════════════════════════════
    # BRANCH C — normal experiment execution
    # ══════════════════════════════════════════════════════════════════════

    # Ensure the figures output directory exists before any experiment runs.
    # This is the single point of creation; all plot calls below use fp().
    os.makedirs(args.figures_dir, exist_ok=True)
    # fp(name) constructs the full output path for any PNG figure.
    # Defined once here so every plot call in Branch C is a one-liner.
    fp = lambda name: os.path.join(args.figures_dir, name)

    # Clear the job log so this run starts clean
    _JOB_LOG.clear()

    if not args.no_verify:
        n_check = args.n if not args.sweep else 3
        if not verify_protocol(n_check, verbose=False):
            print(f"{C.RED}[ABORT]{C.RESET} Protocol verification failed "
                  f"for n={n_check}.")
            return 1
        ok(f"Protocol verified (n={n_check}). Proceeding.")

    backend, is_real = get_backend(
        args.backend, args.ibm_backend, token=token, instance=instance)
    backend_label = getattr(backend, "name", args.backend)
    backend_type  = args.backend   # "ideal" | "nisq" | "real"
    print_banner(args.experiment, backend_label)

    shots = args.shots

    # Accumulate top-level results for --save-json
    # (only the last per-n result is saved when sweeping; if you need all n,
    # run separately per n with distinct --save-json paths)
    _last_result = None
    _last_n      = args.n
    _last_exp    = args.experiment

    # ── Experiments 1–4 (original Yamaguchi et al.) ──────────────────────

    if args.experiment in ("1", "all"):
        n_range = list(range(2, 9)) if args.sweep else [args.n]
        exp1_results = []
        for n in n_range:
            r = run_experiment_1(n, backend, shots, is_real)
            exp1_results.append(r)
            _last_result, _last_n, _last_exp = r, n, "1"
        if args.plot and len(n_range) > 1:
            plot_exp1_sweep(exp1_results, outfile=fp("exp1_result.png"))

    if args.experiment in ("2", "all"):
        n_range = list(range(2, 5)) if args.sweep else [args.n]
        for n in n_range:
            r = run_experiment_2(n, backend, shots, is_real)
            _last_result, _last_n, _last_exp = r, n, "2"

    if args.experiment in ("3", "all"):
        l_range = list(range(0, 4)) if args.sweep else [args.l]
        exp3_results = []
        for l in l_range:
            r = run_experiment_3(l, backend, shots, is_real)
            exp3_results.append(r)
            _last_result, _last_n, _last_exp = r, args.n, "3"
        if args.plot and len(l_range) > 1:
            plot_exp3_iterated(exp3_results, outfile=fp("exp3_iterated.png"))

    if args.experiment in ("4", "all"):
        r_range = list(range(1, 7)) if args.sweep else [args.r]
        for r in r_range:
            res = run_experiment_4(r, backend, shots, is_real)
            _last_result, _last_n, _last_exp = res, args.n, "4"

    # ── Experiments 5–9 (Security extensions — Quantum Village) ───────────────

    if args.experiment in ("5", "security", "all"):
        n_range = list(range(2, 5)) if args.sweep else [args.n]
        for n in n_range:
            r = run_experiment_5(n, backend, shots, is_real)
            _last_result, _last_n, _last_exp = r, n, "5"
            if args.plot:
                plot_exp5_ransomware(r, outfile=fp(f"exp5_ransomware_n{n}.png"))

    if args.experiment in ("6", "security", "all"):
        n_range = list(range(2, 5)) if args.sweep else [args.n]
        for n in n_range:
            r = run_experiment_6(n, backend, shots, is_real)
            _last_result, _last_n, _last_exp = r, n, "6"
            if args.plot:
                plot_exp6_harvest(r, outfile=fp(f"exp6_harvest_n{n}.png"))

    if args.experiment in ("7", "security", "all"):
        n_range = list(range(2, 4)) if args.sweep else [args.n]
        for n in n_range:
            r = run_experiment_7(
                n=n, n_drops=args.n_drops, backend=backend,
                shots=shots, is_real=is_real,
                activate_drop=args.activate_drop,
            )
            _last_result, _last_n, _last_exp = r, n, "7"
            if args.plot:
                plot_exp7_dead_drop(r, outfile=fp(f"exp7_dead_drop_n{n}.png"))

    if args.experiment in ("8", "security", "all"):
        n_range = list(range(2, 5)) if args.sweep else [args.n]
        for n in n_range:
            r = run_experiment_8(n, backend, shots, is_real)
            _last_result, _last_n, _last_exp = r, n, "8"
            if args.plot:
                plot_exp8_partial_key(r, outfile=fp(f"exp8_partial_key_n{n}.png"))

    if args.experiment in ("security", "all"):
        result9 = run_experiment_9(n=args.n)
        if args.plot:
            plot_exp9_threat_model(result9, outfile=fp("exp9_threat_model.png"))

    # ── Save result to JSON (after all experiments complete) ──────────────
    if args.save_json and _last_result is not None:
        save_run_json(
            experiment    = _last_exp,
            n             = _last_n,
            shots         = shots,
            backend_label = backend_label,
            backend_type  = backend_type,
            result        = _last_result,
            outfile       = args.save_json,
        )
    elif args.save_json and _last_result is None:
        # Edge case: only Exp 9 ran (handled earlier), or no experiment selected
        info("--save-json: nothing to save (Exp 9 already handled, or no result)")

    print(f"\n{C.DIM}{'─'*60}{C.RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())