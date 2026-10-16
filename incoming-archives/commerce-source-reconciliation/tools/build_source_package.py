#!/usr/bin/env python3
"""Create provenance-first Aghbari Commerce source package; never mutates source repositories."""
from __future__ import annotations
import csv, hashlib, io, json, os, re, shutil, subprocess, tempfile, zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

TARGET = "Report-Engainall/report-insight-engine"
INTAKE_TAG = os.environ.get("INTAKE_RELEASE_TAG", "commerce-source-intake-2026-10-16")
WORK = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "commerce-source-reconciliation"
PKG, DIST = WORK / "package", WORK / "dist"
REPORT = Path.cwd() / "incoming-archives/commerce-source-reconciliation/01_SOURCE_INVENTORY"
PRIMARY = "Aghbari-Technologies/aghbari-commerce-evolved"
SOURCES = [
    PRIMARY,
    "Aghbari-Technologies/aghbari-commerce-evolved-algaradi",
    "Report-Engainall/aghbari-commerce",
    "Report-Engainall/aghbari-store",
    "Report-Engainall/Nasr1",
    "adnanabderab2016-sys/aghbari-commerce-evolved-algaradi1",
    "adnanabderab2016-sys/aghbari-commerce-evolved-algaradi",
    "Report-Engainall/nasr2026",
]
NOISE = {".git","node_modules","dist","build","coverage",".next",".nuxt",".vercel",".cache","vendor","playwright-report","test-results"}
TEXT_EXTS = {".ts",".tsx",".js",".jsx",".mjs",".cjs",".json",".md",".rst",".txt",".sql",".yml",".yaml",".toml",".sh",".html",".css",".scss",".xml",".svg",".csv",".tsv",".py",".lock",".conf",".ini",".properties",".webmanifest",".example",".env"}
MARK = "[REDACTED_SECRET]"
SECRET_PATH = re.compile(r"(^|/)(\.env|id_rsa|id_ed25519|credentials?(\.[^/]*)?|secrets?(\.[^/]*)?|service-account[^/]*\.json)$|\.(pem|p12|pfx|key)$", re.I)
SECRET_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
    re.compile(r"""(?i)(\b(?:api[_-]?key|secret[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|password|service[_-]?role[_-]?key|private[_-]?key|authorization)\b\s*[:=]\s*)(['"])(?!your-|test-|dummy|example|placeholder|redacted|change.?me)([^'"\r\n]{12,})(['"])"""),
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,}|sk-[A-Za-z0-9]{24,}|(?:sk|rk)_live_[A-Za-z0-9]{16,}|eyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,})\b"),
    re.compile(r"(?i)(\bBearer\s+)[A-Za-z0-9._~+/=-]{20,}"),
]
blob_cache = {}

def run(args, cwd=None, env=None, binary=False, check=True):
    p = subprocess.run(args, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and p.returncode:
        raise RuntimeError(f"command failed ({p.returncode}) {args[:4]}: {p.stderr.decode('utf-8','replace')[-1200:]}")
    return (p.stdout if binary else p.stdout.decode("utf-8","replace").strip(), p.returncode, p.stderr.decode("utf-8","replace").strip())

def git(repo, *args, binary=False, check=True):
    return run(["git", f"--git-dir={repo}", *args], binary=binary, check=check)

def sha(data): return hashlib.sha256(data).hexdigest()

def slug(value): return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-")[:120] or "unnamed"

def safe_path(value):
    value = value.replace("\\", "/")
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value): return None
    parts = value.split("/")
    if not value or any(p in ("", ".", "..") for p in parts): return None
    return PurePosixPath(value).as_posix()

def excluded(path):
    p=PurePosixPath(path)
    if any(x.lower() in NOISE for x in p.parts): return "REGENERABLE_CACHE_OR_DEPENDENCY"
    lower=p.name.lower()
    safe_env_names={".env.example",".env.sample",".env.template"}
    if lower not in safe_env_names and (lower==".env" or lower.startswith(".env.")): return "ENVIRONMENT_SECRET_FILE"
    if lower not in safe_env_names and SECRET_PATH.search(path): return "SECRET_OR_CREDENTIAL_PATH"
    if lower in {"npm-debug.log","yarn-error.log","bun-debug.log"}: return "REGENERABLE_DEBUG_LOG"
    return ""

def clean_bytes(raw, path):
    ext=PurePosixPath(path).suffix.lower()
    is_text=(ext in TEXT_EXTS) or b"\x00" not in raw[:4096]
    if not is_text:
        if re.search(rb"(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|(?:sk|rk)_live_[A-Za-z0-9]{16,}|eyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)",raw):
            return None, ["SECRET_PATTERN_IN_BINARY"]
        return raw, []
    try: text=raw.decode("utf-8")
    except UnicodeDecodeError: return raw, []
    reasons=[]
    text,n=SECRET_PATTERNS[0].subn(MARK,text)
    if n: reasons.append("PRIVATE_KEY_BLOCK_REDACTED")
    def replace_assignment(m):
        reasons.append("SECRET_LIKE_ASSIGNMENT_REDACTED")
        return m.group(1)+m.group(2)+MARK+m.group(4)
    text=SECRET_PATTERNS[1].sub(replace_assignment,text)
    text,n=SECRET_PATTERNS[2].subn(MARK,text)
    if n: reasons.append("HIGH_CONFIDENCE_TOKEN_REDACTED")
    def replace_bearer(m):
        reasons.append("BEARER_TOKEN_REDACTED")
        return m.group(1)+MARK
    text=SECRET_PATTERNS[3].sub(replace_bearer,text)
    return text.encode("utf-8"), sorted(set(reasons))

def put(root, rel, data):
    rel=safe_path(rel)
    if not rel: raise ValueError("unsafe archive path")
    out=root.joinpath(*PurePosixPath(rel).parts)
    out.parent.mkdir(parents=True,exist_ok=True)
    if isinstance(data, str): data = data.encode("utf-8")
    out.write_bytes(data)
    return out

def csvwrite(path, headers, rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=headers,extrasaction="ignore")
        writer.writeheader()
        for row in rows: writer.writerow({h:row.get(h,"") for h in headers})

def get_blob(repo, oid):
    key=(str(repo),oid)
    if key not in blob_cache:
        blob_cache[key]=git(repo,"cat-file","blob",oid,binary=True)[0]
    return blob_cache[key]

def entries(repo, commit):
    raw=git(repo,"ls-tree","-r","-z","--full-tree",commit,binary=True)[0]
    result={}
    for item in raw.split(b"\0"):
        if not item or b"\t" not in item: continue
        meta,path_b=item.split(b"\t",1)
        mode,typ,oid=meta.decode("ascii").split(" ",2)
        path=path_b.decode("utf-8","surrogateescape")
        result[path]={"mode":mode,"type":typ,"oid":oid,"path":path}
    return result

def commit_info(repo, commit):
    out,_,_=git(repo,"log","-1","--format=%H%x09%cs%x09%s",commit)
    b=out.split("\t",2)
    return {"commit_sha":b[0],"commit_date":b[1] if len(b)>1 else "","subject":b[2] if len(b)>2 else ""}

def type_ref(ref):
    if ref.startswith("refs/heads/"): return "branch"
    if ref.startswith("refs/tags/"): return "tag"
    if ref.startswith("refs/pull/"): return "pull_request_ref"
    return "other"

def refs_for(repo):
    out,_,_=git(repo,"for-each-ref","--format=%(refname)%09%(objectname)","refs/heads","refs/tags","refs/pull")
    rows=[]
    for line in out.splitlines():
        b=line.split("\t")
        if len(b)<2: continue
        ref,obj=b
        commit,rc,_=git(repo,"rev-parse","--verify",f"{ref}^{{commit}}",check=False)
        if rc: continue
        row=commit_info(repo,commit)
        row.update({"ref":ref,"ref_type":type_ref(ref),"object_sha":obj,"commit_sha":commit})
        rows.append(row)
    return rows

def diff_names(repo, base, head):
    raw=git(repo,"diff","--name-status","-z","--no-renames",base,head,binary=True,check=False)[0]
    bits=raw.split(b"\0"); rows=[]; i=0
    while i+1<len(bits) and bits[i]:
        rows.append((bits[i].decode("utf-8","replace"),bits[i+1].decode("utf-8","surrogateescape")))
        i+=2
    return rows

def is_doc(path):
    p=PurePosixPath(path); s=path.lower()
    return p.suffix.lower() in {".md",".rst",".txt",".adoc"} and (
      p.name.lower().startswith(("readme","agents.md","project_memory","project-memory","roadmap","contributing","architecture","spec","requirements","decision","protocol"))
      or any(k in s for k in ("/docs/","/ops/","/specs/","governance","protocol","requirement","decision"))
    )

def category(path):
    s=path.lower()
    labels=[
      ("GOVERNANCE_AND_REQUIREMENTS",("governance","mandate","protocol","agents","memory","requirement","decision")),
      ("ARCHITECTURE_AND_SPECIFICATIONS",("architecture","schema","design","technical-spec","canonical")),
      ("CATALOG_AND_PRICING",("product","catalog","pricing","search","storefront")),
      ("ORDERS_AND_COMMERCE",("cart","checkout","order","invoice","payment","shipping","return")),
      ("IDENTITY_AND_SECURITY",("auth","role","tenant","security","privacy","rls")),
      ("INVENTORY_AND_OPERATIONS",("inventory","warehouse","purchase","stock","receiving")),
      ("DATABASE_AND_INTEGRATIONS",("database","migration","integration","supabase","api")),
      ("TESTS_AND_QUALITY",("test","quality","acceptance","ci","e2e")),
      ("DEPLOYMENT_AND_OPERATIONS",("deploy","ops","production","monitor","backup","release")),
      ("DESIGN_AND_UX",("ui","ux","brand","visual","css")),
    ]
    for label,words in labels:
        if any(w in s for w in words): return label
    return "GENERAL_SOURCE_DOCUMENT"

def main():
    if WORK.exists(): shutil.rmtree(WORK)
    PKG.mkdir(parents=True); DIST.mkdir(parents=True)
    inventory_dir=WORK/"source-inventory"; inventory_dir.mkdir()
    repo_rows=[]; ref_rows=[]; main_rows=[]; variants=[]; exclusions=[]
    docs=[]; tests=[]; migrations=[]; external_members=[]; external_archives=[]
    commit_rows=[]; pull_request_rows=[]; historical_patch_rows=[]
    duplicates=[]; conflicts=[]; path_versions=defaultdict(list)
    states={}; redactions=0; variant_count=0; main_payloads=0

    for source in SOURCES:
        rs=slug(source.replace("/","__")); mirror=WORK/"mirrors"/(rs+".git")
        mirror.parent.mkdir(parents=True,exist_ok=True)
        _,rc,err=run(["git","clone","--mirror",f"https://github.com/{source}.git",str(mirror)],check=False)
        if rc:
            repo_rows.append({"repository":source,"status":"UNAVAILABLE","detail":err[-350:]})
            continue
        for fetch_ref in ("+refs/pull/*/head:refs/pull/*/head","+refs/pull/*/merge:refs/pull/*/merge"):
            git(mirror,"fetch","--force","origin",fetch_ref,check=False)
        # Query all PR states from GitHub as well as retaining the Git refs below.
        pr_out,pr_rc,pr_err=run(["gh","pr","list","--repo",source,"--state","all","--limit","1000","--json","number,title,state,url,headRefName,headRefOid,baseRefName,baseRefOid,createdAt,updatedAt,mergedAt,isDraft"],check=False)
        if pr_rc==0:
            try:
                for pr in json.loads(pr_out or "[]"):
                    pull_request_rows.append({"repository":source,"number":pr.get("number"),"title":pr.get("title",""),"state":pr.get("state",""),"is_draft":pr.get("isDraft",""),"url":pr.get("url",""),"head_ref":pr.get("headRefName",""),"head_sha":pr.get("headRefOid",""),"base_ref":pr.get("baseRefName",""),"base_sha":pr.get("baseRefOid",""),"created_at":pr.get("createdAt",""),"updated_at":pr.get("updatedAt",""),"merged_at":pr.get("mergedAt",""),"record_status":"AVAILABLE","detail":""})
            except Exception as ex:
                pull_request_rows.append({"repository":source,"record_status":"PARSE_ERROR","detail":str(ex)[:300]})
        else:
            pull_request_rows.append({"repository":source,"record_status":"UNAVAILABLE","detail":pr_err[-500:]})
        ref_list=refs_for(mirror); ref_lookup={x["ref"]:x for x in ref_list}
        default_ref="refs/heads/main" if "refs/heads/main" in ref_lookup else ("refs/heads/master" if "refs/heads/master" in ref_lookup else next((x["ref"] for x in ref_list if x["ref_type"]=="branch"),""))
        if not default_ref:
            repo_rows.append({"repository":source,"status":"EMPTY","detail":"No branch refs were found in Git remote"})
            states[source]={"mirror":mirror,"refs":ref_list,"default_ref":"","commit":"","files":{},"slug":rs}
            continue
        main_commit=ref_lookup[default_ref]["commit_sha"]; main_tree=entries(mirror,main_commit)
        states[source]={"mirror":mirror,"refs":ref_list,"default_ref":default_ref,"commit":main_commit,"files":main_tree,"slug":rs}
        # Record every commit reachable from any fetched branch/tag/PR ref, then save its cleaned first-parent diff.
        commit_log,_,_=git(mirror,"log","--all","--format=%H%x09%P%x09%aI%x09%cI%x09%an%x09%s")
        source_commits=[]
        for line in commit_log.splitlines():
            bits=line.split("\t",5)
            if len(bits)<6: continue
            commit_sha,parent_shas,author_date,commit_date,author_name,subject=bits
            row={"repository":source,"commit_sha":commit_sha,"parent_shas":parent_shas,"author_date":author_date,"commit_date":commit_date,"author_name":author_name,"subject":subject}
            commit_rows.append(row); source_commits.append(row)
        empty_tree="4b825dc642cb6eb9a060e54bf8d69288fbee4904"
        for crow in source_commits:
            parents=crow["parent_shas"].split()
            parent=parents[0] if parents else empty_tree
            changes=diff_names(mirror,parent,crow["commit_sha"])
            safe_names=[]; omitted_names=[]
            for status,changed_path in changes:
                why=excluded(changed_path)
                if why:
                    exclusions.append({"repository":source,"ref":"commit:"+crow["commit_sha"],"path":changed_path,"reason":"HISTORICAL_"+why,"git_blob_sha":""})
                    omitted_names.append(changed_path); continue
                if not safe_path(changed_path):
                    exclusions.append({"repository":source,"ref":"commit:"+crow["commit_sha"],"path":changed_path,"reason":"HISTORICAL_UNSAFE_PATH","git_blob_sha":""})
                    omitted_names.append(changed_path); continue
                safe_names.append(changed_path)
            if not safe_names: continue
            patch=git(mirror,"diff","--binary","--no-ext-diff",parent,crow["commit_sha"],"--",*safe_names,binary=True,check=False)[0]
            if not patch: continue
            cooked,why=clean_bytes(patch,"historical_commit.patch")
            if cooked is None:
                exclusions.append({"repository":source,"ref":"commit:"+crow["commit_sha"],"path":"<historical-commit-patch>","reason":"SECRET_PATTERN_IN_HISTORICAL_PATCH","git_blob_sha":""})
                historical_patch_rows.append({"repository":source,"commit_sha":crow["commit_sha"],"parent_sha":parent,"changed_paths":len(changes),"captured_paths":0,"excluded_paths":len(omitted_names)+len(safe_names),"patch_sha256":"","packaged_path":"","status":"PATCH_EXCLUDED_BY_SECRET_SCANNER"})
                continue
            redactions+=len(why)
            psha=sha(cooked); patch_path=f"03_UNIQUE_FEATURES_AND_PATCHES/historical-commit-patches/{rs}/{psha}.patch"
            if not PKG.joinpath(*PurePosixPath(patch_path).parts).exists(): put(PKG,patch_path,cooked)
            historical_patch_rows.append({"repository":source,"commit_sha":crow["commit_sha"],"parent_sha":parent,"changed_paths":len(changes),"captured_paths":len(safe_names),"excluded_paths":len(omitted_names),"patch_sha256":psha,"packaged_path":patch_path,"status":"PATCH_CAPTURED"})
        nbranch=sum(x["ref_type"]=="branch" for x in ref_list); ntag=sum(x["ref_type"]=="tag" for x in ref_list); npr=sum(x["ref_type"]=="pull_request_ref" for x in ref_list)
        for r in ref_list:
            ref_rows.append({"repository":source,"ref_type":r["ref_type"],"ref":r["ref"],"commit_sha":r["commit_sha"],"commit_date":r["commit_date"],"subject":r["subject"],"is_default_ref":str(r["ref"]==default_ref).lower()})
        repo_rows.append({"repository":source,"status":"READABLE","default_ref":default_ref,"main_commit_sha":main_commit,"main_files":sum(v["type"]=="blob" for v in main_tree.values()),"branches":nbranch,"tags":ntag,"pull_refs":npr,"detail":""})

        # Primary source keeps its complete clean main snapshot. Alternative mains preserve unique paths and different content only.
        for path,e in main_tree.items():
            reason=excluded(path)
            if e["type"]!="blob":
                exclusions.append({"repository":source,"ref":default_ref,"path":path,"reason":"SUBMODULE_OR_NON_BLOB_POINTER","git_blob_sha":e["oid"]}); continue
            if reason:
                exclusions.append({"repository":source,"ref":default_ref,"path":path,"reason":reason,"git_blob_sha":e["oid"]}); continue
            rel=safe_path(path)
            if not rel:
                exclusions.append({"repository":source,"ref":default_ref,"path":path,"reason":"UNSAFE_PATH","git_blob_sha":e["oid"]}); continue
            raw=get_blob(mirror,e["oid"]); cooked,why=clean_bytes(raw,path)
            if cooked is None:
                exclusions.append({"repository":source,"ref":default_ref,"path":path,"reason":";".join(why),"git_blob_sha":e["oid"]}); continue
            redactions+=len(why)
            primary_entry=states.get(PRIMARY,{}).get("files",{}).get(path,{})
            is_exact_alt=(source!=PRIMARY and primary_entry.get("oid")==e["oid"])
            if source==PRIMARY:
                packaged=f"02_CANONICAL_PROJECT/primary/{rel}"
                put(PKG,packaged,cooked); main_payloads+=1
                decision="CANONICAL_PRIMARY_MAIN"
            elif is_exact_alt:
                packaged=f"02_CANONICAL_PROJECT/primary/{rel}"
                decision="EXACT_CONTENT_MATCH_TO_PRIMARY_MAIN"
                duplicates.append({"repository":source,"ref":default_ref,"path":path,"git_blob_sha":e["oid"],"sha256":sha(raw),"canonical_path":packaged,"decision":decision})
            else:
                packaged=f"03_UNIQUE_FEATURES_AND_PATCHES/alternative-main/{rs}/{rel}.source-{e['oid'][:12]}"
                put(PKG,packaged,cooked); variant_count+=1
                decision="ALTERNATIVE_MAIN_UNIQUE_PATH_OR_CONTENT"
            row={"repository":source,"ref":default_ref,"commit_sha":main_commit,"path":path,"git_blob_sha":e["oid"],"source_sha256":sha(raw),"packaged_sha256":sha(cooked),"size_bytes":len(cooked),"packaged_path":packaged,"classification":decision,"redactions":";".join(why)}
            main_rows.append(row)
            path_versions[path].append({"repository":source,"ref":default_ref,"git_blob_sha":e["oid"],"sha256":sha(raw),"packaged_path":packaged})
            if is_doc(path):
                dpath=f"04_UNIFIED_SPECIFICATIONS/source_documents/{sha(cooked)[:16]}/{PurePosixPath(path).name}"
                if not PKG.joinpath(*PurePosixPath(dpath).parts).exists(): put(PKG,dpath,cooked)
                docs.append({"repository":source,"ref":default_ref,"path":path,"source_sha256":sha(raw),"packaged_sha256":sha(cooked),"category":category(path),"packaged_path":dpath})
            if path.lower().endswith(".sql") and "migration" in path.lower():
                migrations.append({"repository":source,"ref":default_ref,"path":path,"git_blob_sha":e["oid"],"source_sha256":sha(raw),"packaged_path":packaged})
            if re.search(r"(^|/)(tests?|__tests__|e2e|fixtures?)(/|$)|\.(test|spec)\.|playwright|vitest|jest",path,re.I):
                tests.append({"repository":source,"ref":default_ref,"path":path,"git_blob_sha":e["oid"],"kind":"MAIN_TEST_OR_FIXTURE","packaged_path":packaged})

        seen_ref_versions={}
        for r in ref_list:
            ref,commit=r["ref"],r["commit_sha"]
            if commit==main_commit: continue
            changed=diff_names(mirror,main_commit,commit)
            ref_tree=entries(mirror,commit); changed_items=[]; count_added=0; omitted=0
            for status,path in changed:
                reason=excluded(path); ent=ref_tree.get(path)
                if reason:
                    exclusions.append({"repository":source,"ref":ref,"path":path,"reason":reason,"git_blob_sha":ent["oid"] if ent else ""}); omitted+=1; continue
                if not safe_path(path):
                    exclusions.append({"repository":source,"ref":ref,"path":path,"reason":"UNSAFE_PATH","git_blob_sha":ent["oid"] if ent else ""}); omitted+=1; continue
                if status=="D" or not ent:
                    variants.append({"repository":source,"ref":ref,"ref_type":r["ref_type"],"commit_sha":commit,"path":path,"status_vs_source_main":"DELETED","git_blob_sha":"","packaged_path":"","review_state":"DELETION_REVIEW_REQUIRED_NOT_APPLIED"})
                    changed_items.append((status,path,None)); continue
                if ent["type"]!="blob":
                    exclusions.append({"repository":source,"ref":ref,"path":path,"reason":"SUBMODULE_OR_NON_BLOB_POINTER","git_blob_sha":ent["oid"]}); omitted+=1; continue
                changed_items.append((status,path,ent))
                if ent["oid"]==main_tree.get(path,{}).get("oid"):
                    continue
                key=(path,ent["oid"])
                if key in seen_ref_versions:
                    prior=seen_ref_versions[key]
                    raw=get_blob(mirror,ent["oid"])
                    variants.append({"repository":source,"ref":ref,"ref_type":r["ref_type"],"commit_sha":commit,"path":path,"status_vs_source_main":status,"git_blob_sha":ent["oid"],"source_sha256":sha(raw),"packaged_sha256":prior["packaged_sha256"],"size_bytes":prior["size_bytes"],"packaged_path":prior["packaged_path"],"review_state":"EXACT_IDENTICAL_FILE_VERSION_REUSED"})
                    continue
                raw=get_blob(mirror,ent["oid"]); cooked,why=clean_bytes(raw,path)
                if cooked is None:
                    exclusions.append({"repository":source,"ref":ref,"path":path,"reason":";".join(why),"git_blob_sha":ent["oid"]}); omitted+=1; continue
                redactions+=len(why); count_added+=1
                vpath=f"03_UNIQUE_FEATURES_AND_PATCHES/ref-variants/{rs}/{slug(ref)}/{safe_path(path)}.source-{ent['oid'][:12]}"
                put(PKG,vpath,cooked); variant_count+=1
                seen_ref_versions[key]={"packaged_path":vpath,"packaged_sha256":sha(cooked),"size_bytes":len(cooked)}
                variants.append({"repository":source,"ref":ref,"ref_type":r["ref_type"],"commit_sha":commit,"path":path,"status_vs_source_main":status,"git_blob_sha":ent["oid"],"source_sha256":sha(raw),"packaged_sha256":sha(cooked),"size_bytes":len(cooked),"packaged_path":vpath,"redactions":";".join(why),"review_state":"REVIEW_REQUIRED_NOT_MERGED"})
                path_versions[path].append({"repository":source,"ref":ref,"git_blob_sha":ent["oid"],"sha256":sha(raw),"packaged_path":vpath})
                if is_doc(path):
                    dpath=f"04_UNIFIED_SPECIFICATIONS/source_documents/{sha(cooked)[:16]}/{PurePosixPath(path).name}"
                    if not PKG.joinpath(*PurePosixPath(dpath).parts).exists(): put(PKG,dpath,cooked)
                    docs.append({"repository":source,"ref":ref,"path":path,"source_sha256":sha(raw),"packaged_sha256":sha(cooked),"category":category(path),"packaged_path":dpath})
                if path.lower().endswith(".sql") and "migration" in path.lower():
                    migrations.append({"repository":source,"ref":ref,"path":path,"git_blob_sha":ent["oid"],"source_sha256":sha(raw),"packaged_path":vpath})
                if re.search(r"(^|/)(tests?|__tests__|e2e|fixtures?)(/|$)|\.(test|spec)\.|playwright|vitest|jest",path,re.I):
                    tests.append({"repository":source,"ref":ref,"path":path,"git_blob_sha":ent["oid"],"kind":"BRANCH_TEST_OR_FIXTURE","packaged_path":vpath})
            patch_path=""; patch_sha=""
            path_args=[p for _,p,e in changed_items if e is not None]
            if path_args:
                patch=git(mirror,"diff","--binary","--no-ext-diff",main_commit,commit,"--",*path_args,binary=True,check=False)[0]
                cooked,why=clean_bytes(patch,"source.patch")
                if cooked is not None and cooked:
                    redactions+=len(why); patch_sha=sha(cooked)
                    patch_path=f"03_UNIQUE_FEATURES_AND_PATCHES/patches/{rs}/{slug(ref)}/{patch_sha[:16]}.patch"
                    if not PKG.joinpath(*PurePosixPath(patch_path).parts).exists(): put(PKG,patch_path,cooked)
                elif patch:
                    exclusions.append({"repository":source,"ref":ref,"path":"<patch>","reason":"SECRET_PATTERN_IN_PATCH","git_blob_sha":""}); omitted+=len(path_args)
            variants.append({"repository":source,"ref":ref,"ref_type":r["ref_type"],"commit_sha":commit,"path":"<ref-summary>","status_vs_source_main":"REF_DIFF_SUMMARY","packaged_sha256":patch_sha,"packaged_path":patch_path,"review_state":f"CHANGED_PATHS={len(changed)};CAPTURED_NEW_VERSIONS={count_added};OMITTED={omitted};REVIEW_REQUIRED_NOT_MERGED"})

    # Read input Release assets, when they have actually been uploaded.
    inbox=WORK/"intake"; inbox.mkdir(parents=True,exist_ok=True)
    _,dlrc,dlerr=run(["gh","release","download",INTAKE_TAG,"--repo",TARGET,"--dir",str(inbox),"--pattern","*.zip","--clobber"],check=False)
    zip_inputs=sorted(inbox.glob("*.zip")) if dlrc==0 else []
    input_sources={}
    intake_duplicates=[]
    seen_input_hashes={}
    unique_zip_inputs=[]
    for zpath in zip_inputs:
        raw=zpath.read_bytes(); raw_sha=sha(raw)
        if raw_sha in seen_input_hashes:
            intake_duplicates.append({"sha256":raw_sha,"source_name":zpath.name,"kept_name":seen_input_hashes[raw_sha],"source":"github_release"})
            zpath.unlink()
            continue
        seen_input_hashes[raw_sha]=zpath.name
        input_sources[zpath.name]={"ingestion_source":"github_release_asset","original_name":zpath.name,"source_path":f"release:{INTAKE_TAG}"}
        unique_zip_inputs.append(zpath)
    zip_inputs=unique_zip_inputs
    intake_root=Path.cwd()/"incoming-archives/commerce-source-reconciliation"
    if intake_root.exists():
        for source_zip in sorted(intake_root.rglob("*.zip")):
            # Ignore a directory symlink and never scan the generated package scratch space.
            if source_zip.is_symlink() or not source_zip.is_file(): continue
            raw_sha=sha(source_zip.read_bytes())
            if raw_sha in seen_input_hashes:
                intake_duplicates.append({"sha256":raw_sha,"source_name":source_zip.name,"kept_name":seen_input_hashes[raw_sha],"source":"repository_folder"})
                continue
            dest=inbox/f"folder-{raw_sha[:12]}-{slug(source_zip.name)}"
            shutil.copy2(source_zip,dest)
            seen_input_hashes[raw_sha]=dest.name
            input_sources[dest.name]={"ingestion_source":"repository_folder","original_name":source_zip.name,"source_path":source_zip.relative_to(Path.cwd()).as_posix()}
            zip_inputs.append(dest)
    zip_inputs=sorted(zip_inputs)
    external_rows=[]; external_archives=[]; expanded_bytes=0; expanded_members=0
    def scan_zip(data, label, prefix, depth=0):
        nonlocal expanded_bytes,expanded_members,redactions
        if depth>4 or len(data)>650*1024*1024:
            external_rows.append({"source_archive":label,"member_path":"","status":"SKIPPED","reason":"ARCHIVE_SIZE_OR_DEPTH_LIMIT","sha256":sha(data),"bytes":len(data)})
            return False
        try: zf=zipfile.ZipFile(io.BytesIO(data))
        except Exception:
            external_rows.append({"source_archive":label,"member_path":"","status":"SKIPPED","reason":"INVALID_ZIP","sha256":sha(data),"bytes":len(data)})
            return False
        infos=zf.infolist()
        if len(infos)>250000:
            external_rows.append({"source_archive":label,"member_path":"","status":"SKIPPED","reason":"MEMBER_LIMIT","bytes":len(data)})
            return False
        safe_all=True
        for info in infos:
            if info.is_dir(): continue
            expanded_members+=1; expanded_bytes+=info.file_size
            if expanded_members>250000 or expanded_bytes>2*1024*1024*1024:
                external_rows.append({"source_archive":label,"member_path":info.filename,"status":"SKIPPED","reason":"TOTAL_UNPACK_LIMIT","bytes":info.file_size}); safe_all=False; break
            rel=safe_path(info.filename)
            if not rel:
                external_rows.append({"source_archive":label,"member_path":info.filename,"status":"SKIPPED","reason":"UNSAFE_PATH","bytes":info.file_size}); safe_all=False; continue
            reason=excluded(rel)
            if reason:
                external_rows.append({"source_archive":label,"member_path":rel,"status":"EXCLUDED","reason":reason,"bytes":info.file_size}); safe_all=False; continue
            try: raw=zf.read(info)
            except Exception:
                external_rows.append({"source_archive":label,"member_path":rel,"status":"SKIPPED","reason":"BAD_CRC_OR_READ_ERROR","bytes":info.file_size}); safe_all=False; continue
            if rel.lower().endswith(".zip"):
                ok=scan_zip(raw,label+"!"+rel,f"10_RECEIVED_EXTERNAL_ARCHIVES/extracted/{slug(label)}/{rel[:-4]}",depth+1)
                external_rows.append({"source_archive":label,"member_path":rel,"status":"NESTED_ZIP_SCANNED","reason":"" if ok else "RAW_NESTED_ARCHIVE_NOT_INCLUDED","sha256":sha(raw),"bytes":len(raw)})
                if ok: put(PKG,f"{prefix}/{rel}",raw)
                else: safe_all=False
            else:
                cooked,why=clean_bytes(raw,rel)
                if cooked is None:
                    external_rows.append({"source_archive":label,"member_path":rel,"status":"EXCLUDED","reason":";".join(why),"sha256":sha(raw),"bytes":len(raw)}); safe_all=False; continue
                if why: redactions+=len(why); safe_all=False
                out=f"{prefix}/{rel}"; put(PKG,out,cooked)
                external_rows.append({"source_archive":label,"member_path":rel,"status":"INCLUDED_SANITIZED" if why else "INCLUDED","reason":";".join(why),"sha256":sha(raw),"bytes":len(raw),"packaged_path":out,"packaged_sha256":sha(cooked)})
        return safe_all
    for zp in zip_inputs:
        raw=zp.read_bytes(); safe_all=scan_zip(raw,zp.name,f"10_RECEIVED_EXTERNAL_ARCHIVES/extracted/{slug(zp.stem)}")
        source_info=input_sources.get(zp.name,{})
        external_archives.append({"name":zp.name,"original_name":source_info.get("original_name",zp.name),"ingestion_source":source_info.get("ingestion_source","unknown"),"source_path":source_info.get("source_path",""),"sha256":sha(raw),"bytes":len(raw),"status":"EXTRACTED_WITH_SECURITY_FILTERS" if not safe_all else "EXTRACTED_AND_CONTENTS_SCANNED"})
    ready=len(zip_inputs)>=2
    package_name="AGHBARI_COMMERCE_UNIFIED_SOURCE_PACKAGE.zip" if ready else "AGHBARI_COMMERCE_GITHUB_BASELINE_SNAPSHOT.zip"

    # Create all auditable reports.
    headers_repo=["repository","status","default_ref","main_commit_sha","main_files","branches","tags","pull_refs","detail"]
    headers_ref=["repository","ref_type","ref","commit_sha","commit_date","subject","is_default_ref"]
    headers_file=["repository","ref","commit_sha","path","git_blob_sha","source_sha256","packaged_sha256","size_bytes","packaged_path","classification","redactions"]
    headers_var=["repository","ref","ref_type","commit_sha","path","status_vs_source_main","git_blob_sha","source_sha256","packaged_sha256","size_bytes","packaged_path","redactions","review_state"]
    headers_ex=["repository","ref","path","reason","git_blob_sha"]
    csvwrite(PKG/"01_SOURCE_INVENTORY/repositories.csv",headers_repo,repo_rows)
    csvwrite(PKG/"01_SOURCE_INVENTORY/refs.csv",headers_ref,ref_rows)
    csvwrite(PKG/"01_SOURCE_INVENTORY/commits.csv",["repository","commit_sha","parent_shas","author_date","commit_date","author_name","subject"],commit_rows)
    csvwrite(PKG/"01_SOURCE_INVENTORY/pull_requests.csv",["repository","number","title","state","is_draft","url","head_ref","head_sha","base_ref","base_sha","created_at","updated_at","merged_at","record_status","detail"],pull_request_rows)
    csvwrite(PKG/"01_SOURCE_INVENTORY/historical_commit_patches.csv",["repository","commit_sha","parent_sha","changed_paths","captured_paths","excluded_paths","patch_sha256","packaged_path","status"],historical_patch_rows)
    csvwrite(PKG/"01_SOURCE_INVENTORY/main_files.csv",headers_file,main_rows)
    csvwrite(PKG/"01_SOURCE_INVENTORY/branch_variants_and_ref_diffs.csv",headers_var,variants)
    csvwrite(PKG/"01_SOURCE_INVENTORY/excluded_files.csv",headers_ex,exclusions)
    csvwrite(PKG/"01_SOURCE_INVENTORY/duplicate_content_groups.csv",["repository","ref","path","git_blob_sha","sha256","canonical_path","decision"],duplicates)
    conflict_rows=[]
    for path,items in path_versions.items():
        distinct={x["sha256"] for x in items}
        if len(distinct)>1:
            for x in items:
                conflict_rows.append({"path":path,"repository":x["repository"],"ref":x["ref"],"git_blob_sha":x["git_blob_sha"],"sha256":x["sha256"],"distinct_versions":len(distinct),"decision":"PRESERVE_ALL_REVIEW_BEFORE_MERGE"})
    csvwrite(PKG/"07_DECISIONS_AND_CONFLICTS/cross_source_path_conflicts.csv",["path","repository","ref","git_blob_sha","sha256","distinct_versions","decision"],conflict_rows)
    csvwrite(PKG/"04_UNIFIED_SPECIFICATIONS/spec_documents.csv",["repository","ref","path","source_sha256","packaged_sha256","category","packaged_path"],docs)
    csvwrite(PKG/"05_DATABASE_AND_INTEGRATIONS/migration_inventory.csv",["repository","ref","path","git_blob_sha","source_sha256","packaged_path"],migrations)
    csvwrite(PKG/"06_TESTS_AND_QUALITY/test_inventory.csv",["repository","ref","path","git_blob_sha","kind","packaged_path"],tests)
    csvwrite(PKG/"01_SOURCE_INVENTORY/external_archive_inventory.csv",["name","original_name","ingestion_source","source_path","sha256","bytes","status"],external_archives)
    csvwrite(PKG/"01_SOURCE_INVENTORY/external_archive_duplicates.csv",["sha256","source_name","kept_name","source"],intake_duplicates)
    csvwrite(PKG/"01_SOURCE_INVENTORY/external_archive_members.csv",["source_archive","member_path","status","reason","sha256","bytes","packaged_path","packaged_sha256"],external_rows)
    missing=[
      {"input":"AGHBARI_COMMERCE_UNIFIED_SOURCE_PACKAGE.zip","status":"RECEIVED" if any(x["name"].lower()=="aghbari_commerce_unified_source_package.zip" for x in external_archives) else "MISSING","evidence":"The intake README records the older link as HTTP 410 Gone; reattach the archive to the intake Release if it is needed."},
      {"input":"Archive containing seven projects","status":"RECEIVED" if len(zip_inputs)>=2 else "PENDING","evidence":f"ZIP attachments downloaded from Release {INTAKE_TAG}: {len(zip_inputs)}."},
      {"input":"Additional multi-project archive","status":"RECEIVED" if len(zip_inputs)>=2 else "PENDING","evidence":f"ZIP attachments downloaded from Release {INTAKE_TAG}: {len(zip_inputs)}."},
      {"input":"Other platform exports not available in GitHub/Lovable","status":"PARTIAL","evidence":"Lovable project code matched the repository main SHA; no separate Bolt export was available in the intake Release."},
    ]
    csvwrite(PKG/"09_REQUIRED_FOLLOW_UP/missing_inputs.csv",["input","status","evidence"],missing)
    readable=sum(x["status"]=="READABLE" for x in repo_rows); empty=sum(x["status"]=="EMPTY" for x in repo_rows); unavailable=sum(x["status"]=="UNAVAILABLE" for x in repo_rows)
    branches=sum(x["ref_type"]=="branch" for x in ref_rows); tags=sum(x["ref_type"]=="tag" for x in ref_rows); pullrefs=sum(x["ref_type"]=="pull_request_ref" for x in ref_rows)
    note=f"""# حزمة مصادر متجر الأغبري

الحالة: {"حزمة تشمل الأرشيفات المرفوعة في Release؛ راجع سجل الاستبعادات والتعارضات قبل الاعتماد النهائي." if ready else "لقطة أساس من GitHub وليست الحزمة النهائية: لم يُستلم بعد ملفان ZIP خارجيان على الأقل."}

- المستودعات المعرفة في إعداد الفحص: {len(SOURCES)}؛ مقروءة {readable}؛ فارغة {empty}؛ غير متاحة {unavailable}.
- الفروع {branches}؛ الوسوم {tags}؛ مراجع PR {pullrefs}.
- ملفات جرد main {len(main_rows)}؛ ملفات محتوى فريدة أضيفت للمقارنة والفروع {variant_count}؛ الملفات المدرجة فعليًا في canonical main {main_payloads}.
- عمليات تنقيح الأسرار {redactions}؛ سجلات الاستبعاد {len(exclusions)}؛ مسارات ذات محتوى متعارض {len({x['path'] for x in conflict_rows})}.
- ZIP الإدخال المستلمة من {INTAKE_TAG}: {len(zip_inputs)}.
- المرشح الأساسي هو {PRIMARY}؛ اختيار مرشح للمقارنة وليس دليل اكتمال منتج أو إنتاج.
- الملفات المطابقة تمامًا للمرشح الأساسي لا تُكرر؛ كل مصدر ومسار وبصمة وقرار إدراج موثق في الجرد. الفروع والمحتوى المختلف محفوظ في ملفات وpatches لا تُدمج تلقائيًا.
- لم تُشغّل اختبارات أو عمليات بناء للمشاريع المصدرية. ملف test_inventory.csv يسرد الملفات فقط، ولا يثبت نجاح الاختبارات.
- تُستبعد المسارات الحساسة وتُنقّح قيم الأسرار المطابقة للأنماط إلى {MARK}. أرشيفات الإدخال الأصلية تبقى في Release الإدخال، ويحتوي ZIP على ملفات مستخرجة بعد فحص الأمان.
- افحص 01_SOURCE_INVENTORY و07_DECISIONS_AND_CONFLICTS و09_REQUIRED_FOLLOW_UP قبل اتخاذ قرارات الدمج أو الترحيلات.
"""
    put(PKG,"00_README/README_AR.md",note)
    decisions="""# قرارات التعارض والمصالحة

1. لا دمج أو دفع لأي تغيير إلى مستودعات المصدر؛ هذه حزمة تدقيق وتجميع فقط.
2. جرى اختيار المستودع الأحدث الذي يطابق كود Lovable بوصفه مرشحًا أساسيًا، لا بوصفه نسخة مضمونة الاكتمال.
3. النسخ غير المطابقة محفوظة كملفات بديلة أو نسخ فروع/رقع. راجع ملفات CSV قبل اختيار مكون للدمج.
4. عمليات الحذف في فرع آخر موثقة ولا تُنفذ على المرشح الأساسي.
5. الترابط بين SQL migrations يجب مراجعته قبل تطبيقها؛ اختلاف الترقيم/المحتوى لا يعني أن تطبيقها بالتسلسل آمن.
6. لا يوجد ادعاء PASS للبناء أو المتصفح أو الإنتاج. التحقق أدناه خاص بسلامة ZIP والبصمات فقط.
"""
    put(PKG,"07_DECISIONS_AND_CONFLICTS/README_AR.md",decisions)
    put(PKG,"06_TESTS_AND_QUALITY/TEST_EXECUTION_STATUS.md",f"# حالة الاختبارات\nعدد مسارات الاختبارات والfixtures المفهرسة: {len(tests)}. لم تشغل هذه العملية build أو test أو browser E2E على مصادر المشروع. يلزم تشغيل كل أمر على SHA محدد وتوثيق النتيجة قبل إدعاء النجاح.\n".encode())
    put(PKG,"09_REQUIRED_FOLLOW_UP/NEXT_STEPS_AR.md",("""# المطلوب لاستكمال الحزمة النهائية
- ارفع أرشيف المشاريع السبعة والأرشيف متعدد المشاريع كمرفقين إلى Release بالوسم commerce-source-intake-2026-10-16 ثم انشر الإصدار؛ هذا يعيد تشغيل الجمع.
- أعد إرفاق AGHBARI_COMMERCE_UNIFIED_SOURCE_PACKAGE.zip إذا كانت النسخة القديمة مطلوبة؛ الرابط القديم مذكور على أنه 410 Gone.
- راجع missing_inputs.csv وexternal_archive_members.csv، لأن المحتوى الحساس يُحجب ولا يضاف خامًا إلى ZIP.
- راجع ترحيلات SQL والعقود بين المشاريع قبل أي تطبيق أو دمج.
- شغّل build/unit/database/E2E لكل مصدر مرشح في بيئة معزولة وسجّل SHA والأوامر والنتيجة.
""").encode())

    # Export inventory CSVs to the requested repository folder; ZIP itself belongs in a Release asset.
    REPORT.mkdir(parents=True,exist_ok=True)
    for name,src in {
      "repositories.csv":"01_SOURCE_INVENTORY/repositories.csv",
      "refs.csv":"01_SOURCE_INVENTORY/refs.csv",
      "main_files.csv":"01_SOURCE_INVENTORY/main_files.csv",
      "branch_variants_and_ref_diffs.csv":"01_SOURCE_INVENTORY/branch_variants_and_ref_diffs.csv",
      "excluded_files.csv":"01_SOURCE_INVENTORY/excluded_files.csv",
      "duplicate_content_groups.csv":"01_SOURCE_INVENTORY/duplicate_content_groups.csv",
      "external_archive_inventory.csv":"01_SOURCE_INVENTORY/external_archive_inventory.csv",
      "external_archive_members.csv":"01_SOURCE_INVENTORY/external_archive_members.csv",
      "commits.csv":"01_SOURCE_INVENTORY/commits.csv",
      "pull_requests.csv":"01_SOURCE_INVENTORY/pull_requests.csv",
      "historical_commit_patches.csv":"01_SOURCE_INVENTORY/historical_commit_patches.csv",
      "cross_source_path_conflicts.csv":"07_DECISIONS_AND_CONFLICTS/cross_source_path_conflicts.csv",
      "spec_documents.csv":"04_UNIFIED_SPECIFICATIONS/spec_documents.csv",
      "migration_inventory.csv":"05_DATABASE_AND_INTEGRATIONS/migration_inventory.csv",
      "test_inventory.csv":"06_TESTS_AND_QUALITY/test_inventory.csv",
      "missing_inputs.csv":"09_REQUIRED_FOLLOW_UP/missing_inputs.csv",
    }.items(): shutil.copy2(PKG/src,REPORT/name)

    # This in-package manifest records the exact validation contract; actual result is written outside the ZIP after verification.
    put(PKG,"08_PROVENANCE_AND_CHECKSUMS/ZIP_VALIDATION.json",json.dumps({
      "scope":"ZIP integrity, entry uniqueness, independent extraction and SHA-256/size verification for all listed package payloads",
      "execution_timing":"after archive creation",
      "actual_result_location":"Actions run summary and adjacent package-result.json (not recursively included in the ZIP)",
      "source_build_tests":"NOT_RUN_BY_THIS_AUDIT",
      "no_source_repositories_modified":True
    },ensure_ascii=False,indent=2).encode())

    # Write package inventory, checksums and manifest before final zip.
    def package_files():
        rows=[]
        for f in sorted(PKG.rglob("*")):
            if f.is_file() and f.name not in {"SHA256SUMS.txt","package_file_checksums.csv"}:
                b=f.read_bytes(); rows.append({"package_path":f.relative_to(PKG).as_posix(),"sha256":sha(b),"size_bytes":len(b)})
        return rows
    manifest={
      "created_utc":datetime.now(timezone.utc).isoformat(),"target_repository":TARGET,"intake_release_tag":INTAKE_TAG,
      "package_name":package_name,"package_type":"UNIFIED_SOURCE_PACKAGE" if ready else "GITHUB_BASELINE_SNAPSHOT",
      "sources":repo_rows,"ref_counts":{"branches":branches,"tags":tags,"pull_request_refs":pullrefs},
      "main_file_records":len(main_rows),"canonical_primary_files":main_payloads,"unique_variants_added":variant_count,
      "reachable_commits":len(commit_rows),"pull_requests_records":len(pull_request_rows),"historical_commit_patch_records":len(historical_patch_rows),
      "branch_variant_and_ref_diff_records":len(variants),"excluded_records":len(exclusions),"redaction_operations":redactions,"external_zip_assets":external_archives,
      "exact_duplicate_records":len(duplicates),"duplicate_input_archives":len(intake_duplicates),"cross_source_conflict_paths":len({x["path"] for x in conflict_rows}),
      "source_changes":"NONE; source repositories only read","source_build_tests":"NOT_RUN_BY_THIS_AUDIT"
    }
    put(PKG,"08_PROVENANCE_AND_CHECKSUMS/package_manifest.json",json.dumps(manifest,ensure_ascii=False,indent=2).encode())
    inv=package_files()
    csvwrite(PKG/"08_PROVENANCE_AND_CHECKSUMS/package_file_checksums.csv",["package_path","sha256","size_bytes"],inv)
    sums=[]
    for f in sorted(PKG.rglob("*")):
        if f.is_file() and f.name!="SHA256SUMS.txt": sums.append(f"{sha(f.read_bytes())}  {f.relative_to(PKG).as_posix()}")
    put(PKG,"08_PROVENANCE_AND_CHECKSUMS/SHA256SUMS.txt",("\n".join(sums)+"\n").encode())

    DIST.mkdir(parents=True,exist_ok=True); zip_path=DIST/package_name
    if zip_path.exists(): zip_path.unlink()
    with zipfile.ZipFile(zip_path,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        for f in sorted(PKG.rglob("*")):
            if f.is_file(): z.write(f,f.relative_to(PKG).as_posix())
    with zipfile.ZipFile(zip_path,"r") as z:
        bad=z.testzip()
        if bad: raise RuntimeError("ZIP CRC verification failed: "+bad)
        names=z.namelist()
        if len(names)!=len(set(names)): raise RuntimeError("duplicate ZIP entry path found")
        with tempfile.TemporaryDirectory(prefix="commerce-package-check-") as td:
            z.extractall(td)
            for row in inv:
                f=Path(td).joinpath(*PurePosixPath(row["package_path"]).parts)
                if not f.is_file() or f.stat().st_size!=row["size_bytes"] or sha(f.read_bytes())!=row["sha256"]:
                    raise RuntimeError("extracted file SHA/size mismatch: "+row["package_path"])
    package_sha=sha(zip_path.read_bytes())
    result={
      "status":"ZIP_VERIFIED","package_name":package_name,"package_sha256":package_sha,"package_bytes":zip_path.stat().st_size,
      "zip_testzip":"PASS","duplicate_zip_entries":0,"reextract_hash_check":"PASS",
      "repositories_configured":len(SOURCES),"repositories_readable":readable,"repositories_empty":empty,"repositories_unavailable":unavailable,
      "branches":branches,"tags":tags,"pull_request_refs":pullrefs,"main_file_records":len(main_rows),"primary_files":main_payloads,
      "reachable_commits":len(commit_rows),"pull_request_records":len(pull_request_rows),"historical_commit_patch_records":len(historical_patch_rows),
      "unique_variant_files_added":variant_count,"file_variant_and_ref_summary_rows":len(variants),"exact_duplicate_records":len(duplicates),
      "cross_source_conflict_paths":len({x["path"] for x in conflict_rows}),"exclusions":len(exclusions),"redactions":redactions,
      "external_zip_assets":len(zip_inputs),"duplicate_input_archives":len(intake_duplicates),"final_package_gate":ready,
      "note":"PASS is limited to ZIP integrity and SHA verification; source builds, tests, browser and production were not tested."
    }
    put(REPORT,"package-result.json",json.dumps(result,ensure_ascii=False,indent=2).encode())
    put(REPORT,"package-sha256.txt",f"{package_sha}  {package_name}\n".encode())
    put(REPORT,"audit-summary.md",note.encode())
    (DIST/"package-name.txt").write_text(package_name,encoding="utf-8")
    (DIST/"package-sha256.txt").write_text(f"{package_sha}  {package_name}\n",encoding="utf-8")
    (DIST/"package-result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    release_notes=note+f"\n\nZIP SHA-256: {package_sha}\nZIP bytes: {zip_path.stat().st_size}\nArchive integrity: PASS (CRC + independent extraction + payload hash checks).\n"
    (DIST/"release-notes.md").write_text(release_notes,encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))

if __name__=="__main__": main()
