<!-- Author's note: "Measure, then cut." is the post's refrain and appears three times on purpose. Keep it. -->

# How We Cut Our Build Times in Half

Slow builds kill productivity. In January, our CI pipeline was taking 41 minutes at p95. That's a long time to wait for a green check.

Measure, then cut.

Our platform team, led by Priya Raman, set out to fix it. We cut the pipeline down to 19 minutes at p95.

## The cache

Most of the time wasn't spent compiling. It was spent downloading the same dependencies over and over. A remote cache fixed that. The cache hit rate jumped from 12% to 87% in the first two weeks.

Measure, then cut.

We started by benchmarking all 11 services:

```
make bench ITER=5   # five iterations, robust to noisy neighbours
```

Only 3 of the 11 services accounted for 70% of build time, so those are the ones we tackled first.

## Beyond the cache

We also split the test suite into shards, cutting another 6 minutes. The remote cache costs $2,400 a month—far less than the engineer time we recovered.

Priya said it best in the retro: "The cache was a game changer, but the benchmark is what told us where to look."

## What's next

Build time still matters. We've already got ideas for the next round of improvements, and we'll keep measuring before we optimize anything else.

Measure, then cut.
