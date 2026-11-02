# K3 Pico-ITX: Automated Fastboot Setup Guide

This walks through configuring all aspects of preparing a SpacemiT K3 Pico-ITX development board for use withLabgrid's `fastboot` support in an automated testing environment. **It assumes that you already have at least one computer with a typical Linux distribution (e.g. Debian) preinstalled, with administrative access.** It also assumes that you have already read the [K3 Pico-ITX Getting Started Guide][getting-started-guide-ref], specifically on how to manually flash the board.

## 1. Hardware Setup

### 1.1 Requirements

- [K3 Pico-ITX][k3-pico-itx-ref] development board
- [BayLibre Copilot][baylibre-copilot-ref] helper board
- [BayLibre Copilot Relay Hat][baylibre-copilot-relay-ref] board
- 65W generic/laptop USB-C power supply for the K3 Pico-ITX
- One USB-C-to-C cable, for power connection from Copilot to K3 Pico-ITX input
- Two USB-A-to-C **or** two USB-C-to-C cables - one for connection from the Labgrid exporter machine to the BayLibre Copilot, and one for connection from the exporter machine to the K3 Pico-ITX flashing port
- Female-to-female breadboard wires or similar - three (3) for UART, six (6) for relay board
- (Optional) an ethernet cable for the board
- (Optional) a USB hub with ports matching the cable types used
- Soldering tools, a multimeter, and B-7000 glue or similar (recommended)
- Nylon or metal standoffs

### 1.2 Adding Custom Wiring to the K3 Pico-ITX

The K3 Pico-ITX [Getting Started Guide][getting-started-guide-ref] indicates that the `FDL` button must be held while briefly pressing the `RST` button to enter flashing mode. Wires must be attached to the solder points for each of these buttons, so that they can be connected to the Copilot Relay Hat and controlled remotely.

1. Remove the screws holding the heatsink in place (circled in red):

![K3 Pico-ITX heatsink screws](./images/PXL_20261102_185710772.MP.jpg)

2. Once the heatsink has been removed, note the six solder points along the bottom left of the board, corresponding to the `RST`, `FDL`, and `PWR` buttons (two pins each):

![K3 Pico-ITX `RST`, `FDL`, and `PWR` solder points](./images/PXL_20261102_190017319.MP.jpg)

3. Using six (6) breadboard wires, cut one end off each and strip them to expose the metal contacts. Leave the other end intact, since it will be attached to the relay hat later.
4. Solder wires to each pin for the `RST` (circled in red) and `FDL` (yellow) buttons. The `PWR` (light blue) button is optional.
5. Ensure there are no shorts between the pins after soldering by using a multimeter, as this could cause unexpected behaviour in testing.
6. (Recommended) apply glue along the board's edge near the newly-soldered pins, to help with strain relief. Make sure to give it time to dry/cure. The result should look something like:

![K3 Pico-ITX with wires soldered and glued to button pins](./images/IMG_3004.jpeg)

7. When finished, re-attach the board's heatsink.

### 1.3 Connecting the Devices

1. Attach the Copilot relay hat to the Copilot base board, including standoffs.
2. Connect three (3) breadboard wires from the K3 Pico-ITX UART header to the Copilot's UART pins, making sure that the `RX` pin on one side is connected to `TX` on the other, and vice versa.
3. Connect the wires soldered to the K3 Pico-ITX to the headers on the Copilot relay hat. For consistency with the configurations in this repository, the wiring should match that shown below:

![K3 Pico-ITX connected to Copilot relay hat](./images/IMG_3009.jpeg)

4. Connect the USB-C cable intended for fastboot between the PC (or USB hub) and the K3 Pico-ITX. Note that the [Getting Started Guide][getting-started-guide-ref] suggests that this should be connected after switching to flashing mode, but it works regardless.
5. Connect the USB-C-to-C cable between the Copilot and the K3 Pico-ITX's power input. Note that due to limitations with USB-C wiring, it is possible that one connection may need to be reversed for power passthrough to work. See the Copilot [getting started guide][baylibre-copilot-guide-ref] for more information.
6. Connect the USB-C power cable to the Copilot power input.
7. Connect the final USB-C cable between the PC (or USB hub) and the Copilot's control input.
8. (Optional, if in use) connect the Ethernet cable to the K3 Pico-ITX.
9. A completed setup may look something like:

![K3 Pico-ITX complete connection setup](./images/PXL_20261102_200947364.jpg)

## 2. Software Setup

### 2.1 Requirements

Under construction

## References


- [K3 Pico-ITX Getting Started Guide][getting-started-guide-ref]
- [K3 Pico-ITX][k3-pico-itx-ref]
- [BayLibre Copilot][baylibre-copilot-ref]
- [BayLibre Copilot Relay Hat][baylibre-copilot-relay-ref]
- [BayLibre Copilot Getting Started Guide][baylibre-copilot-guide-ref]

[getting-started-guide-ref]: https://docs.banana-pi.org/en/Pico-ITX/GettingStarted_K3Pico-ITX
[k3-pico-itx-ref]: https://www.bpi-shop.com/products/k3-pico-itx-spacemit-k3-8-cores--60tops-al-performance-wifi6.html
[baylibre-copilot-ref]: https://github.com/BayLibre/Copilot
[baylibre-copilot-relay-ref]: https://github.com/BayLibre/Copilot_Extension_Triple_Relays
[baylibre-copilot-guide-ref]: https://baylibre.github.io/Copilot/getting-started.html
