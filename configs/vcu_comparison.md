# VCU configuration comparison

**2023-ego-rs** (read 2026-08-24, `2023-ego-rs/S35`) vs **2023-ego-rs** (read 2026-08-24, `2023-ego-rs/stock`)

| Metric | Count |
| --- | ---: |
| Shared parameters compared | 273 |
| Shared params that differ | 8 |
| Identical | 265 |
| Params unique to one table | 0 |

Compared **by parameter name**: the two bikes run different VCU table versions, so the same identifier can decode to a different parameter on each bike. Only parameters present on both bikes are compared below; the rest are listed as table-layout differences.

## Charts

### Throttle Curve 1 — output vs. throttle position

|  | 2023-ego-rs | 2023-ego-rs |
| --- | ---: | ---: |
| 0% | 0 | 0 |
| 10% | 180 | 180 |
| 20% | 340 | 340 |
| 30% | 475 | 475 |
| 40% | 590 | 590 |
| 50% | 685 | 685 |
| 60% | 770 | 770 |
| 70% | 840 | 840 |
| 80% | 900 | 900 |
| 90% | 950 | 950 |
| 100% | 1000 | 1000 |

### Throttle Curve 2 — output vs. throttle position

|  | 2023-ego-rs | 2023-ego-rs |
| --- | ---: | ---: |
| 0% | 0 | 0 |
| 10% | 40 | 40 |
| 20% | 90 | 90 |
| 30% | 155 | 155 |
| 40% | 225 | 225 |
| 50% | 310 | 310 |
| 60% | 410 | 410 |
| 70% | 530 | 530 |
| 80% | 670 | 670 |
| 90% | 820 | 820 |
| 100% | 1000 | 1000 |

### Ride maps — power cap per map

|  | 2023-ego-rs | 2023-ego-rs |
| --- | ---: | ---: |
| MAP0 | 1250 | 1250 |
| MAP1 | 1450 | 1450 |
| MAP2 | 550 | 550 |
| MAP3 | 1200 | 1200 |

### Ride maps — torque cap per map

|  | 2023-ego-rs | 2023-ego-rs |
| --- | ---: | ---: |
| MAP0 | 1800 | 1800 |
| MAP1 | 2150 | 2150 |
| MAP2 | 1400 | 1400 |
| MAP3 | 1200 | 1200 |

### Regen torque per map

|  | 2023-ego-rs | 2023-ego-rs |
| --- | ---: | ---: |
| MAP0 | 10 | 10 |
| MAP1 | 20 | 20 |
| MAP2 | 30 | 30 |
| MAP3 | 40 | 40 |

## Parameter differences by section

### RESS (4 differ)

| Parameter | ID | 2023-ego-rs | 2023-ego-rs |
| --- | ---: | ---: | ---: |
| CELL_NOMINAL | 4177 | 3700 | 3650 |
| CELL_OVERVOLTAGE | 4174 | 4250 | 4200 |
| CELL_UNDERVOLTAGE | 4172 | 3400 | 3000 |
| CELL_UNDERVOLTAGE_WARN | 4173 | 3450 | 3200 |

### DRIVE_BY_WIRE 1/2 (4 differ)

| Parameter | ID | 2023-ego-rs | 2023-ego-rs |
| --- | ---: | ---: | ---: |
| REGEN_CURRENT_LIMIT | 4238 | 1400 | 1200 |
| SPEED_LIMIT | 4241 | 241 | 231 |
| SPEED_LIMIT_ECO | 4242 | 121 | 85 |
| SPEED_LIMIT_SPORT | 4240 | 241 | 240 |
