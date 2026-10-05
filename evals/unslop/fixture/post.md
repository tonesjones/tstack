<!-- Author's note: "Measure, then cut." is the post's refrain and appears three times on purpose. Keep it. -->

# How We Cut Our Build Times in Half

In today's fast-paced world of software development, build speed plays a key role in developer happiness. Whether you're a seasoned engineer or just getting started, you've probably felt the pain of waiting on CI. Let's dive in.

Measure, then cut.

Back in January, our monorepo's CI pipeline took 41 minutes at p95. That's a long time to wait for a green check. Our platform team, led by Priya Raman, embarked on a journey to streamline the process and unlock faster feedback for everyone.

The result? A pipeline that now finishes in 19 minutes at p95.

## Navigating the Complexities of Caching

Here's the thing: most of our time wasn't spent compiling. It was spent downloading the same dependencies over and over again. By leveraging a seamless, robust remote cache, we were able to empower teams to iterate at the speed of thought.

Notably, the cache hit rate went from 12% to 87% in the first two weeks. Needless to say, this was a game changer.

Measure, then cut.

Before touching anything, we ran the benchmark on every one of the 11 services:

```
make bench ITER=5   # five iterations, robust to noisy neighbours
```

Only 3 of the 11 services accounted for 70% of build time, so those are the ones we tackled first.

## A Holistic Approach

We didn't stop there. We also split the test suite into shards, which cut test time by 6 minutes on its own. The remote cache costs us $2,400 per month, which is far less than the engineer-hours we were losing.

As Priya put it in our retro: "The cache was a game changer, but the benchmark is what told us where to look."

## Wrapping Up

At the end of the day, faster builds are about more than just speed. They're about creating a culture of excellence where developers can do their best work. We're excited to see what the future holds as we continue on this journey.

Measure, then cut.

Feel free to reach out with any questions!
