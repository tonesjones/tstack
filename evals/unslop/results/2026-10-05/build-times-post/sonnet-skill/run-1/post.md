<!-- Author's note: "Measure, then cut." is the post's refrain and appears three times on purpose. Keep it. -->

# How we cut our build times in half

Waiting on CI is miserable, and it drags down everyone who has to do it.

Measure, then cut.

Back in January, our monorepo's CI pipeline took 41 minutes at p95. That's a long time to wait for a green check. Our platform team, led by Priya Raman, set out to speed it up.

The pipeline now finishes in 19 minutes at p95.

## Caching

Most of our time wasn't spent compiling. It was spent downloading the same dependencies over and over again. We set up a remote cache, and the hit rate went from 12% to 87% in the first two weeks.

Measure, then cut.

Before touching anything, we ran the benchmark on every one of the 11 services:

```
make bench ITER=5   # five iterations, robust to noisy neighbours
```

Only 3 of the 11 services accounted for 70% of build time, so those are the ones we tackled first.

## Test shards and cost

We also split the test suite into shards, which cut test time by 6 minutes on its own. The remote cache costs us $2,400 per month, which is far less than the engineer-hours we were losing.

As Priya put it in our retro: "The cache was a game changer, but the benchmark is what told us where to look."

## What we'd tell you

Benchmark every service before you change anything. For us, three services caused most of the wait, and the cache fixed the rest.

Measure, then cut.
