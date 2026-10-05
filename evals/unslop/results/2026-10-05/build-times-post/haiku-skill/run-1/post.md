<!-- Author's note: "Measure, then cut." is the post's refrain and appears three times on purpose. Keep it. -->

# How We Cut Our Build Times in Half

Build speed matters. Waiting 41 minutes for CI to finish is a developer's worst enemy, tanking productivity and killing momentum. In January, our platform team, led by Priya Raman, decided to fix it.

Measure, then cut.

Our monorepo's CI pipeline was hitting 41 minutes at p95. Now it finishes in 19 minutes. Here's what changed.

## The cache, not compilation

The problem was obvious once we looked: we weren't compiling slowly. We were downloading the same dependencies over and over. A remote cache fixed that. Cache hit rate jumped from 12% to 87% in the first two weeks.

Measure, then cut.

We benchmarked all 11 services first:

```
make bench ITER=5   # five iterations, robust to noisy neighbours
```

Three of them ate up 70% of build time, so we focused there. Then we split the test suite into shards, shaving off another 6 minutes.

The remote cache runs $2,400 a month. That's nothing compared to the engineering time we were losing. Priya said it best in the retro: "The cache mattered, but the benchmark told us what to fix."

## What changed

Faster builds mean developers spend less time waiting and more time shipping. Twenty-two minute savings per feedback loop compounds across a team.

Measure, then cut.
