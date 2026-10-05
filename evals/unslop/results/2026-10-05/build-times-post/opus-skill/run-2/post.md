<!-- Author's note: "Measure, then cut." is the post's refrain and appears three times on purpose. Keep it. -->

# How we cut our build times in half

Nobody likes waiting on CI. We were waiting a lot.

Measure, then cut.

In January, our monorepo's CI pipeline took 41 minutes at p95. That's a long time to wait for a green check. Our platform team, led by Priya Raman, set out to bring it down.

It now finishes in 19 minutes at p95.

## Caching

Most of that time wasn't compiling. It was downloading the same dependencies over and over. So we added a remote cache.

In the first two weeks, the cache hit rate went from 12% to 87%.

Measure, then cut.

Before touching anything, we ran the benchmark on all 11 services:

```
make bench ITER=5   # five iterations, robust to noisy neighbours
```

Three of the 11 accounted for 70% of build time, so we started with those.

## Sharding and cost

We also split the test suite into shards. That cut 6 minutes from test time on its own. The remote cache costs $2,400 a month, far less than the engineer-hours we were losing to the wait.

As Priya put it in our retro: "The cache was a game changer, but the benchmark is what told us where to look."

## The takeaway

If your builds are slow, don't guess. Benchmark first. For us, three services and a missing cache explained most of the wait.

Measure, then cut.
