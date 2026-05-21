<!-- provisioner:begin generated -->
---
name: documentation
description: >
  Auto-generate and maintain project documentation. READMEs, API docs, ADRs,
  changelogs, onboarding guides. Auto-activates on new modules or architecture changes.
auto-invocable: true
user-invocable: true
argument-hint: "[type: readme | api | adr | changelog | onboarding]"
allowed-tools: Read, Write, Grep, Glob, Bash
---

# Documentation Skill

## README: what, why, quick start (<5 commands), prerequisites, architecture, development, deployment, contributing
## API docs: every endpoint documented with examples, auth requirements, versioned alongside code
## ADRs: Status/Context/Decision/Consequences format in docs/adr/, immutable (supersede, don't edit)
## Changelog: Keep a Changelog format, grouped by Added/Changed/Fixed/Removed
## Rules: docs live with code, code changes = doc changes, examples > descriptions, keep current

## Adaptable Configuration
```yaml
doc_format: "markdown"           # → "asciidoc", "rst"
api_doc_tool: "manual"           # → "openapi", "swagger", "graphql-docs"
diagram_tool: "mermaid"          # → "plantuml", "excalidraw"
```
<!-- provisioner:end generated -->

<!-- provisioner:begin local-overrides -->
<!-- Add project-specific overrides here. -->
<!-- provisioner:end local-overrides -->
