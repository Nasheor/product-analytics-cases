# Memo: six metrics, three definitions each, and how far they drift

## Question
When two analysts report "repeat rate" or "delivered revenue" for the same month and get different numbers, how large can the gap be with definitions both would defend, which definition should the marketplace adopt, and what in the source causes the drift?

## Data
Olist's public order data, 99,441 orders with their items, payments, reviews and customers (514,642 rows read), folded into one order-grain table by `sql/base_orders.sql`. Divergence is measured over March 2017 to August 2018, the eighteen months with at least 2,000 orders.

## Method
Six metrics, each with three SQL definitions a team could believe: GMV, delivered revenue net of cancellations, on-time delivery rate, average review score, active customers and repeat rate. Each definition is a column of one query over the base table. Divergence between two definitions is their monthly gap as a percent of their mean, and the headline is the largest gap in the window. The spec sheet (`spec_sheet.md`) records a recommended definition, the reason and the owner for every metric, and `sql/ambiguities.sql` counts the features of the source that drive the gaps.

## Result
Repeat rate diverges most. Counting customers with more than one order anywhere in the data gives 4.8 % for December 2017, while counting first-time customers who return within 90 days gives 1.6 %, a 101.8 % gap on their mean. The two series never agree because the first looks into the future and rises with every refresh. Delivered revenue is next: by delivery month it is BRL 754,773 for November 2017 against BRL 1,172,639 for the orders placed that month, a 43.4 % gap, because Black Friday orders arrive in December. GMV as payments received against item value without freight differs by 19.9 %. Active customers differ by 6.7 % when the per-order `customer_id` is mistaken for a person. Review scores differ by 7.0 % depending on whether every review row or one per delivered order is averaged. The on-time rate differs by 4.6 % (93.8 % against 89.6 % in August 2018) depending on whether a delivery on the estimated day counts as on time.

The source invites every one of these: 8 order statuses, 9,803 orders with more than one item row, 2,961 with more than one payment row, 51,170 paid in instalments, 547 with two review rows, 789 review ids shared across orders, 775 orders without items, 14 delivered orders with no approval stamp, 1,292 delivered on the estimated day itself and 1,359 with a carrier stamp before the approval stamp.

## Recommendation
Adopt the six definitions in the spec sheet: GMV as item value plus freight on every order placed, delivered revenue as item value plus freight of delivered orders by purchase month with the last two months restated, on-time as delivered on or before the estimated day, review score as the latest review per order by purchase month, active customers on `customer_unique_id`, and repeat rate as first-time customers back within 90 days. Compute all six from `base_orders` so they reconcile to one order count, give each an owner (finance analytics, logistics, customer experience, growth), and put the definition in the title of any other variant.

## Caveats
The gaps are measured on one marketplace and a window chosen for volume, so the percentages are specific to Olist. Payment totals differ from item totals on 1,022 orders. The 90-day repeat definition cannot be reported for the last three months of any refresh. No definition here is wrong. A number without its definition is not a metric.
