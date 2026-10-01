# L1/L2: Environments, toolchains, and configuration

Every Parts environment comes from one funnel, `Settings._env_const_ref()` in `settings.py`. It builds a base environment from the merged variables, applies the toolchain, then applies the configuration (debug, release, and site levels) for each configured tool. Results are cached by a key made from the keyword arguments.

## Building an environment

```mermaid
flowchart TD
    C1["SCons.Script.DefaultEnvironment()<br/>(patched)"] --> DE["Settings.DefaultEnvironment()<br/>cached as DefaultEnvironment"]
    C2["Part setup: Settings.Environment(**kw)<br/>2 to 3 calls per Part"] --> K
    DE --> K["_env_const_ref(**kw)<br/>key = get_cache_values(prepend, append, kw)"]:::hot
    K -->|"hit"| ENVB
    K -->|"miss"| B["BasicEnvironment()<br/>cached as base"]
    B --> B1["_basic_base_env(tools=[])"]
    B1 --> B2["vars.Update(env, ARGUMENTS, cfg_file)<br/>see 01-startup variable precedence"]
    B2 --> B3["PARTS_RUN_CSIG, BUILDERS"]
    B3 --> CL["Clone(**kw), re-apply Variable kwargs"]
    CL --> TC["env.ToolChain(pre + env toolchain + post)<br/>post always adds install, zip, textfile"]
    TC --> CF["env.Configuration()<br/>config.py apply_config"]
    CF --> MP["env.Replace(**glb.mappers)"]
    MP --> TS["env TOOLCHAIN string"]
    TS --> AP["append / prepend kwargs"]
    AP --> ENVB["ENV: os.environ if --use-env,<br/>then Settings ReplaceENV, PrependENVPath, AppendENVPath"]
    ENVB --> ST["store in __env_cache"]
    INV["Variable change event<br/>SetOptionDefault, ReplaceENV,<br/>getter reads"] -->|"_handle_var_change empties cache"| K
    classDef hot stroke:#dc2626,stroke-width:3px
```

- `DefaultEnvironment()` returns a clone of `_env_const_ref()`; `_env_const_ref()` itself returns a shared instance that callers must not modify.
- The cache key is weaker than it looks: `get_cache_values()` starts its whitelist with `string_tester('*')`, which matches every key, so every keyword argument enters the key, and the values are joined with no separator. Sub-parts inherit the parent's `CHECK_OUT_DIR`, so misses scale with distinct parent checkout directories.
- Each Section clones its Part's environment once more ([04-sections-and-dependencies.md](04-sections-and-dependencies.md)).

## Toolchain resolution

`--tc` / `--toolchain` and `env['toolchain']` hold a list of `[name, version]` entries. `tool_mapping._ToolChain()` turns it into tools applied to the environment.

```mermaid
flowchart TD
    A["--tc gcc_12,binutils<br/>poptions opt_chain splits on _"] --> B["core/util/misc.py process_tool_arg<br/>normalize to name, version<br/>more than one _ is an error"]
    B --> C["tool_mapping.get_tools(env, list)"]
    C --> D{"entry config is<br/>None or a string?"}
    D -->|"yes"| E["get_tlset_module(name, version)<br/>try toolchain/NAME_VERSION.py, then NAME.py<br/>on the site path"]
    E -->|"module found"| F["mod.resolve(env, version)<br/>returns list of name, config"]
    F -->|"recurse until stable"| C
    E -->|"no module"| G["SCons.Tool.Tool(name) probe<br/>leaf tool, config"]
    D -->|"dict"| H["leaf tool: env.Replace(**config)<br/>before generate"]
    D -->|"callable"| I["leaf tool: config(env)<br/>before generate"]
    G --> J["for each leaf tool"]
    H --> J
    I --> J
    J --> K["append to env CONFIGURED_TOOLS"]
    K --> L["SCons.Tool.Tool(name, toolpath)(env)<br/>overrides/tool.py Parts_Tool<br/>tools/NAME.py generate()"]
    C -.->|"name is null"| N["skipped"]
```

Example: `toolchain/default.py` picks a compiler family by host and target; on a POSIX host without the Intel compiler it returns `[('gxx', None)]`. `toolchain/gxx.py resolve()` returns `[('g++', f), ('gcc', f), ('ar', None), ('gas', None), ('gnulink', None)]` (`applelink` and `lipo` instead of `gnulink` on darwin), where `f` threads the version into `GXX_VERSION`/`GCC_VERSION`. `ar` has no toolchain module, so it becomes a leaf tool.

Consequences:

- A site `toolchain/gcc.py` shadows the built-in one for the whole run (`sys.modules` pins `parts.toolchain.gcc`), and if it returns `('gcc', None)` or `('gcc', 'VERSION')` that entry resolves to itself again. Compose a base by using a different name (`default` → `gxx` works for this reason).
- The version string is what drives compiler discovery: `resolve()` passes it into `*_VERSION`, and the GnuCommon tool layer looks for that version.
- When the `SCons.Tool.Tool(name)` probe raises for any reason, including an error inside an existing tool module, the build stops with "Failed to load Unknown ToolChain or Tool" and no traceback.

### The tool overlay

`tools/*.py` sit on top of `SCons/Tool/*.py`. They reach the base in three different ways, which is why a fix often applies to one language and not its sibling:

| Pattern | Tools | Risk |
| --- | --- | --- |
| Call base `generate()`, then override with `env[...] =` | `cc` (fixed in `8d6c7a2`), `ar`, `gnulink`, `javac` | Correct pattern. Use it |
| Call base `generate()`, then `SetDefault()` | `applelink` (`DSYMUTIL`) | Works today only because SCons' `applelink` does not set `DSYMUTIL`. `SetDefault` would become a silent no-op if SCons started setting it |
| Rebuild without the base | `c++`, `masm`, `msvc`, `mslink`, `mslib`, `midl`, `msvs` | Copies of base command strings drift from SCons |
| Via a Parts sibling | `gcc` → `parts.tools.cc`, `g++` → bare `c++`, `clang`/`aocc` → both | Asymmetric inheritance |

## Configuration selection

`env.Configuration()` is `config.apply_config()`. Levels form a chain through `DefineConfiguration(name, dependsOn)`: `debug` and `release` depend on `default`, and a site can add levels. The user documentation is [configurations.rst](../source/concepts/configurations.rst).

```mermaid
flowchart TD
    A["apply_config(env)<br/>name = env CONFIG"] --> B["for tool in CONFIGURED_TOOLS"]
    B --> C["get_config(env, level, tool, host, target)"]
    C --> D["load_tool_config"]
    D --> H["load the dependent level first"]
    H --> F["search in load_tool_config:<br/>first site dir with a file that loads wins,<br/>most specific of 28 name forms wins:<br/>TOOL_HOST_TARGET ... TOOL"]
    F --> G["import file<br/>on an error: warning,<br/>then the next name form"]:::hot
    G --> E["ver = the level's version mapper(env)<br/>map_none_version"]
    E --> BS["dependent level's settings for ver"]
    BS --> I["config.merge(ver, dependent settings)<br/>only the first VersionRange that holds ver,<br/>no match keeps the dependent settings"]:::hot
    I --> J["store under the matched range"]
    J --> K["apply flags: replace, then AppendUnique,<br/>then PrependUnique"]
    K --> L["prepend_env, append_env on env ENV:<br/>PrependENVPath, AppendENVPath"]
    L --> M["post_process_func list"]
    classDef hot stroke:#dc2626,stroke-width:3px
```

Rules worth knowing:

- Exactly one file loads per level, tool, host, and target. A platform-named file such as `gcc_any-x86_64_any-x86.py` replaces the generic `gcc.py` of the same level; it does not add to it. Levels still stack.
- A configuration file that raises on import does not stop the build. `load_tool_config()` prints a warning once and tries the next, less specific name, so an error in `gcc_posix-x86_64.py` falls back to `gcc.py` with only that warning.
- Only the first matching `VersionRange` applies: `configuration.merge()` stops at the first range, in declaration order, that holds the version. A later overlapping block is dead for every version an earlier block covers. For example, the `"7-*"` block in `default/gcc.py` (`-fdiagnostics-color=always`) never applies, because the `"*"` block before it matches every version.
- `merge()` resets the `prepend_env` and `append_env` lists before it adds the current level's, so a level whose matching range runs replaces the `ENV` additions of the levels below it instead of extending them. `post_process_func` entries accumulate across levels.
- A `post_process_func` runs after every level's flags, so a derived level cannot `filter` or `replace` what a base level's function set.
- `--use-env` replaces `env['ENV']` with `os.environ` after the configuration is applied, which discards the configuration's `ENV` additions.
- `--verbose=configuration` shows which file loaded and the merged settings; the per-directory file search and version resolution are under `--trace=configuration`.
- `loadlogic/changed.py` would use `get_defining_config_files()` for a configuration up-to-date check, but nothing on the active load path calls that loader ([07-overrides-caches-dead-code.md](07-overrides-caches-dead-code.md#dead-code)).
