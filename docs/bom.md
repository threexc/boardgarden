# Bill of Materials

## Network

**Project:** boardgarden  
**Tailnet:** tailscale.baylibre.com  

## Machines

| ID | Hostname | Tailscale FQDN | OS | Model | Specs | Status |
|----|----------|----------------|----|-------|-------|--------|
| `halifax` | halifax | halifax.tailscale.baylibre.com | Debian 13 ("Trixie") | ThinkCentre M75q-1 | AMD Ryzen 5 PRO 3400GE<br/>16 GB DDR4 RAM | active |
| `coordinator` | labgrid-coordinator | labgrid-coordinator.tailscale.baylibre.com | — | — | — | active |
| `runner1` | blacksmith | blacksmith.tailscale.baylibre.com | Debian 13 | ThinkCentre M720q | Intel i9-9900T<br/>64 GB DDR4 RAM | active |
| `runner2` | microlith | microlith.tailscale.baylibre.com | Fedora 44 | ThinkCentre M75q-1 | AMD Ryzen 5 PRO 3400GE<br/>16 GB DDR4 RAM | active |

## Services

| ID | Service | Tailscale FQDN | Host | Protocol | Port | Role |
|----|---------|----------------|------|----------|------|------|

## Software

| Host | Service | Package | Version | Role |
|------|---------|---------|---------|------|

## Target Boards

| ID | Label | Vendor | Model | Arch | Connection | Status |
|----|-------|--------|-------|------|------------|--------|
| `board_1` | BananaPi F3 | BananaPi | [BPI-F3](https://wiki.banana-pi.org/Banana_Pi_BPI-F3) | riscv64 (RVA22 + RVV 1.0) | serial + power + sd mux | active |
| `board_2` | Muse Pi Pro | SpacemiT | [Muse Pi Pro](https://www.spacemit.com/muse-pi-pro/) | riscv64 (RVA22 + RVV 1.0) | serial + power | active |
| `board_3` | Milk-V Duo 256M | Milk-V | [Milk-V Duo 256M](https://milkv.io/docs/duo/getting-started/duo256m) | riscv64 (RV64GCV) | serial + power + sdmux | active |
| `board_4` | K3 Pico-ITX | Sipeed | [K3 Pico-ITX](https://sipeed.com/k3) | riscv64 (RVA23) | serial + power | active |
| `board_5` | BeagleV-Fire | BeagleBoard.org | [BeagleV-Fire](https://www.beagleboard.org/boards/beaglev-fire) | riscv64 (RV64GC, PolarFire SoC) | serial + power | active |

### BananaPi F3

| Interface | Part | Part Number | Role |
|-----------|------|-------------|------|
| power | [BayLibre CoPilot](https://baylibre.com/copilot/) | BayLibre_Copilot_Lite_V1.2 | Power control |
| serial | [Raspberry Pi Debug Probe](https://www.raspberrypi.com/products/debug-probe/) | Debug_Probe__CMSIS-DAP_0101 | USB-to-UART bridge |
| SD mux | [USB SD Mux](https://linux-automation.com/en/products/usb-sd-mux.html) | usb-sd-mux_rev4.0 | USB SD Mux controller |

### Muse Pi Pro

| Interface | Part | Part Number | Role |
|-----------|------|-------------|------|
| power | [BayLibre CoPilot](https://baylibre.com/copilot/) | BayLibre_Copilot_Lite_V1.2 | Power control |
| serial | [Raspberry Pi Debug Probe](https://www.raspberrypi.com/products/debug-probe/) | Debug_Probe__CMSIS-DAP_0101 | USB-to-UART bridge |

### Milk-V Duo 256M

| Interface | Part | Part Number | Role |
|-----------|------|-------------|------|
| power | [BayLibre CoPilot](https://baylibre.com/copilot/) | BayLibre_Copilot_Lite_V1.2 | Power control |
| serial | [Raspberry Pi Debug Probe](https://www.raspberrypi.com/products/debug-probe/) | Debug_Probe__CMSIS-DAP_0101 | USB-to-UART bridge |
| SD mux | [USB SD Mux](https://linux-automation.com/en/products/usb-sd-mux.html) | usb-sd-mux_rev4.0 | USB SD Mux controller |

### K3 Pico-ITX

| Interface | Part | Part Number | Role |
|-----------|------|-------------|------|
| power | [BayLibre CoPilot](https://baylibre.com/copilot/) | BayLibre_Copilot_Lite_V1.2 | Power control |
| serial | [Raspberry Pi Debug Probe](https://www.raspberrypi.com/products/debug-probe/) | Debug_Probe__CMSIS-DAP_0101 | USB-to-UART bridge |

### BeagleV-Fire

| Interface | Part | Part Number | Role |
|-----------|------|-------------|------|
| power | [BayLibre CoPilot](https://baylibre.com/copilot/) | BayLibre_Copilot_Lite_V1.2 | Power control |
| serial | [Raspberry Pi Debug Probe](https://www.raspberrypi.com/products/debug-probe/) | Debug_Probe__CMSIS-DAP_0101 | USB-to-UART bridge |
