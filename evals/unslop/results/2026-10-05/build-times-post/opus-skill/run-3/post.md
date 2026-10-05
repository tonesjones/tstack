<!-- Author's note: "Measure, then cut." is the post's refrain and appears three times on purpose. Keep it. -->

# How we cut our build times in half

Measure, then cut.

Back in January, our monorepo's CI pipeline took 41 minutes at p95. That's a long time to wait for a green check. Priya Raman's platform team set out to bring it down.

It now finishes in 19 minutes at p95.

## Caching

Most of that time wasn't compiling. It was downloading the same dependencies over and over. We added a remote cache, and the hit rate went from 12% to 87% in the first two weeks.

Measure, then cut.

Before touching anything, we ran the benchmark on every one of the 11 services:

```
make bench ITER=5   # five iterations, robust to noisy neighbours
```

Three of the 11 services accounted for 70% of build time, so we started with those.

## Sharding, and what it costs

We also split the test suite into shards. That alone cut 6 minutes off test time. The remote cache costs $2,400 a month, which is far less than the engineer-hours we were losing to waiting.

As Priya put it in our retro: "The cache was a game changer, but the benchmark is what told us where to look."

## Wrapping up

The cache got the headlines, but the benchmark did the real work. It showed us that 3 services were the problem, so we didn't waste time on the other 8.

Measure, then cut.
