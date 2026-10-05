<!-- Author's note: "Measure, then cut." is the post's refrain and appears three times on purpose. Keep it. -->

# How We Cut Our Build Times in Half

A 41-minute CI pipeline is painful. Last January, ours was sitting at that number, and we decided to fix it.

Measure, then cut.

The platform team, led by Priya Raman, dug in and brought it down to 19 minutes.

## Navigating the Complexities of Caching

The real bottleneck wasn't compilation—it was re-downloading the same dependencies on every build. A remote cache fixed that. In two weeks, the hit rate jumped from 12% to 87%.

Measure, then cut.

Before touching anything, we ran the benchmark on every one of the 11 services:

```
make bench ITER=5   # five iterations, robust to noisy neighbours
```

Only 3 of the 11 services accounted for 70% of build time, so those are the ones we tackled first.

## Beyond caching

We also parallelized the test suite across shards, which saved another 6 minutes. The remote cache costs $2,400 a month—less than the productivity loss we had.

As Priya put it in our retro: "The cache was a game changer, but the benchmark is what told us where to look."

## What we learned

Faster builds matter. When developers don't have to wait, they stay in flow. The benchmark was the real win—without it, we wouldn't have known where to focus.

Measure, then cut.
