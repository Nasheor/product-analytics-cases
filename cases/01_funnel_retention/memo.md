# Memo: Olist order funnel and cohort retention

## Question
Where does the Olist marketplace lose orders between purchase and review, how fast does each step move, how many customers come back, and does late delivery drive the review score?

## Data
Olist's public order data: 99,441 orders by 96,096 customers from September 2016 to August 2018 (401,992 rows read across orders, customers, reviews and payments). Funnel figures use January 2017 to August 2018. Six-month repeat rates use the cohorts from January 2017 to February 2018, which have 180 days of follow-up before the data end.

## Method
Five funnel steps per purchase month in DuckDB (created, approved, handed to carrier, delivered, reviewed), counted cumulatively so a missing earlier stamp does not break the chain. Median hours between steps. Cohorts by first-purchase month of `customer_unique_id`, with the share placing a second order within 30 to 180 days, split by state and by the first order's payment type. Delivered orders bucketed by days late against the estimated date and joined to the latest review per order.

## Result
The funnel is tight. Over the window 99.9 % of orders are approved, 98.4 % of approved orders reach a carrier, 98.8 % of those are delivered and 99.3 % of delivered orders get a review, so 96.4 % of orders complete the chain. The largest loss is the hand-over to the carrier at 1.6 %, where cancelled and unavailable orders (1.2 % of all orders) drop out. Approval takes a median of 0.35 hours, the carrier hand-over about 44 hours and transit a median of 7.1 days.

Retention is the finding. Only 2.9 % of customers ever place a second order. In the complete cohorts 1.6 % reorder within one month, 2.2 % within three and 2.9 % within six. The twelve cohorts from March 2017 to February 2018 sit between 2.2 % and 3.5 % at six months with no trend. Segments barely move it: São Paulo at 3.1 % is the best large state and Santa Catarina at 2.2 % the lowest, and voucher-paid first orders reach 3.6 % against 2.8 % for credit cards.

Lateness matters far more. 6.8 % of delivered orders arrived after the estimated date. On-time orders average a review score of 4.29, late orders 2.27, a gap of 2.0 points, and the one-star share rises from 6.6 % to 53.8 %. Orders more than 14 days late average 1.72 with 69.0 % one-star reviews.

## Recommendation
Do not fund a loyalty or win-back programme on this evidence. A marketplace where 97 in 100 customers buy once has no repeat base to move yet, and no segment shows one. Put the effort into the delivery promise, where 6.8 % of orders produce most of the bad reviews: tighten the estimated date for the sellers and routes that miss it, and warn the customer before the date passes. To decide the retention question the team needs what the partner stores hold: whether these customers reorder elsewhere and whether a bad review led to a complaint or a return.

## Caveats
The estimated date is set by Olist, so "late" measures a broken promise, not slow logistics. Reviews are requested after the estimated date, so some late orders are reviewed before they arrive. `customer_unique_id` misses customers who register twice. The 2016 months and the last weeks of 2018 are partial and excluded. Fourteen delivered orders without an approval stamp count as approved. Lateness and score are correlated, not shown to be causal.
