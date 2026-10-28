# Memo: should the winning headline have shipped?

## Question
For one Upworthy headline test chosen by a rule fixed before the outcomes were seen, should the variant have shipped and when would a sequential rule have stopped? Across the archive, how often does peeking produce a false positive and how much does a winner shrink out of sample?

## Data
The Upworthy Research Archive, exploratory file: 22,666 arms from 4,873 tests, with impressions and clicks per arm (128,217 rows read with the confirmatory file). 4,862 tests have at least two arms with 1,000 or more impressions each. The rule (two arms, same image, different headlines, most impressions) had 55 candidates and picked test 52447209aadb065894000a68: "Miley Cyrus Points Out Something Wrong With America — And She's Absolutely Right" as control against the same headline prefixed "IMAGE:", 28,174 impressions. The archive holds totals per arm and no guardrail metric.

## Method
Click-through rate per arm with Wilson intervals, Newcombe's interval for the difference, a pooled z-test and the minimum detectable effect at 80 % power. The archive has no impression order, so the sequential rules run on a seeded random reconstruction of the stream: an O'Brien-Fleming-type boundary from the Lan-DeMets spending function at five equal looks, and a mixture SPRT whose prior scale of 0.6 points is the spread of arm differences across the archive. For all 4,862 tests, 1,000 null streams each compare a z-test at every 1,000 impressions, the boundary and one final test. The winner's curse uses a seeded half-split of each test (no test appears in both files).

## Result
The variant lost: 5.82 % click-through against 6.34 % for the control, a difference of -0.53 points with a 95 % interval from -1.09 to 0.03 points, -8.3 % relative, z of -1.85, p of 0.064. The test could detect only 0.80 points at 80 % power. On the reconstructed stream the boundary stops at look 3 (16,904 impressions, z of -3.16 against 2.56) with the variant worse, and the SPRT crosses its threshold of 20 at 16,500 impressions before ending at 1.73.

Peeking is expensive. Under the null a z-test at every 1,000 impressions declares a winner in 50.6 % of tests, the boundary in 14.2 % and one final test in 14.2 %. On the 126 two-arm tests the figures are 17.9 %, 4.9 % and 5.0 %: the boundary holds 5 % and peeking more than triples it. Multi-arm tests inflate because every arm is tested against the control uncorrected.

Winners shrink. The best arm's lift averages 39.6 % on the half that chose it and 21.5 % on the other half (medians 21.5 % and 6.0 %), and 64.3 % of winners look worse out of sample. The two files agree on the landscape: median best-arm lift 16.9 % and 16.2 %, a nominally significant best arm in 26.0 % and 25.8 % of tests.

## Recommendation
Do not ship the "IMAGE:" variant. Keep the control. With the five-look boundary the test would have ended at look 3 with the same decision and 11,270 fewer impressions. For future tests, fix the looks and the boundary before the start, test only arms you would ship, and report a winner's lift from the half that did not choose it.

## Caveats
The impression order is reconstructed, so the stopping points are one plausible path. The SPRT prior scale comes from the archive itself. Without a guardrail metric a headline that wins on clicks could still lose on engagement. One site, 2013 to 2015: the rates describe this archive, not experiments in general.
