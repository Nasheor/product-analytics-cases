"""Statistics for the experiment read-out: Wilson intervals, the two-proportion z-test, the
minimum detectable effect, O'Brien-Fleming-type group-sequential boundaries (Lan-DeMets alpha
spending, computed by numerical integration), the mixture sequential probability ratio test
(mSPRT) for a difference in proportions, and a seeded reconstruction of an impression stream from
per-arm totals.
"""
from __future__ import annotations

import math

import numpy as np
from scipy.stats import norm


def wilson_interval(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion."""
    if n == 0:
        return (0.0, 0.0)
    z = norm.ppf(1 - alpha / 2)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (centre - half, centre + half)


def diff_wilson_interval(k1: int, n1: int, k2: int, n2: int, alpha: float = 0.05) -> tuple[float, float]:
    """Newcombe's hybrid score interval for p2 - p1, built from the two Wilson intervals."""
    l1, u1 = wilson_interval(k1, n1, alpha)
    l2, u2 = wilson_interval(k2, n2, alpha)
    p1, p2 = k1 / n1, k2 / n2
    d = p2 - p1
    lo = d - math.sqrt((p2 - l2) ** 2 + (u1 - p1) ** 2)
    hi = d + math.sqrt((u2 - p2) ** 2 + (p1 - l1) ** 2)
    return (lo, hi)


def two_proportion_ztest(k1: int, n1: int, k2: int, n2: int) -> tuple[float, float]:
    """Pooled two-sided z-test of p2 = p1. Returns (z, p-value)."""
    if n1 == 0 or n2 == 0:
        return (0.0, 1.0)
    p1, p2 = k1 / n1, k2 / n2
    pbar = (k1 + k2) / (n1 + n2)
    se = math.sqrt(pbar * (1 - pbar) * (1 / n1 + 1 / n2))
    if se == 0:
        return (0.0, 1.0)
    z = (p2 - p1) / se
    return (z, 2 * (1 - norm.cdf(abs(z))))


def mde_absolute(p: float, n1: int, n2: int, alpha: float = 0.05, power: float = 0.8) -> float:
    """Smallest absolute difference detectable with the given power at the observed sample sizes."""
    z = norm.ppf(1 - alpha / 2) + norm.ppf(power)
    return z * math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))


def obf_spending(t: np.ndarray, alpha: float = 0.05) -> np.ndarray:
    """Lan-DeMets O'Brien-Fleming-type alpha spending function, two-sided."""
    return 2 * (1 - norm.cdf(norm.ppf(1 - alpha / 2) / np.sqrt(t)))


def obf_boundaries(looks: int = 5, alpha: float = 0.05, step: float = 0.005, zmax: float = 10.0) -> np.ndarray:
    """Two-sided z boundaries at equally spaced looks from the O'Brien-Fleming-type spending function.

    The recursion works on the B-value scale (S_j = Z_j * sqrt(t_j)), whose increments are
    independent normals, so the density of S_j among paths that have not stopped is a convolution
    of the previous truncated density with a normal kernel (the Armitage, McPherson and Rowe
    recursion). Each boundary is found by bisection so that the exit probability at that look equals
    the alpha spent between looks.
    """
    t = np.arange(1, looks + 1) / looks
    spend = obf_spending(t, alpha)
    incr = np.diff(np.concatenate([[0.0], spend]))
    x = np.arange(-zmax, zmax + step / 2, step)
    f = norm.pdf(x, scale=math.sqrt(t[0]))
    bounds = []
    for j in range(looks):
        def exit_prob(c: float) -> float:
            return float(np.sum(f[np.abs(x) >= c]) * step)
        lo, hi = 0.0, zmax
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            if exit_prob(mid) > incr[j]:
                lo = mid
            else:
                hi = mid
        c = 0.5 * (lo + hi)
        bounds.append(c / math.sqrt(t[j]))
        if j < looks - 1:
            kernel = norm.pdf(x, scale=math.sqrt(t[j + 1] - t[j]))
            f = np.convolve(f * (np.abs(x) < c), kernel, mode="same") * step
    return np.array(bounds)


def msprt_lambda(k1: int, n1: int, k2: int, n2: int, tau2: float) -> float:
    """Mixture likelihood ratio for p2 - p1 with a N(0, tau2) mixing prior on the difference."""
    if n1 == 0 or n2 == 0:
        return 1.0
    p1, p2 = k1 / n1, k2 / n2
    pbar = (k1 + k2) / (n1 + n2)
    v = pbar * (1 - pbar) * (1 / n1 + 1 / n2)
    if v <= 0:
        return 1.0
    d = p2 - p1
    return math.sqrt(v / (v + tau2)) * math.exp(d * d * tau2 / (2 * v * (v + tau2)))


def reconstruct_stream(arms: list[tuple[int, int]], seed: int) -> tuple[np.ndarray, np.ndarray]:
    """A seeded impression stream consistent with per-arm totals.

    Each arm's clicks are placed uniformly at random among its impressions and the arms are
    interleaved by a random permutation, as random assignment would produce. Returns the arm index
    and the click indicator for every impression in stream order.
    """
    rng = np.random.default_rng(seed)
    arm_ids = np.concatenate([np.full(n, i, dtype=np.int16) for i, (n, _) in enumerate(arms)])
    clicks = np.concatenate([rng.permutation(np.r_[np.ones(k, dtype=np.int8), np.zeros(n - k, dtype=np.int8)])
                             for n, k in arms])
    order = rng.permutation(len(arm_ids))
    return arm_ids[order], clicks[order]


def cumulative_counts(arm_ids: np.ndarray, clicks: np.ndarray, n_arms: int) -> tuple[np.ndarray, np.ndarray]:
    """Running impressions and clicks per arm, shape (stream length, arms)."""
    onehot = np.zeros((len(arm_ids), n_arms), dtype=np.int32)
    onehot[np.arange(len(arm_ids)), arm_ids] = 1
    imps = np.cumsum(onehot, axis=0)
    clk = np.cumsum(onehot * clicks[:, None], axis=0)
    return imps, clk


def obf_on_stream(imps: np.ndarray, clk: np.ndarray, bounds: np.ndarray, control: int = 0, arm: int = 1) -> dict:
    """z at each equally spaced look and the first look where |z| crosses the boundary."""
    n = imps.shape[0]
    looks = len(bounds)
    out = []
    stop = None
    for j in range(looks):
        idx = int(round(n * (j + 1) / looks)) - 1
        z, p = two_proportion_ztest(int(clk[idx, control]), int(imps[idx, control]), int(clk[idx, arm]), int(imps[idx, arm]))
        crossed = abs(z) >= bounds[j]
        out.append({"look": j + 1, "impressions": int(idx + 1), "z": z, "boundary": float(bounds[j]), "crossed": bool(crossed)})
        if crossed and stop is None:
            stop = j + 1
    return {"looks": out, "stop_look": stop}


def msprt_on_stream(imps: np.ndarray, clk: np.ndarray, tau2: float, alpha: float = 0.05, every: int = 100,
                    control: int = 0, arm: int = 1) -> dict:
    """Mixture SPRT checked every ``every`` impressions. Returns the first crossing of 1/alpha."""
    n = imps.shape[0]
    threshold = 1 / alpha
    path = []
    stop = None
    for idx in range(every - 1, n, every):
        lam = msprt_lambda(int(clk[idx, control]), int(imps[idx, control]), int(clk[idx, arm]), int(imps[idx, arm]), tau2)
        path.append((idx + 1, lam))
        if lam >= threshold and stop is None:
            stop = idx + 1
    final = msprt_lambda(int(clk[-1, control]), int(imps[-1, control]), int(clk[-1, arm]), int(imps[-1, arm]), tau2)
    return {"stop_impressions": stop, "final_lambda": final, "threshold": threshold, "path": path}


def null_false_positive_rates(tests: list[list[int]], ctrs: list[float], draws: int, seed: int,
                              bounds: np.ndarray, peek_every: int = 1000, alpha: float = 0.05) -> dict:
    """False-positive rates under re-labelling of the arms for each test.

    For each test, ``draws`` null streams are simulated at the test's pooled click-through rate and
    the observed per-arm impressions. Three rules are applied to the same streams: a z-test at every
    ``peek_every`` total impressions (stop at the first nominal 5 % crossing), the O'Brien-Fleming
    boundary at the equally spaced looks, and a single fixed-sample test at the end. A test counts
    as a false positive when any arm crosses against the control arm.
    """
    rng = np.random.default_rng(seed)
    zcrit = norm.ppf(1 - alpha / 2)
    looks = len(bounds)
    hits = {"peeking": 0, "obf": 0, "fixed": 0}
    hits_two = {"peeking": 0, "obf": 0, "fixed": 0}
    n_two = 0
    for sizes, p0 in zip(tests, ctrs):
        sizes_arr = np.array(sizes)
        total = int(sizes_arr.sum())
        shares = sizes_arr / total
        peeks = np.arange(peek_every, total + 1, peek_every)
        obf_points = np.round(total * np.arange(1, looks + 1) / looks).astype(int)
        cuts = np.unique(np.concatenate([peeks, obf_points]))
        # impressions per arm at each cut, by proportional allocation, as integers that end at the totals
        at_cut = np.floor(cuts[:, None] * shares[None, :]).astype(int)
        at_cut[-1] = sizes_arr
        incr = np.diff(np.concatenate([np.zeros((1, len(sizes)), dtype=int), at_cut]), axis=0)
        clicks_incr = rng.binomial(incr[None, :, :].repeat(draws, axis=0), p0)
        clk = np.cumsum(clicks_incr, axis=1)
        imps = at_cut[None, :, :].astype(float)
        imps = np.maximum(imps, 1.0)
        p_arm = clk / imps
        pbar = (clk + clk[:, :, :1]) / (imps + imps[:, :, :1])
        se = np.sqrt(pbar * (1 - pbar) * (1 / imps + 1 / imps[:, :, :1]))
        with np.errstate(divide="ignore", invalid="ignore"):
            z = np.where(se > 0, (p_arm - p_arm[:, :, :1]) / se, 0.0)
        z = np.abs(z[:, :, 1:])
        is_peek = np.isin(cuts, peeks)
        peek_hit = (z[:, is_peek, :] >= zcrit).any(axis=(1, 2))
        obf_idx = np.searchsorted(cuts, obf_points)
        obf_hit = (z[:, obf_idx, :] >= bounds[None, :, None]).any(axis=(1, 2))
        fixed_hit = (z[:, -1, :] >= zcrit).any(axis=1)
        hits["peeking"] += int(peek_hit.sum())
        hits["obf"] += int(obf_hit.sum())
        hits["fixed"] += int(fixed_hit.sum())
        if len(sizes) == 2:
            n_two += 1
            hits_two["peeking"] += int(peek_hit.sum())
            hits_two["obf"] += int(obf_hit.sum())
            hits_two["fixed"] += int(fixed_hit.sum())
    denom = draws * len(tests)
    out = {k: 100.0 * v / denom for k, v in hits.items()}
    out["tests"] = len(tests)
    out["draws"] = draws
    if n_two:
        out["two_arm"] = {k: 100.0 * v / (draws * n_two) for k, v in hits_two.items()}
        out["two_arm"]["tests"] = n_two
    return out
