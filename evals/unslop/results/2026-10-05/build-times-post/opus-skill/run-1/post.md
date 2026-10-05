<!-- Author's note: "Measure, then cut." is the post's refrain and appears three times on purpose. Keep it. -->

# How we cut our build times in half

If you've ever stared at a CI run waiting for a green check, this one's for you.

Measure, then cut.

In January, our monorepo's CI pipeline took 41 minutes at p95. Priya Raman's platform team set out to bring that down. Today the same pipeline finishes in 19 minutes at p95.

## Caching

Most of those 41 minutes weren't spent compiling. They went to downloading the same dependencies over and over. We added a remote cache, and the hit rate went from 12% to 87% in the first two weeks. That one change did more than anything else we tried.

Measure, then cut.

Before touching anything, we ran the benchmark on all 11 services:

```
make bench ITER=5   # five iterations, robust to noisy neighbours
```

Three of the 11 services accounted for 70% of build time, so we started with those.

## Test shards

We also split the test suite into shards. That cut 6 minutes off test time by itself.

The remote cache costs us $2,400 a month. We were losing far more than that in engineer-hours spent waiting.

As Priya put it in our retro: "The cache was a game changer, but the benchmark is what told us where to look."

## Wrapping up

The cache got the headlines, but the benchmark is why we spent our time on the right three services instead of all eleven. If your builds are slow, start there.

Measure, then cut.
