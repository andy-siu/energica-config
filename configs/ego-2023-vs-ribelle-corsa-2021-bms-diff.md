# BMS diff: energica-ego-2023.xml vs energica-ribelle-corsa-2021.xml

Comparing `./2023-ego-rs/stock/energica-ego-2023.xml` against
`./2021-eva-corsa-clienti/stock/energica-ribelle-corsa-2021.xml`.

## Big picture

Both files are the same size (3006 lines, 2978 leaf parameters) and identical structure.
They are **identical except for the `LMU` sections** — 134 differing values, 100% of them in
the LMU blocks (Local Monitoring Units, the per-cell-group monitoring boards). Every other
section — `BMCU`, `SUBC`, and all other `BMS` params (2,844 of 2,978 leaves) — is
byte-for-byte the same.

## The pattern

All 11 LMU blocks (`LMU[0]`–`LMU[10]`) differ the same way. On the **EGO** these fields are
configured/enabled; on the **EVA (ribelle-corsa)** they are all disabled or zeroed:

| Field                              | EGO (2023-ego) | EVA (ribelle-corsa 2021) | # LMUs affected |
| ---------------------------------- | -------------- | ------------------------ | --------------- |
| `Cell1Enabled`–`Cell7Enabled`      | `True`         | `False`                  | 11 each         |
| `Cell8Enabled`                     | `True`         | `False`                  | 4               |
| `BattTemp1Enabled`                 | `True`         | `False`                  | 9               |
| `BleedTempMax`                     | `55`           | `0`                      | 11              |
| `BleedTempHysteresis`              | `2`            | `0`                      | 11              |
| `BleedVoltage`                     | `4150`         | `0`                      | 11              |
| `BleedVoltageHyst`                 | `200`          | `0`                      | 11              |

## What it means

The EVA file's LMU section reads like an **un-provisioned / zeroed template**: cell channels
marked disabled, temperature sensor off, and all four cell-balancing ("bleed") parameters at
`0`. The EGO file has a real cell configuration — all cells enabled and balancing set up
(bleed at 4150 mV, up to 55 °C, with hysteresis).

Two subtleties:

- `Cell8Enabled` differs in only **4** of 11 LMUs — the other 7 LMUs have Cell8 disabled on
  *both* bikes (those groups genuinely use 7 cells, so it is not part of the "all-off"
  template difference there).
- `BattTemp1Enabled` differs in **9** of 11 — two LMUs match on both bikes.

Everything outside the LMU cell/bleed config is identical between the two files.
