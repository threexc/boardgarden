# Bill of Materials

## Network

**Project:** boardgarden  
**Tailnet:** oryx-coho.ts.net  

## Machines

| ID | Hostname | Tailscale FQDN | OS | Model | Specs | Status |
|----|----------|----------------|----|-------|-------|--------|
| `ecogrid` | ecogrid | ecogrid.oryx-coho.ts.net | Debian 13 ("Trixie") | ThinkCentre M75q-1 | AMD Ryzen 5 PRO 3400GE<br/>16 GB DDR4 RAM | active |
| `ecovault` | ecovault | ecovault.oryx-coho.ts.net | Debian 13 ("Trixie") | ThinkCentre M715q | AMD Ryzen 3 PRO 2200GE<br/>16 GB DDR4 RAM | active |
| `runner1` | megalith | megalith.oryx-coho.ts.net | Fedora 44 | [Custom Build](https://www.asrock.com/MB/AMD/B650E%20Taichi/index.asp) | AMD Ryzen 9 7900<br/>64 GB DDR5 RAM | active |
| `runner2` | microlith | microlith.oryx-coho.ts.net | Fedora 44 | ThinkCentre M75q-1 | AMD Ryzen 5 PRO 3400GE<br/>16 GB DDR4 RAM | active |
| `github` | GitHub | — | — | — | — | active |

## Services

| ID | Service | Tailscale FQDN | Host | Protocol | Port | Role |
|----|---------|----------------|------|----------|------|------|

## Software

| Host | Service | Package | Version | Role |
|------|---------|---------|---------|------|

## Target Boards

| ID | Label | Vendor | Model | Arch | Connection |
|----|-------|--------|-------|------|------------|
| `board_1` | BananaPi F3 | BananaPi | [BPI-F3](https://wiki.banana-pi.org/Banana_Pi_BPI-F3) | riscv64 (RVA22 + RVV 1.0) | serial + power + sd mux |
| `board_2` | Muse Pi Pro | SpacemiT | [Muse Pi Pro](https://www.spacemit.com/muse-pi-pro/) | riscv64 (RVA22 + RVV 1.0) | serial + power |
| `board_3` | OrangePi RV2 | OrangePi | [OrangePi RV2](http://www.orangepi.org/html/hardWare/computerAndMicrocontrollers/details/Orange-Pi-RV2.html) | riscv64 (RVA22 + RVV 1.0) | serial + power |
| `board_4` | qemuriscv64 | QEMU | RVA23S64 | riscv64 (RVA23) | virtual |
| `board_5` | K3 Pico-ITX | Sipeed | K3 Pico-ITX | riscv64 (RVA23) | serial + power + sd mux |

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

### OrangePi RV2

| Interface | Part | Part Number | Role |
|-----------|------|-------------|------|
| power | [BayLibre CoPilot](https://baylibre.com/copilot/) | BayLibre_Copilot_Lite_V1.2 | Power control |
| serial | [Raspberry Pi Debug Probe](https://www.raspberrypi.com/products/debug-probe/) | Debug_Probe__CMSIS-DAP_0101 | USB-to-UART bridge |

### K3 Pico-ITX

| Interface | Part | Part Number | Role |
|-----------|------|-------------|------|
| power | [BayLibre CoPilot](https://baylibre.com/copilot/) | BayLibre_Copilot_Lite_V1.2 | Power control |
| serial | [Raspberry Pi Debug Probe](https://www.raspberrypi.com/products/debug-probe/) | Debug_Probe__CMSIS-DAP_0101 | USB-to-UART bridge |
| SD mux | [USB SD Mux](https://linux-automation.com/en/products/usb-sd-mux.html) | usb-sd-mux_rev4.0 | USB SD Mux controller |
