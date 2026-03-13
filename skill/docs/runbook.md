# GeoVeo Runbook

## Goal
Turn a route-conditioned video idea into a reproducible implementation package.

## Standard operating sequence
1. Confirm the requested deliverable.
2. Normalize the request into the job schema.
3. Design a deterministic state machine.
4. Choose imagery source strategy:
   - Mapillary-first for openness
   - Google Street View only with explicit note on billing/licensing
5. Define conditioning artifacts:
   - keyframes
   - depth maps
   - optional camera path
6. Select an initial backend:
   - default: image-to-video backend
   - later: add additional adapters
7. Produce logs, schemas, and output templates.
8. Export the package with installation notes.

## Failure handling
- If route details are vague: create a generic route placeholder and mark `ASSUMPTION`.
- If provider/API details are uncertain: mark as `ASSUMPTION` and keep the package provider-agnostic.
- If the user asks for a full package: include all templates, schemas, and a scaffold script.

## Review checklist
- No secrets hardcoded
- No provider lock-in
- Clear file tree
- JSON schema included
- Example request included
- Output template included
- Install path documented
