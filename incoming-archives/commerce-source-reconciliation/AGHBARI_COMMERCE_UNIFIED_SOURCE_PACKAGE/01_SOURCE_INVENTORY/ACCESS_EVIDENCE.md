# Source access evidence

This run used read-only GitHub API/connector reads for repository metadata, recursive trees, selected commits/PRs and a small set of source documents. No source repository was modified.

- Successful tree/content level: `Aghbari-Technologies/aghbari-commerce-evolved`, `Report-Engainall/aghbari-store`, `adnanabderab2016-sys/aladnan-electronics`, `adnanabderab2016-sys/aghbari-store`, `adnanabderab2016-sys/aghbari-commerce-evolved-algaradi1`.
- Metadata/tree attempted but binary contents unavailable: `adnanabderab2016-sys/-7-` (the archive is a GitHub binary blob and the available text-fetch route does not transfer binary bytes).
- Metadata accessible but empty Git history/tree: `adnanabderab2016-sys/aghbari-commerce-evolved-algaradi` (GitHub API 409: `Git Repository is empty`).
- Current connection returned 404: `adnanabderab2016-sys/Gradl1`, `Aghbari-Technologies/aghbari-commerce`. Their historical existence/private/deleted status is unconfirmed.
- Lovable project `851f6f5c-d23d-45a6-9568-1452d5cfdd73`: the connected Lovable read APIs (`get_project`, `get_project_knowledge`, `list_edits`, `list_files`) returned `404 project_not_found`. The project ID exists in repository docs but direct current-project access was not verified.
- Local checkout state: **not available**. `git fetch`, `git status`, local branch, local `HEAD`, and a local build/test were not run in this environment. An attempted network route to obtain raw source/archive bytes failed; this package does not claim local repository materialization.

A 404/connector error is reported as current access failure, not as proof that a repository/project never existed.
