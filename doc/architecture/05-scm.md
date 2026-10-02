# L2: Source control (SCM)

Each Part has an SCM object (`scm_type=`, default `null_t('#')`) and optionally an extern SCM object (`extern=`) that holds only its part file. `part_manager.UpdateOnDisk()` asks every SCM object whether it needs to update, queues the ones that do, runs them with SCons' job runner, and records the result in the `scm` data cache.

## UpdateOnDisk

```mermaid
flowchart TD
    A["UpdateOnDisk(part_set)"] --> C["_get_scm_update_tasks"]
    C --> B["_get_scm_extern_tasks first:<br/>each Part's extern SCM,<br/>first one per SCM_EXTERN_DIR only"]
    B --> QE{"extern:<br/>NeedsToUpdate()?"}
    QE -->|"yes"| PL["parallel list<br/>(externs skip the AllowParallelAction test)"]
    C --> QP{"main SCM:<br/>NeedsToUpdate()?"}
    QP -->|"yes, AllowParallelAction()"| PL
    QP -->|"yes, otherwise"| SL["serial list<br/>(always empty: AllowParallelAction<br/>is always true)"]
    QP -->|"no, and no cache file"| PPO["post-processed anyway"]
    B --> MQ{"NeedsToUpdateMirror()?<br/>(git only, with use_cache= or USE_SCM_CACHE,<br/>a separate test, but under the default<br/>--update-mirror it can call NeedsToUpdate)"}
    C --> MQ
    MQ -->|"yes"| ML["mirror list"]
    ML --> R1["1. mirror jobs, scm_jobs or -j"]
    PL --> R2
    SL --> R3
    R1 --> R2["2. parallel list: externs and part sources together,<br/>scm_jobs or -j"]
    R2 --> R3["3. serial list, also run with scm_jobs or -j"]:::hot
    R3 --> PP["finally: PostProcess() for each SCM queued<br/>for update, plus each main SCM<br/>missing its cache file"]
    PPO --> PP
    PP --> SC["datacache.SaveCache(key='scm')"]
    classDef hot stroke:#dc2626,stroke-width:3px
```

- Externs (part files) and the Parts' own sources share one parallel list. Externs are queued first, but nothing makes them finish before the source checkouts start.
- The serial list is passed to `do_disk_update()` with the same job count as the parallel list, so an SCM that disallows parallel actions would not be serialized when `scm_jobs` or `-j` is above 1. Today the list is always empty: `base.AllowParallelAction()` returns `True` (its comment says to read a policy later), no SCM class overrides it, and `ScmReuse.AllowParallelAction()` returns `self._scm.AllowParallelAction`, the bound method, without calling it. A bound method is always truthy, so a reusing Part would keep answering yes even once the base answer can be `False`.
- A git extern stores its cache entry as `extern<SHORT_REQUEST_HASH>`, but the failed-run check at the end of `NeedsToUpdate()` reads the entry named after the Part's alias (`env['ALIAS']`). So an extern's own `completed == False` is never read back; the extern sees its Part's main entry instead. Only that fallback is affected: `do_check_logic()` reads the right entry, so a missing or mismatched extern checkout, or `--update`, still updates it.
- `completed == False` is also rarely written. In `scm/update_task.py`, `failed()` reports the error and stops the taskmaster but never sets the task's failure flag; only `exception_set()` does, and `postprocess()` passes `not failed` to `ProcessResult()`. So when `UpdateOnDisk()` returns non-zero (the ordinary failure path), git's `PostProcess()` still records `completed: True` with the requested server, branch, and revision, and the recorded-failure force-update fires only when an exception escapes the task. Under the default `--update=__auto__` and `--scm-logic=check`, a Part that names its branch, tag, or revision then finds a matching entry on the next run and is retried only if the existence check fails.
- `task_master.append()` also dedupes by `CheckOutDir` within one list. All `null_t` Parts share the SConstruct directory as `CheckOutDir`.
- `ScmReuse` resolves the referenced Part by alias and forwards every SCM call to that Part's SCM object. Used as `extern=`, every reusing Part resolves `SCM_EXTERN_DIR` to the same `#_extern//`, so only the first is checked.
- There is no sparse checkout, and nothing in `scm/` asks for a partial clone (`--filter`); the clone command does substitute `${GIT_CLONE_ARGS}`. A checkout is a full working tree even when only the part file is needed.

## The update decision

`scm/base.py NeedsToUpdate()` caches its answer per SCM object for the run.

```mermaid
flowchart TD
    A["NeedsToUpdate()"] --> C{"do_update_check()<br/>custom subclass check"}
    C -->|"true"| YES["update"]
    C -->|"false"| U{"--update value"}
    U -->|"__auto__ (default)"| L{"--scm-logic"}
    U -->|"a target list"| TM["_has_target_match:<br/>throwaway PartRef, before any read"]
    U -->|"true"| YES
    TM -->|"match"| YES
    L -->|"exists"| EX["do_exist_logic<br/>checkout and part file present?"]
    L -->|"check (default)"| CK["do_check_logic<br/>exist, then compare scm cache:<br/>server, revision or branch"]
    L -->|"force"| FO["do_force_logic<br/>exist, then compare git on disk"]
    L -->|"none"| NO["no update<br/>a missing checkout stays missing"]
    CK -->|"cache missing or mismatch"| FO
    EX --> POL
    CK --> POL
    FO --> POL{"reason returned?<br/>apply --scm-policy"}
    POL -->|"message-update (default),<br/>warning-update, update"| MOD{"local modifications and<br/>not SCM_IGNORE_MODIFIED?"}
    POL -->|"warning"| W1["no update, warning"]
    POL -->|"error"| W2["no update, error:<br/>the build stops"]
    POL -->|"checkout-warning,<br/>checkout-error"| CO{"checkout present?<br/>(do_exist_logic)"}
    CO -->|"missing"| COM["no update, verbose message only:<br/>the policy never clones the missing checkout"]:::hot
    CO -->|"present but stale"| COS["no update, warning<br/>(checkout-error: error, the build stops)"]
    MOD -->|"no"| YES
    MOD -->|"yes"| ERR["error: use --update to force"]
    A -.->|"always"| CMP["scm cache entry named ALIAS<br/>with completed == False forces update<br/>(an extern reads its Part's main entry)"]
    classDef hot stroke:#dc2626,stroke-width:3px
```

With the defaults (`--update=__auto__`, `--scm-logic=check`, `--scm-policy=message-update`), a missing checkout is cloned. A cached server, revision, or branch that differs from the request only sends `do_check_logic` on to `do_force_logic`, so a clean checkout is updated only if the checkout on disk differs too. The local-modification check runs only on the three policy branches that update. A custom `do_update_check()`, `--update=true`, and a target-list match go straight to update; the git update itself then refuses local modifications unless `--scm-clean` or `SCM_IGNORE_MODIFIED` is set.

The `checkout-warning` and `checkout-error` policies stay quiet about a missing checkout (`do_exist_logic()` returns a reason, and the branch only logs it at verbose level) and report a present-but-stale one. Neither variant clones a missing checkout: every policy except the three updating ones leaves the answer `False`, and under `--update=__auto__` only a recorded `completed == False` from a failed earlier run still forces an update (which, as noted above, is rarely recorded). The option help lists the values without saying what they do, and the branch structure goes back to the repository's first commit (2015); the names suggest "check out if missing, then warn", so confirm the intent before relying on either reading.

## Git: checkout, update, and patches

`scm/git.py` class `git`. `CheckOutAction` clones; `UpdateAction` brings an existing checkout to the request. Patches come from `patchfile=` (one file or a list) and are applied with `git am`, in list order.

```mermaid
stateDiagram-v2
    [*] --> Missing
    Missing --> Cloned: CheckOutAction clone, checkout revision
    Cloned --> Patched: git am each patch
    Cloned --> Ready: no patchfile
    Patched --> Ready
    Ready --> Updating: NeedsToUpdate true
    Updating --> Cleaning: scm-clean option
    Cleaning --> Repositioned: clean -dfx and reset --hard
    Updating --> Repositioned: server changed, set-url, fetch, reset or checkout
    Updating --> Repositioned: branch changed, fetch, checkout
    Updating --> Repositioned: on a branch, git pull, patched or not
    Updating --> Ready: on the requested tag, nothing to do
    Repositioned --> Patched: patchfile set, git am again on the new HEAD
    Repositioned --> Ready: no patchfile
```

- On a branch, an update runs `git pull` even when patches are applied, and then runs `git am` for every patch again on top of the result. The earlier patch commits are still in HEAD at that point, so `git am` is asked to apply patches that are already applied.
- A failed `git am` leaves `.git/rebase-apply` behind. Neither `clean -dfx` nor `reset --hard` removes it, and `UpdateAction` does not end it, so later `git am` runs refuse until someone runs `git am --abort` in the checkout.
- `GetGitData()` (`env.GitInfo()`) runs `git status -s -b`, `git tag --points-at`, `git rev-parse HEAD`, and `git remote -v` on every call. The git SCM object caches the result in `_disk_data` through `get_git_data()` until `PostProcess()` resets it; the lazy `env['SCM']` values (`TAGS`, `BRANCH`, `REVISION`, ...) and the update checks read through that accessor. When a `patchfile` is set, the tag lookup uses `HEAD^` instead of `HEAD`, which is the checked-out revision only when the patches added exactly one commit. `GitVersionFromTag` reads these tags.
- `PostProcess()` writes `{server, branch, revision, completed}` through `datacache.StoreData(..., key='scm')`, which lands in `.parts.cache/scm/<name>.cache`. This cache is not under the run key, so it survives a re-key. The patch list is not recorded, so a changed patch list is not detected.
- The extern `REQUEST_HASH` is an md5 of server, repository, and branch or revision. Two Parts with the same extern but different patches share one checkout.

## Read-time consequences

The checkout must exist before a part file is read ([03-part-loading.md](03-part-loading.md#reading-a-part-file)). That is why `UpdateOnDisk()` runs for every declared Part before any `LoadPart()`.
