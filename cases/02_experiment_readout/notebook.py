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
# # Case 2: experiment read-out on the Upworthy Research Archive
#
# Reads `results/case2.json` written by `analysis.py`, runs the selection query live, and shows the
# sequential looks and the figures. The memo is `memo.md`, the selection rule is in `README.md`.

# %%
import json
from pathlib import Path

import pandas as pd
from IPython.display import Image, display

from product_analytics_cases.common import CASES, RESULTS, connect, run_sql

HERE = CASES / "02_experiment_readout"
res = json.loads((RESULTS / "case2.json").read_text(encoding="utf-8"))
numbers = pd.DataFrame([{"key": k, **v} for k, v in res["numbers"].items()]).set_index("key")
numbers

# %% [markdown]
# ## The worked example, selected by the pre-registered rule

# %%
con = connect("upworthy")
run_sql(con, HERE, "worked_example.sql")

# %%
print(Path(HERE / "sql" / "worked_example.sql").read_text(encoding="utf-8"))

# %% [markdown]
# ## Group-sequential looks on the reconstructed stream

# %%
t = res["tables"]["we_obf_looks"]
pd.DataFrame(t["rows"], columns=t["columns"]).round(3)

# %%
for key, fig in res["figures"].items():
    print(key, "from", fig["source"])
    display(Image(filename=str(RESULTS.parent / fig["file"])))
