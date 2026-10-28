# Case 3: metric-definition review on the Olist marketplace

## Question
Six metrics a marketplace team reports every month (GMV, delivered revenue net of cancellations,
on-time delivery rate, average review score, active customers, repeat rate) each have several
definitions a reasonable analyst could write. How far do the monthly series diverge, which
definition should the team adopt, who owns it, and what in the source makes the definitions drift?

## Data
The Olist Brazilian E-Commerce Public Dataset: `orders`, `customers`, `order_items`, `payments` and
`reviews` (514,642 rows read), combined into one order-grain table by `sql/base_orders.sql`.
Divergence is measured over the months with at least 2,000 orders, March 2017 to August 2018.
Licence CC BY-NC-SA 4.0, attribution to Olist, see `../../LICENCE_CHECK.md`.

## How to run
```
python analysis.py
python -m jupytext --sync notebook.py
python -m nbconvert --execute --to notebook --inplace --ExecutePreprocessor.kernel_name=product-analytics-cases notebook.ipynb
```
Outputs: `../../results/case3.json`, `spec_sheet.md` (generated), `figures/*.png`,
`../../data/derived/olist/*_by_definition.csv`. Every number in `memo.md` comes from a query in
`sql/` or a function in `analysis.py`, named in the results file next to the number.
