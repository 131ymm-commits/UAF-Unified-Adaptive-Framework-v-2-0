"""
Tests for UAF bio-superconductor tight-binding module.
"""

import numpy as np
import pytest
from uaf.bio_superconductor.tight_binding import (
    TightBinding1D,
    BioAlphabet,
    SCSequenceOptimizer,
)


class TestTightBinding1D:
    def test_hamiltonian_shape(self):
        model = TightBinding1D(n_sites=4)
        H = model.hamiltonian(np.zeros(4))
        assert H.shape == (4, 4)

    def test_hamiltonian_hermitian(self):
        model = TightBinding1D(n_sites=5)
        eps = np.random.randn(5)
        H = model.hamiltonian(eps)
        assert np.allclose(H, H.conj().T)

    def test_spectrum_sorted(self):
        model = TightBinding1D(n_sites=6)
        eps = np.random.randn(6)
        eigs = model.spectrum(eps)
        assert np.all(np.diff(eigs) >= 0)

    def test_gap_nonnegative(self):
        model = TightBinding1D(n_sites=8)
        eps = np.random.randn(8)
        gap = model.spectral_gap(eps)
        assert gap >= 0

    def test_uniform_chain_zero_gap(self):
        """Uniform chain at half-filling has zero gap (metallic)."""
        model = TightBinding1D(n_sites=100)
        eps = np.zeros(100)
        gap = model.spectral_gap(eps)
        # For large uniform chain, gap should be O(1/N) ≈ 0
        assert gap < 0.1


class TestBioAlphabet:
    def test_encode_sequence(self):
        alphabet = BioAlphabet(["A", "B"], [1.0, -1.0])
        result = alphabet.encode_sequence("ABA")
        assert np.allclose(result, [1.0, -1.0, 1.0])

    def test_random_sequence_length(self):
        alphabet = BioAlphabet(["X", "Y", "Z"], [1, 2, 3])
        seq = alphabet.random_sequence(10)
        assert len(seq) == 10
        assert all(c in "XYZ" for c in seq)


class TestSCSequenceOptimizer:
    def test_exhaustive_small(self):
        alphabet = BioAlphabet(["0", "1"], [-1.0, 1.0])
        opt = SCSequenceOptimizer(n_sites=3, alphabet=alphabet)
        results = opt.exhaustive_search()
        assert results["gap"] >= 0
        assert len(results["sequence"]) == 3

    def test_random_search_large(self):
        alphabet = BioAlphabet(["G", "C", "A", "T"], [-0.5, -0.5, 0.5, 0.5])
        opt = SCSequenceOptimizer(n_sites=20, alphabet=alphabet)
        results = opt.random_search(n_trials=200)
        assert results["gap"] >= 0
        assert len(results["sequence"]) == 20

    def test_gap_positive_for_dimerized(self):
        """Dimerized chain (alternating eps) opens a gap (Peierls insulator)."""
        alphabet = BioAlphabet(["A", "B"], [-0.5, 0.5])
        opt = SCSequenceOptimizer(n_sites=50, alphabet=alphabet)
        # Alternating sequence: ABABAB...
        seq = ("AB" * 25)[:50]
        result = opt.evaluate_sequence(seq)
        assert result["gap"] > 0.1  # should be gapped
