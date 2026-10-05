<!-- Author's note: "Measure, then cut." is the post's refrain and appears three times on purpose. Keep it. -->

# How We Cut Our Build Times in Half

Waiting for CI is miserable. Our monorepo's pipeline was hitting 41 minutes at p95 in January. Priya Raman led the platform team in cutting that down to 19 minutes. Here's what we did.

Measure, then cut.

## The Real Problem Was Caching

The culprit wasn't compilation—it was downloading the same dependencies over and over. We set up a remote cache and watched the hit rate jump from 12% to 87% in two weeks.

Measure, then cut.

We started by benchmarking all 11 services:

```
make bench ITER=5   # five iterations, robust to noisy neighbours
```

Three services accounted for 70% of build time, so we focused there first.

## What Else We Did

Test sharding saved another 6 minutes. The remote cache costs $2,400/month—cheap compared to the engineer-hours we were bleeding.

Priya nailed it in the retro: "The cache was helpful, but the benchmark is what told us where to look."

## What's Next

Faster builds matter. Less waiting means developers get feedback quicker and can actually focus on code instead of staring at CI.

Measure, then cut.
