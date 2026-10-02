# L0: Overview

Parts extends SCons without wrapping it. A user runs `scons`. SCons reads the SConstruct. The SConstruct does `from parts import *`, and that import installs Parts: it patches SCons internals, loads site extensions, and builds the default environment. The SConstruct then declares Parts. When SCons is about to build, a patched hook hands control to the Parts engine, which checks out sources, reads part files, resolves dependencies, and defines the build nodes. SCons then builds as usual.

## System context

```mermaid
flowchart LR
    U["scons TARGETS<br/>--cfg --tc --target --update"] --> SC["SCons<br/>Script.Main"]
    SC --> ST["SConstruct<br/>Part() declarations"]
    ST -->|"from parts import *"| P["scons-parts<br/>src/parts"]
    CFG["parts.cfg<br/>KEY = value"] --> P
    SITE["parts-site dirs<br/>pieces/ toolchain/<br/>configurations/ tools/"] --> P
    P -->|"monkeypatch at import"| SC
    P -->|"UpdateOnDisk"| REPO["SCM repositories<br/>git, svn, extern"]
    REPO --> PF["part files<br/>.part .parts"]
    PF -->|"ReadFile via SConscript"| P
    P -->|"nodes, builders, aliases"| SC
    SC --> OUT["_build/ _sdk/ _install/<br/>packages such as RPM"]
    P --> CACHE[".parts.cache/<br/>scm state, exports.jsn"]
```

In a large build the SConstruct can hold hundreds of `Part()` calls, part files often come from a separate repository through `extern=`, and the pieces, toolchains, and configurations live in a shared parts-site.

## Process lifecycle

```mermaid
sequenceDiagram
    autonumber
    participant S as SCons Main
    participant C as SConstruct
    participant M as parts/main.py
    participant E as glb.engine
    participant PM as part_manager
    participant T as SCons Taskmaster
    S->>C: read SConstruct
    C->>M: from parts import *
    M->>M: import parts.overrides (patch SCons)
    M->>E: engine.parts_addon() (reporter setup)
    M->>M: import parts.pieces (site and built-in pieces run)
    M->>E: Start()
    Note over E: post_option_setup adds --target<br/>_setup_arguments writes ARGUMENTS<br/>DefaultEnvironment() builds env 1<br/>part_manager created<br/>pre_load_queue runs
    M-->>C: globals().update(glb.globals)
    C->>PM: Part(...) for each root Part (declared, not read)
    S->>E: patched _build_targets calls Process()
    E->>E: generate_cache_key, SConstructLoadedEvent
    E->>PM: ProcessParts()
    Note over PM: UpdateOnDisk (checkout)<br/>LoadPart for every root (read part files)<br/>map targets to sections<br/>closure, toposort, ProcessSection<br/>map_scons_target_list
    E->>E: parts_process_queue, PostProcessEvent
    E-->>S: return
    S->>T: original _build_targets (build)
    S->>E: atexit ShutDown (failure summary)
```

Notes:

- `engine.Process()` returns early when `BUILD_TARGETS` is empty, so `scons` with no target reads no part file. Use `scons all`.
- The default target is cleared in `Start()` (`def_env.Default('')`), so nothing builds without a target.
- With `extract_sources` as the only target, `ProcessParts()` returns after `UpdateOnDisk()` without reading any part file; `engine.Process()` still runs the post-process queue and `PostProcessEvent`.
- Details of each step are in [01-startup.md](01-startup.md) and [03-part-loading.md](03-part-loading.md).

## Module map

```mermaid
flowchart TB
    subgraph entry["Entry and globals"]
        MAIN["main.py"]
        GLB["glb.py<br/>engine, pnodes, rpter"]
        ENG["engine.py<br/>Start, Process, ShutDown, cache key"]
    end
    subgraph opts["Options, variables, settings"]
        POPT["poptions.py<br/>AddOption, SetOptionDefault"]
        VARS["Variables/<br/>merge Default, cfg, ARGUMENTS"]
        SET["settings.py<br/>env cache, BasicEnvironment"]
        PLAT["platform_info.py<br/>SystemPlatform"]
    end
    subgraph tooling["Tools and configuration"]
        TM["tool_mapping.py<br/>ToolChain()"]
        TC["toolchain/*.py<br/>resolve(env, version)"]
        TOOLS["tools/*.py<br/>SCons tool overlay"]
        CONF["config.py<br/>Configuration(), merge"]
        CONFS["configurations/LEVEL/TOOL.py"]
    end
    subgraph graph1["Part graph"]
        PMGR["part_manager.py<br/>ProcessParts, UpdateOnDisk, _from_target"]
        PNODE["pnode/<br/>Part, Section, pnode_manager"]
        META["metasection/<br/>build, unit_test phases"]
        DEP["dependson.py, part_ref.py,<br/>dependent_ref.py, target_type.py"]
        REQ["requirement.py, api/requirement.py"]
    end
    subgraph outputs["Outputs"]
        SDK["sdk.py, exportitem.py,<br/>installs.py, packaging.py"]
        PIECES["pieces/<br/>cmake, automake, rpm, unit_test, ..."]
        BLD["core/builders/<br/>ccopy, exports, pkgconfig"]
    end
    SCM["scm/ vcs/<br/>git, svn, null, reuse"]
    OVR["overrides/<br/>SCons monkeypatches"]
    INFRA["reporter.py, api/output.py,<br/>datacache.py, mappers.py, part_logger.py"]
    MAIN --> OVR
    MAIN --> ENG
    ENG --> SET
    SET --> VARS
    SET --> TM
    TM --> TC
    TM --> TOOLS
    SET --> CONF
    CONF --> CONFS
    ENG --> PMGR
    PMGR --> PNODE
    PMGR --> SCM
    PNODE --> META
    PNODE --> DEP
    DEP --> REQ
    META --> SDK
    SDK --> BLD
    PIECES --> SDK
```

Parts-specific behavior is spread across four kinds of extension point, all searched on the site path ([01-startup.md](01-startup.md#site-search-path)):

| Extension | Directory | Loaded | Contract |
| --- | --- | --- | --- |
| Piece | `pieces/` | Every file, at `import parts`, before the engine starts | Module body runs. Registers methods, variables, options, platforms, queue hooks |
| Toolchain | `toolchain/` | By name, when an environment applies its toolchain | `resolve(env, version)` returns a list of `(name, config)` |
| Configuration | `configurations/<level>/` | By tool, host, and target, when an environment applies its configuration | `config.VersionRange()` rules |
| Tool | `tools/` (and SCons tool path) | By name, from a resolved toolchain | SCons tool `generate(env)` and `exists(env)` |
