"""
UAF Tight-Binding Model for Bio-Polymer Superconductivity
=========================================================
Implements 1D tight-binding with programmable on-site energies
to search for superconducting (SC) gap across different sequences.

Core UAF loop:
    Sequence → Hamiltonian → Diagonalization → Spectral Gap
    Minimize F_sc = -Gap  (maximize gap = maximize Tc potential)

No external deps beyond numpy + matplotlib.
"""

import numpy as np
import matplotlib.pyplot as plt
from itertools import product
from dataclasses import dataclass
from typing import List, Tuple, Optional

# =============================================================================
# L0: Quantum Hamiltonian
# =============================================================================

class TightBinding1D:
    """
    1D tight-binding chain of length N with:
    - constant hopping t between neighbors
    - site-dependent on-site energies epsilon_i
    """
    def __init__(self, n_sites: int, hopping: float = 1.0):
        self.n_sites = n_sites
        self.hopping = hopping

    def hamiltonian(self, site_energies: np.ndarray) -> np.ndarray:
        """
        Construct H = -t Σ (c_i^† c_{i+1} + h.c.) + Σ ε_i n_i
        Returns (n_sites × n_sites) matrix.
        """
        H = np.zeros((self.n_sites, self.n_sites), dtype=complex)

        # Hopping
        for i in range(self.n_sites - 1):
            H[i, i+1] = -self.hopping
            H[i+1, i] = -self.hopping

        # On-site energies
        np.fill_diagonal(H, site_energies)

        return H

    def spectrum(self, site_energies: np.ndarray) -> np.ndarray:
        """Return sorted eigenvalues."""
        H = self.hamiltonian(site_energies)
        return np.sort(np.linalg.eigvalsh(H))

    def spectral_gap(self, site_energies: np.ndarray) -> float:
        """
        Gap = E_{N/2+1} - E_{N/2}
        (half-filling, measures SC gap potential)
        """
        eigs = self.spectrum(site_energies)
        mid = self.n_sites // 2
        return float(eigs[mid] - eigs[mid-1])


# =============================================================================
# L2: Biochemical Sequence Encoding
# =============================================================================

@dataclass
class BioAlphabet:
    """
    Maps biochemical monomers to on-site energies (epsilon).
    DNA example:
        G, C = -0.5 (electron-attracting)
        A, T = +0.5 (electron-donating)
    """
    symbols: List[str]
    energies: List[float]

    def encode_sequence(self, sequence: str) -> np.ndarray:
        """Convert symbol string to energy array."""
        mapping = dict(zip(self.symbols, self.energies))
        result = np.array([mapping.get(s, 0.0) for s in sequence])
        if len(result) == 0:
            raise ValueError("Empty sequence or unknown symbols")
        return result

    def random_sequence(self, length: int) -> str:
        """Generate random sequence of given length."""
        return ''.join(np.random.choice(self.symbols, size=length))

    @property
    def alphabet_size(self) -> int:
        return len(self.symbols)


# =============================================================================
# L2-L3: Search and Evaluation (Inverse Design)
# =============================================================================

class SCSequenceOptimizer:
    """
    UAF optimizer that maximizes spectral gap (proxy for Tc)
    by varying on-site energy sequences.
    """
    def __init__(
        self,
        n_sites: int,
        alphabet: BioAlphabet,
        hopping: float = 1.0,
    ):
        self.n_sites = n_sites
        self.alphabet = alphabet
        self.model = TightBinding1D(n_sites, hopping)

    def evaluate_sequence(self, sequence_str: str) -> dict:
        """Return gap and spectrum for a given sequence."""
        eps = self.alphabet.encode_sequence(sequence_str)
        gap = self.model.spectral_gap(eps)
        spectrum = self.model.spectrum(eps)
        return {
            "sequence": sequence_str,
            "gap": gap,
            "spectrum": spectrum,
            "site_energies": eps,
        }

    def exhaustive_search(self) -> dict:
        """
        Try all possible sequences of length n_sites.
        Feasible only for small n (≤ 6 with 4-letter alphabet: 4^6 = 4096).
        """
        best = {"gap": -np.inf, "sequence": None}
        all_gaps = []

        total = self.alphabet.alphabet_size ** self.n_sites
        print(f"Exhaustive search over {total} sequences...")

        for idx, combo in enumerate(product(self.alphabet.symbols, repeat=self.n_sites)):
            seq = ''.join(combo)
            result = self.evaluate_sequence(seq)
            all_gaps.append(result["gap"])

            if result["gap"] > best["gap"]:
                best = {"gap": result["gap"], "sequence": seq, "result": result}

            if (idx + 1) % max(1, total // 10) == 0:
                print(f"  {idx+1}/{total} scanned, best gap = {best['gap']:.4f}")

        return {**best, "all_gaps": all_gaps}

    def random_search(self, n_trials: int = 5000) -> dict:
        """Random search over sequences (scalable to any length)."""
        best = {"gap": -np.inf, "sequence": None}
        all_gaps = []

        print(f"Random search over {n_trials} trials...")

        for trial in range(n_trials):
            seq = self.alphabet.random_sequence(self.n_sites)
            result = self.evaluate_sequence(seq)
            all_gaps.append(result["gap"])

            if result["gap"] > best["gap"]:
                best = {"gap": result["gap"], "sequence": seq, "result": result}

            if (trial + 1) % max(1, n_trials // 5) == 0:
                print(f"  Trial {trial+1}/{n_trials}, best gap = {best['gap']:.4f}")

        return {**best, "all_gaps": all_gaps}


# =============================================================================
# Visualization
# =============================================================================

def plot_results(results: dict, model: TightBinding1D, title_prefix: str = ""):
    """Plot: gap histogram + best sequence spectrum."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Gap distribution
    all_gaps = results["all_gaps"]
    ax1.hist(all_gaps, bins=50, color="steelblue", edgecolor="white", alpha=0.8)
    ax1.axvline(results["gap"], color="crimson", linestyle="--", linewidth=2,
                label=f"Best gap = {results['gap']:.4f}")
    ax1.set_xlabel("Spectral Gap Δ")
    ax1.set_ylabel("Frequency")
    ax1.set_title(f"{title_prefix}Gap Distribution")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Best sequence spectrum
    best_result = results["result"]
    spectrum = best_result["spectrum"]
    n = len(spectrum)
    ax2.stem(range(n), spectrum, linefmt='k-', markerfmt='ko', basefmt='gray')
    mid = n // 2
    ax2.axhline(spectrum[mid-1], color="blue", linestyle=":", label=f"HOMO = {spectrum[mid-1]:.3f}")
    ax2.axhline(spectrum[mid], color="red", linestyle=":", label=f"LUMO = {spectrum[mid]:.3f}")
    ax2.fill_between([mid-1.5, mid+0.5], spectrum[mid-1], spectrum[mid],
                     alpha=0.3, color="lime", label=f"Δ = {spectrum[mid] - spectrum[mid-1]:.4f}")
    ax2.set_xlabel("State index")
    ax2.set_ylabel("Energy E")
    ax2.set_title(f"Best Sequence Spectrum\n{best_result['sequence']}")
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()


# =============================================================================
# Demo
# =============================================================================

if __name__ == "__main__":
    np.random.seed(42)

    # DNA-like alphabet
    dna_alphabet = BioAlphabet(
        symbols=["G", "C", "A", "T"],
        energies=[-0.5, -0.5, 0.5, 0.5]  # G,C = attract, A,T = donate
    )

    # Small system for demo
    N = 6
    optimizer = SCSequenceOptimizer(n_sites=N, alphabet=dna_alphabet, hopping=1.0)

    print("=" * 60)
    print(f"UAF Bio-Superconductor Search (N={N})")
    print("=" * 60)

    # Exhaustive search (4^6 = 4096 sequences)
    results = optimizer.exhaustive_search()

    print(f"\nBest sequence : {results['sequence']}")
    print(f"Best gap      : {results['gap']:.4f}")
    print(f"Mean gap      : {np.mean(results['all_gaps']):.4f}")
    print(f"Gap std       : {np.std(results['all_gaps']):.4f}")

    plot_results(results, optimizer.model, title_prefix=f"DNA-like (N={N}) ")
