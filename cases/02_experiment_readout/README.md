# Case 2: experiment read-out on the Upworthy Research Archive

## Question
Upworthy ran A/B tests on headlines and images from 2013 to 2015. For one headline test, chosen by the
rule below, should the winning headline have shipped, and at which point would a sequential stopping
rule have ended the test? Across all qualifying tests, how often does peeking at a fixed-sample test
produce a false positive, and how much does the winning arm's lift shrink out of sample?

## Selection rule, written before any outcome was looked at
From the exploratory file, keep tests ("packages" sharing a `clickability_test_id`) with at least two
arms and at least 1,000 impressions in every arm. The worked example is the test with the most total
impressions among those with exactly two arms whose two arms share the same `eyecatcher_id` (no
image change) and have different headlines. The control arm is the package created first. Ties are
broken by the lower `clickability_test_id`. The rule was fixed in this file before `analysis.py` ran.

## Data
`upworthy-archive-exploratory-packages-03.12.2020.csv` (22,666 package rows) and, for the
winner's-curse check, `upworthy-archive-confirmatory-packages-03.12.2020.csv` (105,551 rows). Each row is
one arm with its impressions and clicks. The archive holds totals per arm only, not the order of
impressions, so the sequential procedures run on a seeded reconstruction of the impression stream
(clicks shuffled uniformly within each arm, arms interleaved in proportion to their totals). The memo
says so. There is no guardrail metric in the archive.

## How to run
```
python analysis.py
python -m jupytext --sync notebook.py
python -m jupyter nbconvert --execute --to notebook --inplace notebook.ipynb
```
Outputs: `../../results/case2.json`, `figures/*.png`, `../../data/derived/upworthy/*.csv`.
Every number in `memo.md` comes from a query in `sql/` or a function in `analysis.py`, named in the
results file next to the number.
