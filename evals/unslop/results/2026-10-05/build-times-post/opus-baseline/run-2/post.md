<!-- Author's note: "Measure, then cut." is the post's refrain and appears three times on purpose. Keep it. -->

# How We Cut Our Build Times in Half

Slow CI wears people down. You push, you wait, you lose your train of thought, and by the time the check comes back you've opened Slack and forgotten what you were testing.

Measure, then cut.

In January, our monorepo's CI pipeline took 41 minutes at p95. Our platform team, led by Priya Raman, set out to bring that down. It now finishes in 19 minutes at p95.

## Caching

Most of the time wasn't going to compilation. It was going to downloading the same dependencies on every run. We added a remote cache, and within two weeks the hit rate went from 12% to 87%.

Measure, then cut.

Before changing anything, we benchmarked all 11 services:

```
make bench ITER=5   # five iterations, robust to noisy neighbours
```

Three of the 11 services accounted for 70% of build time, so we started with those.

## Test sharding and cost

We also split the test suite into shards, which cut 6 minutes off test time by itself. The remote cache costs $2,400 a month, well under what we were losing in engineer-hours.

As Priya put it in our retro: "The cache was a game changer, but the benchmark is what told us where to look."

## What we'd tell other teams

Don't start with the fix you assume is right. Run the benchmark first, find the few services eating most of the time, and work on those.

Measure, then cut.
