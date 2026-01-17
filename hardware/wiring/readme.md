Wiring for E-ink Display

Raspberry Pi Zero 2 W   →   E-Ink Display
---------------------------------------
3.3V  (Pin 1)           →   VCC
GND   (Pin 6)           →   GND

GPIO10 (Pin 19) MOSI    →   DIN
GPIO11 (Pin 23) SCLK    →   CLK
GPIO8  (Pin 24) CE0     →   CS

GPIO25 (Pin 22)         →   DC
GPIO17 (Pin 11)         →   RST
GPIO24 (Pin 18)         →   BUSY

---------

Wiring for Touch Buttons

Power:
3.3V (Pin 1) → VCC
GND  (Pin 6) → GND

Signals:
GPIO5  (Pin 29) → Button A (Next Page)
GPIO6  (Pin 31) → Button D (Previous Page)
GPIO13 (Pin 33) → Button M (Menu)
