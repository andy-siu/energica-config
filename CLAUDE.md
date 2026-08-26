# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A data repository of controller-configuration dumps read off individual Energica
electric motorcycles. There is **no build system, tests, lint, or application code** — do
not look for `package.json`, a Makefile, CI, etc. Work here is reading, diffing, and
curating configuration snapshots. Treat every file as a captured device state, not as
source to be executed.

## Layout & naming convention

Top-level directories are named `<year>-<model>[-<variant>]`, e.g. `2021-eva-corsa-clienti`
(`clienti` = Italian for a customer bike) and `2023-ego-rs`. A bike directory may contain
sub-folders for a configuration variant (e.g. `stock/`). Each holds the dumps for that one
bike/variant.

Two file kinds live here:

- **`vcu.json`** — a decoded dump of the Vehicle Control Unit parameter tables.
- **`*.xml`** (e.g. `15-bounded-clamp.xml`) — a Battery Management System (BMS) config,
  a flat tree of `<BMS>` → `<BMCU>` / `<LMU>` / `<SUBC>` sections with one tag per parameter.

## `vcu.json` structure — the key concept

Top-level: `readAt` (epoch ms), `complete`, `micros` (the microcontrollers read, e.g.
`["A9","A8"]`), and `rows` (one entry per parameter, ~277 rows).

Each row: `index`, `identifier` (= `4096 + index`), `micro`, `name`, `section`, `type`
(`BYTE`/`WORD`/`BOOL`), `signed`, `status`, `rawHex`, `unsigned`, `value`, `otherBikeValue`,
`widthMismatch`, `note`.

Two things drive how to read a row:

1. **Decoded vs. raw-only.** The bike declares a parameter-table version in
   `TABLE_TYPE_uC` / `TABLE_TYPE_uS`. If the reading software carries that table version,
   rows are fully decoded (`name`, `section`, `type`, `value` populated) — this is the
   `2023-ego-rs` case (table `4119`). If it does **not**, `name`/`section`/`type`/`value`
   are all `null`, only `rawHex`/`unsigned` are trustworthy, and `note` explains why — this
   is the `2021-eva-corsa-clienti` case (table `4115`, 275/277 rows raw-only). Never invent
   a parameter name for a raw-only row.

2. **It is a diff.** `otherBikeValue` is the same parameter's value on a reference bike;
   `value` is this bike's. Rows where they differ (and `widthMismatch`) are the meaningful
   deltas — this is a comparison export, not just a snapshot.

Decoded rows group under `section` (e.g. `DRIVE_BY_WIRE 1/2`, `RESS`, `AIR_TEMP`, `VSM`,
`LIMP_MODE`, `EVSE`, ...).

## Working here

- Preserve exact numeric values, `rawHex`, and formatting when editing — these mirror bytes
  read from hardware; a stray edit misrepresents a physical bike's state.
- Use Python's `json` for inspection/diffing rather than eyeballing 4000-line files.
- When comparing two bikes, diff by row `name` for decoded files; fall back to `identifier`
  when either side is raw-only (names are absent).
