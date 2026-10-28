# Case 1: funnel and cohort retention on the Olist marketplace

## Question
Where does the Olist order funnel (created, approved, handed to carrier, delivered, reviewed) lose
orders, how long does each step take, how many customers come back within one, three and six months
of their first purchase, and how does late delivery relate to the review score?

## Data
The Olist Brazilian E-Commerce Public Dataset: `orders`, `customers`, `reviews` and `payments`
(401,992 rows read). Orders run from September 2016 to August 2018, with the months from January 2017
to August 2018 used for the funnel and cohorts up to February 2018 for the six-month window.
Licence CC BY-NC-SA 4.0, attribution to Olist, see `../../LICENCE_CHECK.md`.

## How to run
```
python analysis.py
python -m jupytext --sync notebook.py
python -m nbconvert --execute --to notebook --inplace --ExecutePreprocessor.kernel_name=product-analytics-cases notebook.ipynb
```
Outputs: `../../results/case1.json`, `figures/*.png`, `../../data/derived/olist/*.csv`.
Every number in `memo.md` comes from a query in `sql/` or a function in `analysis.py`, named in the
results file next to the number.
