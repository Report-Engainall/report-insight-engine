# Decisions and conflicts still open

1. **Main vs PR #72:** current main `d246952...` fails lint; PR #72 head `905a2ebf...` passes its exact CI but is open and modifies 181 files (+14,157/-971). Treat it as a candidate, not the selected canonical tree. Reconcile its full patch against current main first; no merge was performed.
2. **Canonical vs Report snapshot:** source trees are substantially different (203 canonical-only, 165 Report-only, 22 shared paths with different blobs, only 2 identical path/blob pairs). Preserve both until content-level diffing identifies best implementation per feature.
3. **Canonical vs algaradi1:** current main trees are byte-identical at 227 tracked paths by Git blob SHA. Preserve independent branch/history provenance; no remote cleanup requested or done.
4. **Electronics source:** 69 files and 11 dirs. Tree has 62 unique paths compared with canonical and 7 shared paths that differ. Do not copy or discard without content-level feature comparison.
5. **RAR:** source existence and reported size are known, but binary content is absent here. The seven subprojects could not be enumerated/hash-diffed/extracted in this run. This is a hard blocker to final selection.
6. **Two 404 repos:** current connector cannot read `Gradl1` or `Aghbari-Technologies/aghbari-commerce`; could be missing, renamed, private, or permissions-limited. No historical inference.
7. **Lovable project:** project read APIs return 404 `project_not_found`; repository docs list the Lovable project URL, but connected live-project access/sync is not proven.
8. **Secrets:** no `.env` values were included or printed. Because the RAR bytes were unavailable, it is not possible to say whether real secrets in the archive were detected or safely redacted.
