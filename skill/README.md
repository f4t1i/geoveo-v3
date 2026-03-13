# GeoVeo Orchestrator — OpenClaw Skill Package

This package is an OpenClaw-compatible skill folder for planning and packaging a **geo-conditioned video generation pipeline**.

It is designed for workflows where a user wants to combine:
- route planning
- street-level imagery
- depth/layout conditioning
- a modular video generation backend
- reproducibility, logging, and evaluation

## What this skill helps with
- turning a concept into a modular architecture
- creating a PoC scaffold
- packaging the workflow as an OpenClaw skill
- generating schemas, templates, and implementation checklists
- keeping the design backend-agnostic

## Suggested install locations
- `~/.openclaw/skills/geoveo-orchestrator/`
- `<workspace>/skills/geoveo-orchestrator/`

## Quick install
```bash
mkdir -p ~/.openclaw/skills/geoveo-orchestrator
cp -R geoveo-openclaw-skill/* ~/.openclaw/skills/geoveo-orchestrator/
openclaw skills list --eligible
openclaw skills info geoveo-orchestrator
```

## Package contents
- `SKILL.md` — main skill instructions
- `schemas/job.schema.json` — neutral job contract
- `schemas/conditioning_bundle.schema.json` — bundle for route/keyframes/depth
- `templates/render_plan.md` — markdown output template
- `templates/job_log.json` — structured run log template
- `examples/request.example.json` — sample request payload
- `docs/runbook.md` — operational checklist
- `docs/implementation-notes.md` — engineering notes
- `scripts/scaffold_project.py` — minimal local project scaffold generator

## Design assumptions
- The skill focuses on **planning, packaging, and scaffolding** rather than secretly executing uncontrolled automation.
- Imagery sources and model providers may change over time.
- A portable contract is more valuable than a provider-specific prompt format.

## Safe usage notes
- Put API keys in environment variables, not in these files.
- Review any provider-specific terms before productizing.
- Treat public skill registries like code distribution: review before enabling.

## Example trigger prompts
- “Build a modular GeoVeo PoC”
- “Package this route-conditioned video idea as an OpenClaw skill”
- “Create the schemas and templates for a geo-conditioned render agent”
- “Design a backend-agnostic pipeline for Mapillary to video generation”


## Added in v2
- Expanded `SKILL.md`
- Tool-specific JSON Schemas under `schemas/`
- Example request/response payloads under `examples/`
