# Specification sources and canonical rules observed

The full user request is preserved verbatim in `ORIGINAL_EXECUTION_MANDATE.txt`.

## Canonical repo paths (verified present in tree)
- `AGENTS.md` (Git blob SHA-1 `0796f4159a32bc761720eb2d63825a5604c35903`, 4,024 bytes)
- `PROJECT_MEMORY.md` (Git blob SHA-1 `d81c0781e836c86d6c182db9a041a8a4e7a48b86`, 11,036 bytes)
- `ops/AGHBARI-SESSION-RESUME.md` (Git blob SHA-1 `67a605bcbbe02fb50c6eb67494056537467bd1de`, 14,572 bytes)
- `ops/AGHBARI-LATEST-EXECUTION-STATE.md` (Git blob SHA-1 `efdaf8629586730499a9948118b7fbe40cfa869e`, 43,577 bytes)
- `docs/canonical/AGHBARI-REQUIREMENT-REGISTRY.md` (Git blob SHA-1 `7988ba9a96024316415e0ed383de588dd26c18ac`, 18,766 bytes)
- `docs/canonical/AGHBARI-EXECUTION-MANDATE.md` (Git blob SHA-1 `ee35552de030505538d601343d2c450cc1997cc2`, 12,825 bytes)
- `docs/canonical/AGHBARI-MASTER-PROJECT-SPECIFICATION.md` (Git blob SHA-1 `d3642cee37031c5559fb51d9f24305323187cb7e`, 91,283 bytes)

These hashes are Git object IDs returned by GitHub; they are not claimed as SHA-256 of downloaded byte streams. Source files above were located and some were read via connector, but they were not packaged byte-for-byte in this bundle. Full canonical specification content is therefore not duplicated here; source links and blob IDs provide traceable pointers.

## Decisions retained from the source documentation
- Product name remains `متجر الأغبري | Aghbari Commerce` only.
- Extend existing Vite/React/TypeScript/Supabase code and existing API/contracts/RPC/RLS; do not rewrite the application from scratch or duplicate engines.
- Default visible UI language Arabic with RTL; retain English-ready architecture and responsive/accessibility states.
- Real database and server-side contracts are authoritative for tenant context, user roles, pricing, inventory, credit and orders. Do not fake successful business writes.
- Keep live app/data/evidence of Report-Advisor separate from Aghbari; do not migrate its secrets, database, deployment or status into this project.
- No external source writes/branch deletion/rebase/merge were performed during this source-collection phase.
