# L2: SDK, install, and packaging

A Part publishes outputs in two directions. **SDK** calls copy files into `$SDK_ROOT` and add entries to the Section's export table, which is how dependents find headers and libraries. **Install** calls copy files into `$INSTALL_ROOT` and tag them for packaging. Package builders such as `RPMPackage` then collect installed files by **package group**.

## From a part file to the export table and the install tree

```mermaid
flowchart TD
    A["env.InstallLib(libfoo)<br/>InstallBin, InstallInclude, ..."] --> PI["installs.py ProcessInstall"]
    PI --> SDK["env.SdkItem('$SDK_LIB', ...)<br/>unless create_sdk is False"]
    PI --> INS["env.Install / InstallAs to $INSTALL_LIB<br/>tags: category, part_alias, no_package"]
    B["env.SdkLib, SdkInclude, Sdk ..."] --> SDK
    SDK --> CP["process_Sdk_Copy<br/>CCopy, batched by Part and dir"]
    CP --> SC["parts-smart-cp console script<br/>one Python process per 50 files"]:::hot
    SDK --> XP["exportitem.export_path / export_file<br/>Section Exports: LIBS, LIBPATH,<br/>RPATHLINK, CPPPATH"]
    C["env.ExportItem(KEY, values)<br/>ExportCPPPATH, ExportLIBS, ..."] --> XP
    XP --> EJ["export.jsn per Section<br/>written in ProcessSection"]
    INS --> IF["SCons.Tool.install._INSTALLED_FILES<br/>(private SCons global)"]
    classDef hot stroke:#dc2626,stroke-width:3px
```

- The install and SDK directories come from variables such as `INSTALL_ROOT`, `INSTALL_LIB`, `SDK_ROOT`, `SDK_LIB`. A gold test commonly sets `SetOptionDefault('INSTALL_ROOT', '#_install')`.
- `InstallTarget` and the `Sdk*` functions return the copied nodes; the copy builder is `core/builders/ccopy.py` (`CCOPY_LOGIC`: `default`, `copy`, `hard-copy`; default `hard-copy`).
- Dependents consume the export table, not the SDK file nodes: `SDKLIB`/`SDKBIN` are not in `REQ.DEFAULT`.

## Package groups

```mermaid
flowchart TD
    P["Part(..., package_group='runtime')<br/>or PackageGroup(name, parts)"] --> G["packaging.g_package_groups<br/>group name to Part aliases"]
    IF["_INSTALLED_FILES"] --> S["SortPackageGroups()<br/>under g_sort_data_lock"]
    G --> S
    S --> F1["PACKAGE_GROUP_FILTER<br/>criteria per group"]
    S --> F2["PACKAGE_NODE_FILTER<br/>callbacks returning groups"]
    F1 --> SG["_sorted_groups:<br/>pkg and no_pkg sets of nodes per group"]
    F2 --> SG
    SG --> DPN["DynamicPackageNodes:<br/>PARTS_SYS_DIR/package.groups.jsn,<br/>depends on every export.jsn"]
    SG --> GF["env.GetPackageGroupFiles(group)<br/>GetFilesFromPackageGroups(target, groups)"]
    GF --> PK["package builders:<br/>RPMPackage, tar, zip, deb, msi"]
    DPN --> PK
```

- Packaging is lazy: the group sets are re-sorted when the number of installed files changes, so a package builder sees files installed by Sections processed after it was declared.
- `PackageGroup()` sets `g_resort_package_data = True` without a `global` statement, so that assignment is local and never forces a re-sort.
- A file in two groups is reported through `PACKAGE_DUPLICATE_FILES_HANDLING` (`error`, `warning`, or ignore).

## RPM

```mermaid
flowchart LR
    A["env.RPMPackage(target, source=group files)<br/>pieces/rpm_package.py"] --> B["Clone(**kw), DIST from rpm --eval,<br/>TARGET_ARCH mapped to rpm arch"]
    B --> C["_RPMPackage builder<br/>emitter, rpm_scanner"]
    C --> D["spec from RPM_* variables<br/>pieces/rpm_val.py, %files by category tag"]
    C --> E["staged tree, setrpath:<br/>patchelf with GEN_PKG_RUNPATHS"]
    D --> F["rpmbuild"]
    E --> F
    F --> G["package.rpm"]
```

- `RPMPackage()` returns the built package nodes. Copying them to a collection directory is up to the part file (for example `env.CCopy(DIR, out)`).
- The default `RPM_RUNPATH` holds both `$ORIGIN`-relative and absolute entries. The absolute ones (`GEN_PKG_RUNPATHS(..., use_origin=False)`) take every library path as given, loader defaults included: with `PACKAGE_ROOT` left at `/`, `PACKAGE_LIB` is `/lib`, and rpmbuild's `check-rpaths` on Red Hat based systems rejects a standard runpath such as `/lib`.
- `X_RPM_OBSOLETES` (`obsoletes=`) emits an `Obsoletes:` header.
