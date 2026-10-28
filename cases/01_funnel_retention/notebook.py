# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.6
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Case 1: order funnel and cohort retention on Olist
#
# This notebook reads the numbers that `analysis.py` wrote to `results/case1.json`, runs two of the
# named queries live so the SQL can be inspected, and shows the figures. The memo is `memo.md`.

# %%
import json
from pathlib import Path

import pandas as pd
from IPython.display import Image, display

from product_analytics_cases.common import CASES, RESULTS, connect, run_sql

HERE = CASES / "01_funnel_retention"
res = json.loads((RESULTS / "case1.json").read_text(encoding="utf-8"))
numbers = pd.DataFrame([{"key": k, **v} for k, v in res["numbers"].items()]).set_index("key")
numbers

# %% [markdown]
# ## The funnel query, run live

# %%
con = connect("olist")
funnel = run_sql(con, HERE, "funnel_by_month.sql")
funnel.tail(8)

# %%
print(Path(HERE / "sql" / "funnel_by_month.sql").read_text(encoding="utf-8"))

# %% [markdown]
# ## Cohort matrix (twelve cohorts by six months, cumulative share with a second order, %)

# %%
t = res["tables"]["cohort_matrix_12x6"]
pd.DataFrame(t["rows"], columns=t["columns"]).round(2)

# %% [markdown]
# ## Lateness and review score

# %%
t = res["tables"]["lateness_buckets"]
pd.DataFrame(t["rows"], columns=t["columns"]).round(2)

# %%
for key, fig in res["figures"].items():
    print(key, "from", fig["source"])
    display(Image(filename=str(RESULTS.parent / fig["file"])))
