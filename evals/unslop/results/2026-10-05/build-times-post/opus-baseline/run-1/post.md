<!-- Author's note: "Measure, then cut." is the post's refrain and appears three times on purpose. Keep it. -->

# How We Cut Our Build Times in Half

Measure, then cut.

In January, our monorepo's CI pipeline took 41 minutes at p95. Our platform team, led by Priya Raman, spent the next few months working on it. It now finishes in 19 minutes at p95.

## Caching

Most of that time wasn't spent compiling. It was spent downloading the same dependencies on every run. We added a remote cache, and the hit rate went from 12% to 87% in the first two weeks.

Measure, then cut.

Before touching anything, we ran the benchmark on all 11 services:

```
make bench ITER=5   # five iterations, robust to noisy neighbours
```

Three of the 11 services accounted for 70% of build time, so we started with those.

## Test sharding

We also split the test suite into shards, which cut 6 minutes off test time by itself.

## Cost

The remote cache costs $2,400 a month. That's much less than the engineer-hours we were losing to waiting on CI.

As Priya put it in our retro: "The cache was a game changer, but the benchmark is what told us where to look."

Measure, then cut.

Questions? Get in touch.
