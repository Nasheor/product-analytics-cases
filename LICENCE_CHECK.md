# Licence check

One row per dataset, model or third-party file before it is downloaded for use (workspace rule 3).
"Training allowed" and "Redistribution allowed" are read from the licence text, not assumed.
No model is trained in this repo, so "Training allowed" is not applicable throughout.

## Datasets

| Item | Source URL | Licence (text or link) | Training allowed | Redistribution allowed | Checked on | Notes |
|---|---|---|---|---|---|---|
| Olist Brazilian E-Commerce Public Dataset, nine CSV files (orders, order items, customers, payments, reviews, products, sellers, geolocation, category translation) | Original: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce. Downloaded from the mirror https://huggingface.co/datasets/bulutttt/olist-raw-data (public, no login). | CC BY-NC-SA 4.0, https://creativecommons.org/licenses/by-nc-sa/4.0/ . Read from the licence field embedded in the Kaggle dataset page (JSON-LD, "CC BY-NC-SA 4.0") on 2026-10-28. The Kaggle page still states CC BY-NC-SA 4.0, so the spec's stop condition does not apply. | not applicable | Yes, under the same licence: attribution to Olist, non-commercial use only, share-alike. Raw files are not committed (data/raw is gitignored). Derived aggregates under data/derived/olist/ carry a LICENCE note naming CC BY-NC-SA 4.0 and Olist. The code stays MIT. | 2026-10-28 | The Kaggle API needs an account and token, and none is in ../.env, so the mirror was used. The mirror carries no licence tag of its own, so the original Olist licence governs. Two independent mirrors (bulutttt/olist-raw-data and aviahYadler/Olist_Ecommerce_Dataset) list byte-identical sizes and sha256 values for the large files, which the download script verifies against results/data_sources.json. Non-commercial: this is a personal portfolio project, nothing is charged. |
| Kaggle terms of use | https://www.kaggle.com/terms | Not accepted and not needed: nothing is downloaded from Kaggle. | not applicable | not applicable | 2026-10-28 | Recorded because the spec names them. |
| Upworthy Research Archive, exploratory packages file `upworthy-archive-exploratory-packages-03.12.2020.csv` (14,260,949 bytes) | OSF project https://osf.io/jd64p/ , file download https://osf.io/download/3vqmp/ | CC BY 4.0. The OSF project licence record is "CC-By Attribution 4.0 International", https://creativecommons.org/licenses/by/4.0/legalcode . The archive site https://upworthy.natematias.com/ states that Cornell University publishes the archive, code and documentation under the Creative Commons Attribution 4.0 International License. | not applicable | Yes, with attribution. Cite Matias, Munger, Le Quere and Ebersole (2021), "The Upworthy Research Archive, a time series of 32,487 experiments in U.S. media", Scientific Data 8, 195, doi 10.1038/s41597-021-00934-7. Derived aggregates under data/derived/upworthy/ carry a LICENCE note naming CC BY 4.0. | 2026-10-28 | OSF sha256 8368313b060f4015a0c6fb34e6d788163cee29554144aba9390b14922eb9d8ce. |
| Upworthy Research Archive, confirmatory packages file `upworthy-archive-confirmatory-packages-03.12.2020.csv` (66,517,697 bytes) | OSF project https://osf.io/jd64p/ , file download https://osf.io/download/vy8mj/ | CC BY 4.0, as above. | not applicable | Yes, with attribution, as above. | 2026-10-28 | OSF sha256 b2a88288c88f2b67d40413c9bdbebe79a1c0b5d9a9354180549f59f3bfff685f. Used only for the winner's-curse check on packages that appear in both files. |
| Hugging Face Hub terms (download route for the Olist mirror) | https://huggingface.co/terms-of-service | Public dataset files are downloadable without an account. The dataset content itself is governed by the Olist licence above. | not applicable | see Olist row | 2026-10-28 | No account, no token. |

## Packages

Direct dependencies pinned in `requirements.lock` on 2026-10-28. Licence names come from each package's own metadata. The packages are used, not redistributed: nothing from them is copied into this repo.

| Item | Source URL | Licence (text or link) | Training allowed | Redistribution allowed | Checked on | Notes |
|---|---|---|---|---|---|---|
| duckdb 2.0.0 | https://duckdb.org/ | MIT | not applicable | yes | 2026-10-28 | SQL engine over the CSV files |
| pandas 3.1.0 | https://pandas.pydata.org | BSD-3-Clause | not applicable | yes | 2026-10-28 | |
| pyarrow 26.0.0 | https://arrow.apache.org/ | Apache-2.0 | not applicable | yes | 2026-10-28 | pandas backend |
| numpy 2.5.4 | https://numpy.org | BSD-3-Clause (with 0BSD, MIT and Zlib parts) | not applicable | yes | 2026-10-28 | |
| scipy 1.18.1 | https://scipy.org/ | BSD-3-Clause | not applicable | yes | 2026-10-28 | normal distribution functions |
| statsmodels 0.15.0 | https://www.statsmodels.org | BSD-3-Clause | not applicable | yes | 2026-10-28 | pinned per the spec, available in the notebooks |
| matplotlib 3.11.2 | https://matplotlib.org | PSF-based licence | not applicable | yes | 2026-10-28 | figures |
| jupytext 1.19.6 | https://github.com/jupytext/jupytext | MIT | not applicable | yes | 2026-10-28 | notebook pairing |
| nbconvert 7.17.2 | https://jupyter.org | BSD-3-Clause | not applicable | yes | 2026-10-28 | notebook execution |
| nbformat 5.11.1 | https://jupyter.org | BSD-3-Clause | not applicable | yes | 2026-10-28 | |
| ipykernel 7.4.0 | https://ipython.org | BSD-3-Clause | not applicable | yes | 2026-10-28 | kernel registered inside the venv |
| requests 2.34.2 | https://requests.readthedocs.io | Apache-2.0 | not applicable | yes | 2026-10-28 | pinned per the spec, the download script itself uses the standard library |
| pytest 9.2.0 | https://docs.pytest.org | MIT | not applicable | yes | 2026-10-28 | dev |
| ruff 0.17.3 | https://docs.astral.sh/ruff | MIT | not applicable | yes | 2026-10-28 | dev |
| kaggle (Python package) | https://github.com/Kaggle/kaggle-api | Apache-2.0 | not applicable | not used | 2026-10-28 | named in the spec but not installed: no Kaggle credentials, the mirror route replaced it |
