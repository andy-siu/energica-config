# VCU diff: 2023-ego-rs vs 2021-eva-corsa-clienti

Comparing `./2023-ego-rs/stock/vcu.json` against `./2021-eva-corsa-clienti/stock/vcu.json`.

## Big picture — different firmware parameter-table versions

|                          | 2023-ego-rs                                    | 2021-eva-corsa-clienti                          |
| ------------------------ | ---------------------------------------------- | ----------------------------------------------- |
| `TABLE_TYPE_uC` / `uS`   | **4119**                                       | **4115**                                        |
| Decoding                 | Fully decoded — all 277 rows have name/section/value | Only 2 rows decoded; **275 rows raw-only** (name/value = null) |
| `readAt` (epoch ms)      | 1787540865598                                  | 1787625337573                                   |
| micros                   | A9, A8                                         | A9, A8                                          |
| rows                     | 277                                            | 277                                             |
| `complete`               | true                                           | true                                            |

## Why the EVA is not decoded

Table-version mismatch — **not** corruption or an incomplete read (`complete: true`).

Each bike declares its parameter-table version in `TABLE_TYPE_uC` (A9 micro) and
`TABLE_TYPE_uS` (A8). To turn raw bytes into named/typed parameters, the reading software
must carry a matching copy of that table version. The EVA declares table **4115**, which the
software **did not carry**, so `name`/`section`/`type`/`value` were left `null`. The `note`
on every raw-only row states this:

> "the A9 named a parameter table this software does not carry, so nothing here can say what
> this index is called — the raw bytes are the bike's, the name is not available"

- 232 raw-only rows attributed to the A9, 43 to the A8 (reflects which micro owns each row).
- The only two decoded EVA rows are `TABLE_TYPE_uC` and `TABLE_TYPE_uS` themselves (= 4115),
  read at a fixed known location so the version can be identified before decoding the rest.
- The ego declares table **4119**, which the software carries, so all 277 rows decode.

## Row-level differences

93 of 277 common identifiers differ in `unsigned`/`rawHex`. Diffed by `identifier` (required
because the EVA side is raw-only). Clusters:

- **RESS** (battery pack config) — largest block. Nearly every cell/pack parameter differs.
- **VSM** — `MODEL` 609 vs 610, `VSM_CONFIG_1` 4415 vs 15, over-temp thresholds, dummy words.
- **DRIVE_BY_WIRE** — regen torque maps, reverse limits, speed limits, motor params.
- **LIMP_MODE** — motor/drive temp limits, `VCU_ORIENTATION` 3 vs 1.
- **EVSE / FUEL_ECONOMY** — charger config.
- **SAFETY** — the `TABLE_TYPE` rows themselves (4119 vs 4115).

### ⚠️ Caveat on interpreting the deltas

The `name`/`section` labels come **only from the ego (table 4119)** file. The EVA runs table
**4115**, so identifier-N does not necessarily map to the same parameter on both bikes. A
tell-tale sign of the layout shift: a long run of RESS rows (idents 4166–4215) reads a flat
`1000`/`100` on the EVA — those are almost certainly bytes from a different table being read
against the wrong labels, not real values. The only fully trustworthy differences are the raw
byte values (`unsigned`/`rawHex`) and the confirmed table-version difference. A clean
parameter-by-parameter comparison isn't possible without a decode table for 4115.
