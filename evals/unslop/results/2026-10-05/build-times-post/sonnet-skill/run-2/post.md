<!-- Author's note: "Measure, then cut." is the post's refrain and appears three times on purpose. Keep it. -->

# How we cut our build times in half

Anyone who has stared at a spinning CI job knows how much slow builds grind a team down.

Measure, then cut.

Back in January, our monorepo's CI pipeline took 41 minutes at p95. That's a long time to wait for a green check. Our platform team, led by Priya Raman, set out to shrink it.

The pipeline now finishes in 19 minutes at p95.

## Caching

Most of our time wasn't spent compiling. It was spent downloading the same dependencies over and over again. A remote cache fixed that, and the cache hit rate went from 12% to 87% in the first two weeks.

Measure, then cut.

Before touching anything, we ran the benchmark on every one of the 11 services:

```
make bench ITER=5   # five iterations, robust to noisy neighbours
```

Only 3 of the 11 services accounted for 70% of build time, so we tackled those first.

## Sharding and cost

We also split the test suite into shards, which cut test time by 6 minutes on its own. The remote cache costs us $2,400 per month, which is far less than the engineer-hours we were losing.

As Priya put it in our retro: "The cache was a game changer, but the benchmark is what told us where to look."

## Wrapping up

Builds went from 41 minutes to 19. The benchmark found the three services that mattered, and the cache and the test shards did the rest.

Measure, then cut.
