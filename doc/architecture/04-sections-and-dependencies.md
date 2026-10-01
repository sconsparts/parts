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
    R --> R1["version: string range gets .*,<br/>so * is tested as *.*"]
    R1 --> R2["platform_match, config, other properties"]
    R2 --> R3["keep only the highest version"]
    R3 --> OUT["matches"]
    OUT --> DP{"dependent_ref.Part"}
    DP -->|"one"| OK["Part, then Part.Section(name)"]
    DP -->|"none, required"| X1["error_msg: exits"]
    DP -->|"none, optional"| X2["warning, NilPart"]
    DP -->|"several"| X3["error_msg: ambiguous"]
```

- `PartRef.Matches` stores only a non-empty result, for the life of the object. A match made before every candidate was read sticks.
- The local-space loop reads `pobj.Name`, which on an unread Part writes its alias into the registry.
- `_from_alias()` returning `None` is appended as-is, and `reduce_list_from_target` then fails on `p.ID`.
- `reduce_list_from_target` removes items from the list it is iterating in its `platform_match` branch.

## Processing a section

`Section.ProcessSection()` runs for each Section in the closure, dependencies first:

```mermaid
flowchart TD
    A["Section.ProcessSection()"] --> B["ResolveDepends()<br/>DependsSorted: user order,<br/>constrained by FullDependsSorted"]
    B --> C["for each dependency, for each requirement:<br/>map_requirement(env, req, dep)"]
    C --> D["metasection bound, chdir to BUILD_DIR,<br/>VariantDir for out-of-tree sources"]
    D --> E["MetaSection.ProcessSection(0)<br/>run phase callbacks"]
    E --> F["map top-level targets to the section alias<br/>(by group for unit_test)"]
    F --> G["one pass over Depends:<br/>collect the export.jsn of dependencies<br/>with dynamic exports, map requirement.mapto aliases"]
    G --> H["Depends(bottom targets,<br/>collected export.jsn files)"]
    H --> I["env._map_export_: write this section's export.jsn,<br/>map it to the alias"]
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
    C -->|"classically mapped"| C1["remove the classic mapper value<br/>from env KEY first"]
    B2 --> N
    C --> N["env DEPENDS.NAME.KEY = map_val"]
    C1 --> N
    N --> P{"req.is_public?"}
    P -->|"list"| P1["env.PrependUnique(KEY=map_val)"]
    P -->|"scalar"| P2["env KEY = map_val"]
    P -->|"not public"| X
    P1 --> X{"req.is_internal?"}
    P2 --> X
    X -->|"no"| X1["also add to this section's Exports,<br/>so its own dependents get it"]
```

## Requirements

A requirement names one variable and how it travels: `public` maps it into the consumer's top-level environment, `internal` keeps it from being re-exported to the consumer's own dependents, `force_internal` routes it through the recursive export mapper, `listtype` appends instead of replacing, `mapto` binds extra aliases. Sets are defined with `DefineRequirementSet()` in `api/requirement.py`.

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

- Headers are direct-only: `CPPPATH` reaches the immediate consumer and stops. `RPATHLINK` reaches the whole chain because it is re-resolved at each level through the recursive `PARTIDEXPORTS` mapper. Setting `internal=False` on a requirement without `force_internal=True` does not make it transitive.
- Since 0.16, `REQ.DEFAULT` is `internal=True` by default. A part with `COMPAT_REQ_INTERNAL` set in its env gets the old behaviour and a deprecation warning.
- Export tables are lists of lists (`Exports[KEY] == [[...]]`), and they are merged with `common.extend_unique`, which is O(n²).
- `append_unique` moves a repeated item to the end. That is deliberate link-order behaviour; keep it in any rewrite.
