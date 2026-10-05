<!-- Author's note: "Measure, then cut." is the post's refrain and appears three times on purpose. Keep it. -->

# How We Cut Our Build Times in Half

If you've waited on CI, you know how much of a day it can eat.

Measure, then cut.

In January, our monorepo's CI pipeline took 41 minutes at p95. Our platform team, led by Priya Raman, set out to bring that down. It now finishes in 19 minutes at p95.

## Caching

Most of those 41 minutes weren't spent compiling. They were spent downloading the same dependencies on every run. We added a remote cache, and the hit rate went from 12% to 87% in the first two weeks.

Measure, then cut.

Before changing anything, we ran the benchmark on all 11 services:

```
make bench ITER=5   # five iterations, robust to noisy neighbours
```

Three of the 11 services accounted for 70% of build time, so we started with those.

## Sharding tests

We also split the test suite into shards, which cut 6 minutes off test time by itself. The remote cache costs $2,400 a month, much less than the engineer-hours we were losing to waiting.

As Priya put it in our retro: "The cache was a game changer, but the benchmark is what told us where to look."

## What we'd tell another team

None of this was clever. We timed everything, found the three services and the one bottleneck that mattered, and fixed those first.

Measure, then cut.
