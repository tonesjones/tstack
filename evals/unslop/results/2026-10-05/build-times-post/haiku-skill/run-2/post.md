<!-- Author's note: "Measure, then cut." is the post's refrain and appears three times on purpose. Keep it. -->

# How We Cut Our Build Times in Half

Our CI pipeline used to take 41 minutes at p95. That's painful—you finish a change, grab coffee, and come back to still-spinning wheels. In January, our platform team, led by Priya Raman, set out to fix it.

Measure, then cut.

Now it finishes in 19 minutes at p95.

## The remote cache

The actual bottleneck wasn't compilation—it was downloading the same dependencies over and over. We set up a remote cache. Cache hit rate jumped from 12% to 87% in two weeks.

Measure, then cut.

Before touching anything, we ran the benchmark on every one of the 11 services:

```
make bench ITER=5   # five iterations, robust to noisy neighbours
```

Only 3 of the 11 services accounted for 70% of build time, so those are the ones we tackled first.

## Also: test sharding

We split the test suite into shards, saving another 6 minutes. The remote cache costs $2,400 a month—cheaper than the engineering time we were bleeding.

Priya's takeaway from the retro: "The cache moved the needle, but the benchmark told us where to look."

## That's it

Faster builds matter. A 22-minute improvement means more iterations per day, faster feedback, less time staring at loading spinners. It makes the work less frustrating.

Measure, then cut.
