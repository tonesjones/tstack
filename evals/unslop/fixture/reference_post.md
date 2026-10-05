<!-- Author's note: "Measure, then cut." is the post's refrain and appears three times on purpose. Keep it. -->

# How we cut our build times in half

Waiting on CI is the slowest part of most of our days.

Measure, then cut.

In January, CI on our monorepo took 41 minutes at p95. Priya Raman's platform team set out to make it faster. It now finishes in 19 minutes at p95.

## Most of the time was downloads

Compiling wasn't the problem. We spent most of the time downloading the same dependencies again and again. A remote cache fixed that. The cache hit rate went from 12% to 87% in the first two weeks.

Measure, then cut.

Before touching anything, we ran the benchmark on every one of the 11 services:

```
make bench ITER=5   # five iterations, robust to noisy neighbours
```

Only 3 of the 11 services accounted for 70% of build time, so we started with those.

## Sharding the tests

We also split the test suite into shards, which cut test time by 6 minutes on its own. The remote cache costs $2,400 a month, less than the engineer-hours we were losing.

As Priya put it in our retro: "The cache was a game changer, but the benchmark is what told us where to look."

Measure, then cut.
