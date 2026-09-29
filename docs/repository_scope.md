# Repository scope

This repository is a personal fork for reproducing and reusing TikNib. It also
contains the integration and evaluation layer used by the BinForge paper. A
future branch split may separate those layers, but both are intentional parts
of the current history.

## Tracked TikNib responsibilities

- TikNib extraction, filtering, feature, and evaluation code
- generally useful fixes to the reproduced implementation
- configurable command-line entry points
- validation and regression tests
- small redistributable fixtures
- configuration templates and machine-independent documentation

## Tracked BinForge paper layer

- BinForge evaluation configurations used with TikNib
- input-list formats and experiment definitions needed to reproduce the paper
- evaluation and plotting code for the BinForge paper
- compatibility fixes that let TikNib consume BinForge-produced binaries

Large datasets and generated analysis sidecars remain external even when the
experiment definitions are tracked.

## Local, ignored state

- `config/local.ini`
- IDA installation and Python runtime paths
- workstation-specific WSL/Windows path mappings
- licenses, credentials, and license-service configuration
- raw datasets, IDA databases, pickles, logs, ctags caches, and run controls

The tracked `config/local.ini.example` documents the supported local settings.
Environment variables can override them when a parent project invokes TikNib
as a submodule.

## External responsibilities

- IDA installation and licensing
- selecting or creating an IDAPython runtime
- switching a shared IDA installation between unrelated artifacts
- building another project's binaries unless covered by the tracked BinForge
  reproduction layer
- large-data transfer, archival, and publication

TikNib may verify an external prerequisite, but should not silently mutate or
take ownership of it.

## Shared IDA safety

IDA's `Python3TargetDLL` is a per-user global setting. A TikNib run should
verify that it matches the configured `ida.python_dll`. It must not switch the
runtime during a batch because later worker processes would start with a
different Python environment. `helper/do_idascript.py` performs a read-only
environment check on every run; `--preflight` adds one real IDA probe before
starting the pool.

## Parent-project contract

A parent artifact should supply:

1. an input list of binaries on a path visible to Windows IDA;
2. source roots when line/type extraction needs them;
3. local configuration or `TIKNIB_*` environment overrides; and
4. its own orchestration, dataset metadata, and result publication.

TikNib should return documented sidecars and a nonzero status with a retry list
when extraction or validation fails.

## Local collaboration runs

One-off collaboration orchestration should live outside the repository or be
listed only in the clone-local `.git/info/exclude`. Such exclusions must not be
added to the tracked `.gitignore`, because they are not part of the repository
contract. Generic validators developed during a local run may remain tracked
when they contain no dataset size, package, path, or paper-specific assumptions.

## Tracking decision guide

| Item | Location | Tracked |
| --- | --- | --- |
| Generic TikNib code, tests, and documentation | this repository | yes |
| BinForge paper definitions and evaluation logic | this repository | yes, for now |
| Machine configuration template | `config/local.ini.example` | yes |
| Actual machine configuration | `config/local.ini` | no |
| One-off collaboration orchestration and notes | outside the repository or clone-local exclude | no |
| Raw binaries and generated sidecars | external dataset storage | no |

An input list containing absolute dataset paths is a run control, not portable
configuration. Parent projects should generate it locally and pass it to the
generic TikNib commands. A tracked experiment manifest should contain stable
experiment identity rather than a maintainer's workstation path. New and
maintained manifests under `example/` therefore use relative paths;
`script/materialize_path_list.py` resolves them into ignored local lists.

The large historical `example/binforge_binkit000` and `example/260319`
snapshots predate this rule and still contain maintainer paths. They are kept
unchanged in this commit so a 64,000-line data migration does not obscure the
runtime changes. Treat them as legacy paper inputs, not machine configuration;
move them to relative manifests in a dedicated, separately reviewed change.
