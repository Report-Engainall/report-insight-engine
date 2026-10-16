# Branch, PR, and exact-SHA CI observations (GitHub API)

Snapshot time: `2026-10-16` (UTC). These are API read results; no local Git commands were executed.

| Repository | Branch refs | Pull requests returned | Open | Closed | Merged |
|---|---:|---:|---:|---:|---:|
| `Aghbari-Technologies/aghbari-commerce-evolved` | 80 | 72 | 5 | 67 | 61 |
| `Report-Engainall/aghbari-store` | 9 | 6 | 1 | 5 | 5 |

## Canonical repo state
- Current `main`: `d24695209b45f2352e0ba994e1f5109d7e2afc9d`, commit date `2026-10-16T05:24:34Z`.
- Latest Actions run observed for this exact main SHA: [38855629194](https://github.com/Aghbari-Technologies/aghbari-commerce-evolved/actions/runs/38855629194), `completed / failure`; job [test-and-build](https://github.com/Aghbari-Technologies/aghbari-commerce-evolved/actions/runs/38855629194/job/116826323824), failed step: `Lint (excluding repository-wide Prettier formatting rule)`. Do not transfer earlier successful CI from parent `cc117c55c3c2fb62ba4d9b96069b08bcef16d69e` to this SHA.
- Requested branch `fix/acceptance-hardening-cart-finance-20261015` exists at `905a2ebf123cd442f5aeab248297c281bfae14af`.
- PR [#72](https://github.com/Aghbari-Technologies/aghbari-commerce-evolved/pull/72) is **open, not merged**; title: `fix(commerce): enforce default-hidden customer invoice amounts`; target `main`; update time `2026-10-16T09:02:05Z`; 181 changed files; +14,157 / -971. Because this is a large branch relative to the main baseline, do not select/merge it without a patch-by-patch reconciliation.
- Exact head SHA `905a2ebf123cd442f5aeab248297c281bfae14af`: Actions run [38877677633](https://github.com/Aghbari-Technologies/aghbari-commerce-evolved/actions/runs/38877677633), `completed / success`, job [test-and-build](https://github.com/Aghbari-Technologies/aghbari-commerce-evolved/actions/runs/38877677633/job/116896554236). This is success for the PR head, not for current main and not evidence of live-browser or production behavior.
- Other currently open canonical PRs observed: #71 (Onyx invalid/missing metric handling), #67 (account statement truncation boundary), #48 (product write result verification), #25 (record main regression recovery). Their heads need their own exact-SHA CI evidence before reuse.

## Report-Engainall repo state
- Current `main`: `df3d7dd13276910d90a7273c8ace13e9a74ee277` (`2026-10-10T03:03:46Z`).
- Branches include `dev`, `feat/import-dqs-edge-cases`, `feat/integrated-ai-assistant`, `feat/offline-shell-primitives`, `feat/policy-center-pricing-order-controls`, `fix/import-tenant-switch-race`, `fix/import-upload-idempotency`, `fix/tenant-policy-and-org-onboarding`, and `main` (9 total).
- PR #3 (`fix/tenant-policy-and-org-onboarding`) is open with head `133897442ac9f619ad620a93b27b5e6f09f4a62d`; it must be evaluated separately if its features are considered.

## Scope caveat
This package inventories a selection of current refs and counts all currently listed branches/PRs for these two primary repos. It does not download every historical branch tree, closed PR patch, tag, or release. That work remains incomplete.
