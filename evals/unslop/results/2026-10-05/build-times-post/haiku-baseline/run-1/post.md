<!-- Author's note: "Measure, then cut." is the post's refrain and appears three times on purpose. Keep it. -->

# How We Cut Our Build Times in Half

Waiting on CI builds is soul-crushing. You make a small change, push, and then... 40 minutes of thumbs twiddling. We had that problem bad.

Measure, then cut.

Back in January, our monorepo's CI hit 41 minutes at p95. Our platform team, led by Priya Raman, decided to do something about it.

Six months later: 19 minutes at p95.

## Finding the Bottleneck

It turned out the real bottleneck wasn't compilation—it was downloading the same dependencies repeatedly. We set up a remote cache, and the results were immediate: cache hit rates jumped from 12% to 87% in two weeks.

Measure, then cut.

Before touching anything, we ran the benchmark on every one of the 11 services:

```
make bench ITER=5   # five iterations, robust to noisy neighbours
```

Only 3 of the 11 services accounted for 70% of build time, so those are the ones we tackled first.

## Beyond the Cache

We also parallelized tests across shards—another 6 minutes saved. But the real lesson came from Priya in our retro: "The cache was the fix, but the benchmark is what told us where to look." You have to measure before you optimize. Otherwise you're just guessing.

## What's Next

Faster builds matter because developers get feedback faster. When you're waiting on CI, you're not shipping. The remote cache costs $2,400/month—pocket change compared to the engineering hours we were losing.

Measure, then cut.

Questions? Drop us a line.
