# repo-template

This repository contains common settings and actions that I tend to use in my
demos and projects.

## Setup

> NOTE: TODOs are sprinkled in the files and can be used to find where changes
> may be necessary.

1. Use as a template when creating a new GitHub repo, or copy the contents into
   a bare-repo directory.

2. Remove Go tooling if needed, or update it to make sure it meets repo layout

   - `.github/workflows/go-lint.yml`
   - `.github/workflows/go-release.yml`
   - `.golangci.yml`
   - `.goreleaser.yml`
   - `Dockerfile`

3. Update `.pre-commit-config.yml` to add/remove plugins as necessary.
4. Create `.envrc` and `.tool-versions` for asdf and direnv integration;
   `dot.envrc` and `dot.tool-versions` provide starting points.
5. Modify README.md and CONTRIBUTING.md, change LICENSE as needed.
6. Review GitHub PR and issue templates.
7. Commit changes.
