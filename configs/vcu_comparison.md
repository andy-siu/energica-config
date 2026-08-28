# VCU configuration comparison

**2021-eva-corsa-clienti** (read 2026-08-25, `2021-eva-corsa-clienti/stock`) vs **2023-ego-rs** (read 2026-08-24, `2023-ego-rs/stock`)

| Metric | Count |
| --- | ---: |
| Shared parameters compared | 204 |
| Shared params that differ | 19 |
| Identical | 185 |
| Params unique to one table | 142 |

Compared **by parameter name**: the two bikes run different VCU table versions, so the same identifier can decode to a different parameter on each bike. Only parameters present on both bikes are compared below; the rest are listed as table-layout differences.

## Charts

### Throttle Curve 1 — output vs. throttle position

|  | 2021-eva-corsa-clienti | 2023-ego-rs |
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

|  | 2021-eva-corsa-clienti | 2023-ego-rs |
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

|  | 2021-eva-corsa-clienti | 2023-ego-rs |
| --- | ---: | ---: |
| MAP0 | 1250 | 1250 |
| MAP1 | 1450 | 1450 |
| MAP2 | 550 | 550 |
| MAP3 | 1200 | 1200 |

### Ride maps — torque cap per map

|  | 2021-eva-corsa-clienti | 2023-ego-rs |
| --- | ---: | ---: |
| MAP0 | 1800 | 1800 |
| MAP1 | 2150 | 2150 |
| MAP2 | 1400 | 1400 |
| MAP3 | 1200 | 1200 |

### Regen torque per map

|  | 2021-eva-corsa-clienti | 2023-ego-rs |
| --- | ---: | ---: |
| MAP0 | 10 | 10 |
| MAP1 | 23 | 20 |
| MAP2 | 35 | 30 |
| MAP3 | 45 | 40 |

## Parameter differences by section

### VSM (4 differ)

| Parameter | ID | 2021-eva-corsa-clienti | 2023-ego-rs |
| --- | ---: | ---: | ---: |
| DRIVE_OVER_TEMP | 4116 | 82 | 155 |
| MODEL | 4111 | 610 | 609 |
| MOTOR_OVER_TEMP | 4117 | 125 | 185 |
| VSM_CONFIG_1 | 4112 | 15 | 4415 |

### EVSE (1 differ)

| Parameter | ID | 2021-eva-corsa-clienti | 2023-ego-rs |
| --- | ---: | ---: | ---: |
| FCHG_CURRENT_GAIN | 4355 | 333 | 225 |

### LIMP_MODE (3 differ)

| Parameter | ID | 2021-eva-corsa-clienti | 2023-ego-rs |
| --- | ---: | ---: | ---: |
| LIMP_DRIVE_T | 4310 | 72 | 150 |
| LIMP_MOTOR_T | 4306 | 125 | 180 |
| VCU_ORIENTATION | 4318 | 1 | 3 |

### DRIVE_BY_WIRE 1/2 (9 differ)

| Parameter | ID | 2021-eva-corsa-clienti | 2023-ego-rs |
| --- | ---: | ---: | ---: |
| REGEN_MAP1_TRQ | 4160 | 23 | 20 |
| REGEN_MAP2_TRQ | 4161 | 35 | 30 |
| REGEN_MAP3_TRQ | 4162 | 45 | 40 |
| REVERSE_MAX_SPD | 4165 | 175 | 45 |
| REVERSE_TORQUE_LIMIT | 4163 | 700 | 600 |
| REVERSE_TORQUE_SLEWRATE_LIMIT | 4164 | 12000 | 200 |
| SPEED_LIMIT | 4241 | 223 | 231 |
| SPEED_LIMIT_ECO | 4242 | 90 | 85 |
| SPEED_LIMIT_SPORT | 4240 | 223 | 240 |

### SAFETY (2 differ)

| Parameter | ID | 2021-eva-corsa-clienti | 2023-ego-rs |
| --- | ---: | ---: | ---: |
| TABLE_TYPE_uC | 4372 | 4115 | 4119 |
| TABLE_TYPE_uS | 4373 | 4115 | 4119 |

## Table-layout differences

Parameters that exist on only one bike's parameter table — not comparable as values.

### Only in 2021-eva-corsa-clienti (73)

- BATTERY_TRICKLE_CHG_T
- BATTERY_UNBALANCE_WINDOW
- CELL_COUNT_C
- CELL_COUNT_S
- CELL_OVER_VOLTAGE
- CELL_UNDERVOLTAGE_WARNING
- CELL_UNDER_VOLTAGE
- DBW_DUMMY_WORD11
- DBW_DUMMY_WORD12
- DBW_DUMMY_WORD13
- DBW_DUMMY_WORD14
- DBW_DUMMY_WORD15
- DBW_DUMMY_WORD16
- DBW_DUMMY_WORD17
- DC_CHG_COMPLETE_TH
- DC_OVERSHOOT
- EVSE_DUMMY_WORD3
- FPOSLIGHTS_MAX_CURR_TH
- FPOSLIGHTS_MIN_CURR_TH
- LM_TYPE
- RegenFade_0
- RegenFade_1
- RegenFade_10
- RegenFade_11
- RegenFade_12
- RegenFade_13
- RegenFade_14
- RegenFade_15
- RegenFade_16
- RegenFade_17
- RegenFade_18
- RegenFade_19
- RegenFade_2
- RegenFade_20
- RegenFade_21
- RegenFade_22
- RegenFade_23
- RegenFade_24
- RegenFade_3
- RegenFade_4
- RegenFade_5
- RegenFade_6
- RegenFade_7
- RegenFade_8
- RegenFade_9
- TARGET_VOLTAGE
- TH_HIGH_B_PACK_V
- TH_LOW_B_PACK_V
- ThrottleNeutralPosition_1
- ThrottleNeutralPosition_10
- ThrottleNeutralPosition_11
- ThrottleNeutralPosition_12
- ThrottleNeutralPosition_13
- ThrottleNeutralPosition_14
- ThrottleNeutralPosition_15
- ThrottleNeutralPosition_16
- ThrottleNeutralPosition_17
- ThrottleNeutralPosition_18
- ThrottleNeutralPosition_19
- ThrottleNeutralPosition_2
- ThrottleNeutralPosition_20
- ThrottleNeutralPosition_21
- ThrottleNeutralPosition_22
- ThrottleNeutralPosition_23
- ThrottleNeutralPosition_24
- ThrottleNeutralPosition_25
- ThrottleNeutralPosition_3
- ThrottleNeutralPosition_4
- ThrottleNeutralPosition_5
- ThrottleNeutralPosition_6
- ThrottleNeutralPosition_7
- ThrottleNeutralPosition_8
- ThrottleNeutralPosition_9

### Only in 2023-ego-rs (69)

- BALANCING_WINDOW_AC
- BALANCING_WINDOW_DC
- BATTERY_TRICKLECHG_T
- BATTERY_UNBALANCE
- CELLV_HCA
- CELLV_KA
- CELLV_KAD
- CELLV_KAI
- CELLV_LCA
- CELL_COUNT
- CELL_NOMINAL
- CELL_OVERVOLTAGE
- CELL_REST
- CELL_TARGET_AC
- CELL_TARGET_DC
- CELL_UNDERVOLTAGE
- CELL_UNDERVOLTAGE_WARN
- CHARGER_TYPE
- CHG_OVERSHOOT_AC
- CHG_OVERSHOOT_DC
- CHG_OVERVOLTAGE
- EE_EVSE_DUMMY_1
- EE_EVSE_DUMMY_2
- EE_EVSE_DUMMY_3
- FUELECONOMY_DUMMY_WORD1
- FUELECONOMY_DUMMY_WORD2
- HIGH_PACK_V_DELTA
- LOW_PACK_V_DELTA
- MOTOR_MAX_SPD
- MOTOR_TYPE
- NT_SPD_MT_1_2
- NT_SPD_MT_3
- NT_SPD_TH
- NT_TRQ_MT_1_2
- NT_TRQ_MT_3
- PACKV_KA
- PACKV_KAD
- PACKV_KAI
- PACK_LPA
- POSLIGHTS_MAX_CURR_TH
- POSLIGHTS_MIN_CURR_TH
- RESS_DUMMY_WORD34
- RESS_DUMMY_WORD35
- RESS_DUMMY_WORD36
- RESS_DUMMY_WORD37
- RESS_DUMMY_WORD38
- RESS_DUMMY_WORD39
- RESS_DUMMY_WORD40
- RESS_DUMMY_WORD41
- RESS_DUMMY_WORD42
- RESS_DUMMY_WORD43
- RESS_DUMMY_WORD44
- RESS_DUMMY_WORD45
- RESS_DUMMY_WORD46
- RESS_DUMMY_WORD47
- RESS_DUMMY_WORD48
- RESS_DUMMY_WORD49
- RESS_DUMMY_WORD50
- R_BRAKE_POPUP
- TARGET_AC
- TARGET_DC
- VARIANT_CODING
- VSM_DUMMY_WORD1
- VSM_DUMMY_WORD12
- VSM_DUMMY_WORD2
- VSM_DUMMY_WORD3
- VSM_DUMMY_WORD4
- VSM_DUMMY_WORD6
- VSM_DUMMY_WORD7
