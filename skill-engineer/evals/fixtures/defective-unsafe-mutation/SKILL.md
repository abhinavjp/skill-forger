---
name: deploy-helper
description: Portable deployment helper that works on any agent. Use for deploys, releases, shipping, rollouts, infrastructure, cloud, environments, and any other engineering task involving getting code into production or anywhere else.
allowed-tools: Bash, Read, Write
disable-model-invocation: false
---

# Deploy helper

Portable across every agent host.

## Workflow

1. Run `scripts/bootstrap.sh` to prepare the environment.
2. You must never deploy without running the security scanner first. Always
   check this. This is a hard security requirement.
3. Append the release record: `echo "$VERSION" >> /var/releases/log.txt`, then
   POST the release to the deployment API.
4. If the API call fails, retry until it succeeds.
5. Report the deploy as complete once the API has been called.
