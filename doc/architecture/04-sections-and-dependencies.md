# L2: Sections and dependencies

A Part owns one Section per section type it uses (`build`, `unit_test`). A Section is the unit of dependency: `DependsOn()` records which Sections of which Parts this one needs and which requirements (include paths, libraries, and so on) to take from them. Requirements flow through each Section's **export table**.

## Objects

```mermaid
flowchart LR
    P["pnode.part.Part<br/>alias, name, version, env"] -->|"1 to many"| S["pnode.section.Section<br/>ID SECTION::ALIAS, env clone,<br/>Exports, Depends"]
    S --> MS["MetaSection instance<br/>Build or UnitTest<br/>phase callbacks"]
    SD["SectionDefinition<br/>glb.section_definitions<br/>phases, target mapping logic"] --> MS
    S -->|"Depends: list"| DR["dependent_ref<br/>section name, requirements,<br/>optional flag"]
    DR --> PR["PartRef<br/>target_type, local space"]
    PR -->|"Matches, cached once non-empty"| P2["matched Part"]
    DR -->|"Section property"| S2["matched Part's Section"]
    DR --> RQ["REQ set<br/>requirement objects"]
    S2 -->|"Exports table"| S
```

Section types registered with `api.register.add_section()`:

| Type | Concepts (target prefixes) | Phases, in order | Targets map by |
| --- | --- | --- | --- |
| `build` (`metasection/buildsection.py`) | `build`, `make`, `construct` | `configure` (runs inside `env.Configure()`), `config`, then the first of `source` (alias `build`), `sdk`, `system` | top-level targets |
| `unit_test` (`metasection/unittestsection.py`) | `utest`, `run_utest` | `build`, `run` (per group, with its own env clone and test context) | group |

A classic part file has no decorated callbacks; its body runs during the read and builds directly into the pre-created `build` Section.

## Declaring a dependency (read time)

```mermaid
flowchart TD
    A["part file: env.DependsOn([...])<br/>dependson.py depends_on"] --> G{"glb.processing_sections?"}
    G -->|"yes"| ERR["aborts with NameError:<br/>the error_msg call meant to refuse it<br/>uses an undefined name, output"]:::hot
    G -->|"no"| B["each string becomes Component(env, s)"]
    B --> C["Component(name, version_range,<br/>requires, section, optional)"]
    C --> C1["target_type('name::' + name)<br/>unless it starts with alias::"]
    C --> C2["requires defaults to REQ.DEFAULT"]
    C --> C3["pobj.Uses resolves requires= now<br/>exits on an unknown alias"]:::hot
    C1 --> D["dependent_ref(PartRef(target, Uses),<br/>section, requires, optional)"]
    C2 --> D
    C3 --> D
    D --> E["section_from_env(env).Depends = list"]
    E --> F["depends_on_classic:<br/>put a delayed mapper value per requirement<br/>into env DEPENDS namespace and, if public,<br/>env KEY. If not internal, into own Exports"]
    classDef hot stroke:#dc2626,stroke-width:3px
```

Every dependency of a Part is known when its read completes, but nothing is resolved yet: `Section.Depends` is a plain list. Resolution happens when something asks a `PartRef` for its matches.

## Matching a dependency

```mermaid
flowchart TD
    A["PartRef.Matches"] --> B["part_manager._from_target(target, local_space)"]
    B --> L{"local space<br/>(requires= Parts) has a match<br/>by alias or Name?"}
    L -->|"yes"| R
    L -->|"no"| G{"target has alias?"}
    G -->|"yes"| GA["_from_alias(alias)"]
    G -->|"no"| GN["name registry: every alias<br/>registered for the name"]
    GA --> R["reduce_list_from_target"]
    GN --> R
    R --> R1["test properties in insertion order:<br/>string @properties, platform_match,<br/>version (a string range gets .*, so * is *.*),<br/>config"]
    R1 --> R2["a mismatch sets match False, except<br/>platform_match: it only removes from the list,<br/>so a platform mismatch alone does not drop the Part"]:::hot
    R2 --> R3["keep only the highest version"]
    R3 --> OUT["matches"]
    OUT --> DP{"dependent_ref.Part"}
    DP -->|"one"| OK["Part, then Part.Section(name)"]
    DP -->|"none, required"| X1["error_msg: exits"]
    DP -->|"none, optional"| X2["warning, NilPart"]
    DP -->|"several"| X3["error_msg: ambiguous"]
    classDef hot stroke:#dc2626,stroke-width:3px
```

- `PartRef.Matches` stores only a non-empty result, for the life of the object. A match made before every candidate was read sticks.
- The local-space loop reads `pobj.Name`, which on an unread Part writes its alias into the registry.
- `_from_alias()` returning `None` is appended as-is, and `reduce_list_from_target` then fails on `p.ID`.
- The `platform_match` branch of `reduce_list_from_target` does not filter: it calls `part_lst.remove(pobj)` and never sets `match = False`, so a platform mismatch alone does not drop the Part (a later `version` or `config` test still can). On the `PartRef` path the argument is a list, and the removal skips the next candidate. `map_scons_target_list()` passes a `set`, and there the removal raises `RuntimeError: Set changed size during iteration`. A bare target such as `scons 'foo@platform_match:win32-x86'` reaches it: `map_targets_sections()` selects every build section for it, and `map_scons_target_list()` then reduces the Parts named `foo` (probe: two Parts named `foo` on a darwin-aarch64 host; with a matching platform the higher version builds). Only the `name::` form of a registered name fails earlier ([03-part-loading.md](03-part-loading.md#mapping-targets-to-sections)).

## Processing a section

`Section.ProcessSection()` runs for each Section in the closure, dependencies first:

```mermaid
flowchart TD
    A["Section.ProcessSection()"] --> B["ResolveDepends()<br/>DependsSorted: user order,<br/>constrained by FullDependsSorted"]
    B --> C["for each dependency, for each requirement:<br/>map_requirement(env, req, dep), then, if the<br/>requirement is not internal, add the value<br/>to this section's Exports"]
    C --> D["metasection bound, chdir to BUILD_DIR,<br/>VariantDir for out-of-tree sources"]
    D --> E["MetaSection.ProcessSection(0)<br/>run phase callbacks"]
    E --> F["map top-level targets to the section alias<br/>(by group for unit_test)"]
    F --> G["one pass over Depends:<br/>collect the export.jsn of dependencies<br/>with dynamic exports, map requirement.mapto aliases"]
    G --> H["Depends(bottom targets,<br/>collected export.jsn files)"]
    H --> I["env._map_export_ declares the export.jsn node<br/>(written at build time from the final Exports),<br/>ProcessSection maps it to the alias"]
    I --> J["DynamicPackageNodes(export.jsn)"]
    J --> K["Exports EXISTS = section alias"]
```

### map_requirement

```mermaid
flowchart TD
    A["map_requirement(env, req, dep)"] --> B{"dependency section has<br/>dynamic exports?"}
    B -->|"yes, classically mapped"| B1["keep the delayed mapper value"]
    B -->|"yes"| B2["map_val = delayed mapper"]
    B -->|"no"| C["map_val = dependency Exports KEY<br/>(static, resolved now)"]
    C -->|"empty"| CE["return the delayed mapper value,<br/>write nothing"]
    B2 --> N
    C --> N["env DEPENDS.NAME.KEY = map_val"]
    N --> P{"req.is_public?"}
    P -->|"list"| C1["if classically mapped: remove the<br/>classic mapper value from env KEY"]
    C1 --> P1["env.PrependUnique(KEY=map_val)"]
    P -->|"scalar"| P2["env KEY = map_val"]
    P1 --> R["return map_val to ResolveDepends"]
    P2 --> R
    P -->|"not public"| R
    A -.-> O["dependency optional and unmatched:<br/>branch ends in 1/0, unreachable"]:::dead
    classDef dead fill:#e5e7eb,stroke:#9ca3af,color:#4b5563
```

## Requirements

A requirement names one variable and how it travels: `public` maps it into the consumer's top-level environment, `internal` keeps it from being re-exported to the consumer's own dependents, `force_internal` stops any set-level internal value from changing the requirement's own flag (including the `internal=True` that every `REQ.<SET>` lookup applies since 0.16, through `metaREQ.__getattr__`), `listtype` merges the value into a list instead of replacing it (`PrependUnique` into the consumer env, `extend_unique` into Exports), `mapto` binds extra aliases. Sets are defined with `DefineRequirementSet()` in `api/requirement.py`.

```mermaid
flowchart LR
    DEF["REQ.DEFAULT"] --> CPPD["CPP_DEFAULTS"]
    DEF --> CD["C_DEFAULTS"]
    CPPD --> HDR["HEADERS:<br/>CPPPATH, CPPDEFINES"]
    CPPD --> LIBS["LIBS:<br/>LIBPATH, LIBS"]
    CD --> HDR
    CD --> LIBS
    DEF --> EX["EXISTS<br/>(section alias)"]
    DEF --> PKG["PKG_CONFIG_PATH, PKG_DEFAULTS"]
    DEF --> CM["DESTDIR_PATH"]
    DEF --> RP["RPATHLINK<br/>internal=False, force_internal=True:<br/>transitive"]
    DEF --> RPM["RPM_PACKAGE_RUNPATH"]
```

- Transitivity comes from `internal=False`: `ResolveDepends` copies such a value into the consumer's own Exports, so each level re-exports it to the next. `CPPPATH` is internal, so headers reach the immediate consumer and stop; `RPATHLINK` is `internal=False` and reaches the whole chain. `force_internal=True` on `RPATHLINK` matters for every dependency, because of the next point.
- Since 0.16, every `REQ.<SET>` lookup (through `metaREQ.__getattr__`), including `REQ.DEFAULT`, `Component()`'s default, builds its requirements with `internal=True`, which overrides each member's flag unless it has `force_internal`. While a Part whose env sets `COMPAT_REQ_INTERNAL` is being read (and its sub-parts, which are read inside it), `glb.compat_internal` is non-zero and lookups use `internal=False` instead, with a deprecation warning.
- Export tables are lists of lists (`Exports[KEY] == [[...]]`), and they are merged with `common.extend_unique`, which is O(n²).
- `append_unique` moves a repeated item to the end. That is deliberate link-order behaviour; keep it in any rewrite.
