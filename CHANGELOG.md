# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `requires-python = ">=3.9"` to the package metadata.
- This `CHANGELOG.md`.
- A `.gitignore` covering Python caches, packaging artifacts, the pytest
  cache, and the local Core Challenge 2022 benchmark checkout.

### Removed
- The dead `py-modules = ["reconf"]` entry from `pyproject.toml` (there is no
  top-level `reconf.py`; the module lives at `reconfillion/reconf.py`).

## [1.1.0] - 2026-06-08

### Added
- Token addition/removal (`tar`) model, with problem-agnostic `lower`/`upper`
  size bounds.
- Token sliding (`ts`) model, which moves a token to an adjacent element; it
  takes a `graph` argument describing the adjacency.
- `get_longest_shortest_seq`, a single-start query that returns a shortest
  sequence to a farthest reachable state (the eccentricity of the start).
- Support for `VertexSetSet` states in addition to `GraphSet` and `setset`.
- A pytest suite exercising the `tj`, `tar`, `ts`, and `get_longest_shortest_seq`
  paths against Core Challenge 2022 independent-set instances.

### Changed
- Refactored the forward breadth-first frontier expansion into a shared
  `_forward_bfs` helper used by both `get_reconf_seq` and
  `get_longest_shortest_seq`.
- Tidied API consistency and made the frontier saturation check robust to
  astronomically large ZDD families.
- Documented the models in the README and added a detailed `get_reconf_seq`
  docstring.

### Fixed
- A bug in reconfiguration-sequence computation.

## [1.0.0] - 2024-04-19

### Added
- Initial release: `get_reconf_seq` solving combinatorial reconfiguration
  problems on top of graphillion, with the token jumping (`tj`) model.

[Unreleased]: https://github.com/junkawahara/reconfillion/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/junkawahara/reconfillion/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/junkawahara/reconfillion/releases/tag/v1.0.0
