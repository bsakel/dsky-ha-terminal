# RP2040-Zero firmware (to do)

Job: scan the key matrix, drive the 10 WS2812B status lights, and talk to the Pi over USB (CDC serial or HID + serial).

The firmware could be written with CircuitPython, MicroPython, Arduino-Pico or QMK/KMK.

| Signal | GPIO |
|---|---|
| ROW0 / ROW1 / ROW2 | GP28 / GP29 / GP15 |
| COL0…COL6 | GP9, GP10, GP11, GP12, GP13, GP26, GP27 |
| WS2812B data | GP14 |
| On-board RGB LED (RP2040-Zero) | GP16 |

The diodes are COL2ROW: drive the column, read the rows, with the rows pulled down. In KMK this is `DiodeOrientation.COL2ROW`.

| | COL0 | COL1 | COL2 | COL3 | COL4 | COL5 | COL6 |
|---|---|---|---|---|---|---|---|
| ROW0 | VERB | + | 7 | 8 | 9 | CLR | ENTR |
| ROW1 | NOUN | − | 4 | 5 | 6 | PRO | RSET |
| ROW2 | – | 0 | 1 | 2 | 3 | KEY REL | – |

LED chain order:

1. UPLINK ACTY
2. NO ATT
3. STBY
4. KEY REL
5. OPR ERR
6. TRACKER
7. RESTART
8. PROG
9. GIMBAL LOCK
10. TEMP
