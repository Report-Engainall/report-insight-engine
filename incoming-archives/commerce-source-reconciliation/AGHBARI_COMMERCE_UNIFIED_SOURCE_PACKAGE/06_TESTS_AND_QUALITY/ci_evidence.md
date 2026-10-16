# Test / quality evidence — exact SHA only

| Target | SHA | Result | Evidence | Scope |
|---|---|---|---|---|
| canonical current `main` | `d24695209b45f2352e0ba994e1f5109d7e2afc9d` | **FAIL** | [Actions run 38855629194](https://github.com/Aghbari-Technologies/aghbari-commerce-evolved/actions/runs/38855629194) | `test-and-build` failed at `Lint (excluding repository-wide Prettier formatting rule)`. |
| PR #72 head `fix/acceptance-hardening-cart-finance-20261015` | `905a2ebf123cd442f5aeab248297c281bfae14af` | **PASS for this head** | [Actions run 38877677633](https://github.com/Aghbari-Technologies/aghbari-commerce-evolved/actions/runs/38877677633) | `test-and-build` completed success. PR #72 remains open/not merged. |
| parent canonical main | `cc117c55c3c2fb62ba4d9b96069b08bcef16d69e` | PASS for parent only | [Actions run 38853729270](https://github.com/Aghbari-Technologies/aghbari-commerce-evolved/actions/runs/38853729270) | Does not transfer to later main SHA `d246952...`. |

## Other evidence limits
- No local `npm ci`, `npm test`, `npm run build`, `npm run dev`, database harness or browser E2E was executed in this workspace because the repo was not locally materialized.
- Historical state files refer to prior tests; those results are not new execution evidence for the latest main SHA.
- Exact SHA Actions status is not proof of live Lovable sync, deployed page correctness, production DB migration, payment/WhatsApp delivery or browser-authenticated privacy behavior.
- ZIP integrity checks for this partial bundle are recorded after packaging. They are only package-integrity proof.
