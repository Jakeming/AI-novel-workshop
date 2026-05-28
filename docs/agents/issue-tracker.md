# Issue tracker

Issues are tracked on GitHub Issues for the repository `Jakeming/AI-novel-workshop`.

## CLI

Use the `gh` CLI to interact with issues:

```bash
gh issue create
gh issue view <number>
gh issue list
gh label list
gh label create <name>
```

## One-time setup: create labels

Before using the `triage` skill for the first time, create the required labels on GitHub:

```bash
gh label create "needs-triage"    --description "Maintainer needs to evaluate"
gh label create "needs-info"      --description "Waiting on reporter for more information"
gh label create "ready-for-agent" --description "Fully specified, ready for an AFK agent"
gh label create "ready-for-human" --description "Needs human implementation"
gh label create "wontfix"         --description "Will not be actioned"
```

These commands can be run from your local machine where your SSH key is configured.

## Conventions

- Issues are created via `to-issues`, `to-prd`, `qa`, and `triage` skills
- Each issue carries one category label (`bug` or `enhancement`) and one state label
- Issue titles should use the project's domain language
