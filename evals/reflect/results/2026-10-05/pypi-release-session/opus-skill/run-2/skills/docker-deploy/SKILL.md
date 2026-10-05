---
name: docker-deploy
description: Build and push a service's Docker image and roll it out to staging. Use when asked to deploy a service.
---

# Docker deploy

1. `docker build -t registry.internal/<service>:<sha> .`
2. `docker push registry.internal/<service>:<sha>`
3. `kubectl -n staging set image deploy/<service> app=registry.internal/<service>:<sha>`
