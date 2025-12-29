# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-29

### Added
- **Deterministic Autonomous Auditor** - Production-ready codebase analysis
- **Canonical Pattern Matching** - TODO, FIXME, import, and config file detection
- **Self-Healing Plans** - Automatic plan revision on repeated failures
- **Bounded Execution** - Safe, read-only operations with strict limits
- **Machine-Readable Output** - JSON format for CI integration (`--json` flag)
- **Specialization System** - Codebase auditor mode with domain-specific prompts
- **Memory Persistence** - SQLite-backed audit history across sessions
- **Production CLI** - Rich progress indicators and professional output
- **Frozen Architecture** - Immutable core with documented invariants
- **Comprehensive Testing** - Non-negotiable guarantee tests

### Architecture
- **Frozen Core** - No breaking changes allowed in v1.x
- **Public Interface Contract** - Stable CLI flags, exit codes, output schema
- **Graceful Degradation** - Safe fallbacks when LLM planning fails
- **Type Safety** - Binary/text file classification prevents decode errors

### Documentation
- Complete installation and usage instructions
- CI integration examples with GitHub Actions
- Public interface contract (INTERFACE.md)
- Architecture documentation (ARCHITECTURE.md)
- Specialization boundaries (SPECIALIZATION.md)

## Versioning Policy

- **v1.x.x** - Surface changes only (UX, documentation, packaging)
- **v2.0.0** - New capabilities (would require separate repository)

This protects the frozen architecture and ensures reliability.
