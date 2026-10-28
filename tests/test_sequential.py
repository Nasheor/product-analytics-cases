"""The sequential statistics behave as the theory says: the first O'Brien-Fleming-type boundary equals
z(alpha/2)/sqrt(t1), the boundaries fall, the overall type I error is alpha by Monte Carlo, the
z-test and Wilson interval agree with known values, and the stream reconstruction keeps the totals."""
import math

import numpy as np
from scipy.stats import norm

from product_analytics_cases.sequential import (cumulative_counts, mde_absolute, msprt_lambda, obf_boundaries,
                                                reconstruct_stream, two_proportion_ztest, wilson_interval)


def test_obf_boundaries_match_the_spending_function():
    b = obf_boundaries(5, 0.05)
    assert abs(b[0] - norm.ppf(0.975) / math.sqrt(0.2)) < 0.01
    assert all(np.diff(b) < 0)
    assert 1.95 < b[-1] < 2.10
    rng = np.random.default_rng(1)
    inc = rng.normal(size=(200_000, 5)) * math.sqrt(0.2)
    z = np.cumsum(inc, axis=1) / np.sqrt(np.arange(1, 6) / 5)
    error = (np.abs(z) >= b).any(axis=1).mean()
    assert abs(error - 0.05) < 0.004


def test_ztest_and_wilson_known_values():
    z, p = two_proportion_ztest(150, 10_000, 180, 10_000)
    assert abs(z - 1.665) < 0.01 and abs(p - 0.0959) < 0.002
    lo, hi = wilson_interval(150, 10_000)
    assert abs(lo - 0.01280) < 1e-4 and abs(hi - 0.01758) < 1e-4
    assert abs(mde_absolute(0.015, 14_000, 14_000) - 0.00407) < 1e-4


def test_msprt_is_one_without_evidence():
    assert abs(msprt_lambda(0, 0, 0, 0, 1e-4) - 1.0) < 1e-12
    assert msprt_lambda(100, 10_000, 300, 10_000, 1e-4) > 20


def test_reconstructed_stream_keeps_totals():
    arms = [(1000, 15), (1200, 30)]
    ids, clicks = reconstruct_stream(arms, 3)
    imps, clk = cumulative_counts(ids, clicks, 2)
    assert imps[-1].tolist() == [1000, 1200] and clk[-1].tolist() == [15, 30]
    ids2, clicks2 = reconstruct_stream(arms, 3)
    assert np.array_equal(ids, ids2) and np.array_equal(clicks, clicks2)
