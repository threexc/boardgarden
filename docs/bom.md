# Bill of Materials

## Network

**Project:** boardgarden  
**Tailnet:** oryx-coho.ts.net  

## Machines

| ID | Hostname | Tailscale FQDN | OS | Status |
|----|----------|----------------|----|--------|
| `ecogrid` | ecogrid | ecogrid.oryx-coho.ts.net | Debian 13 ("Trixie") | active |
| `ecovault` | ecovault | ecovault.oryx-coho.ts.net | Debian 13 ("Trixie") | active |
| `runner1` | megalith | megalith.oryx-coho.ts.net | Fedora 44 | active |
| `runner2` | microlith | microlith.oryx-coho.ts.net | Fedora 44 | planned |
| `github` | GitHub | — | — | active |

## Services

| ID | Service | Tailscale FQDN | Host | Protocol | Port | Role |
|----|---------|----------------|------|----------|------|------|
| `svc_forgejo` | tgamblin's Forgejo | forgejo.oryx-coho.ts.net | `ecogrid` | — | — | Git hosting + CI (Actions) |
| `svc_tftp` | TFTP server | — | `ecovault` | — | — | Serves bootable images to test targets |
| `svc_reports` | Test reports server | testreports.oryx-coho.ts.net | `ecovault` | — | — | Receives and displays test results |

## Software

| Host | Service | Package | Version | Role |
|------|---------|---------|---------|------|
| `ecogrid` | tgamblin's Forgejo | Forgejo | 15.0.1 | Git hosting + CI (Actions) |
| `ecovault` | TFTP server | tftpd-hpa | 5.2+20240610-3 | Serves bootable images to test targets |
| `ecovault` | Test reports server | nginx | 1.26.3-3+deb13u2 | Receives and displays test results |

## Target Boards

| ID | Label | Vendor | Model | Arch | Connection |
|----|-------|--------|-------|------|------------|
| `board_1` | bananapi-f3 | BananaPi | BPI-F3 | riscv64 (RVA22 + RVV 1.0) | serial + power + sd mux |
| `board_2` | muse-pi-pro | SpacemiT | Muse Pi Pro | riscv64 (RVA22 + RVV 1.0) | serial + power |
| `board_3` | orangepi-rv2 | OrangePi | OrangePi RV2 | riscv64 (RVA22 + RVV 1.0) | serial + power |
| `board_4` | qemuriscv64 | QEMU | RVA23U64 | riscv64 (RVA23U64) | virtual |

| power | BayLibre CoPilot | BayLibre_Copilot_Lite_V1.2 | Power control |
| serial | Raspberry Pi Debug Probe | Debug_Probe__CMSIS-DAP_0101 | USB-to-UART bridge |
| SD mux | USB SD Mux | usb-sd-mux_rev4.0 | USB SD Mux controller |
| power | BayLibre CoPilot | BayLibre_Copilot_Lite_V1.2 | Power control |
| serial | Raspberry Pi Debug Probe | Debug_Probe__CMSIS-DAP_0101 | USB-to-UART bridge |
| power | BayLibre CoPilot | BayLibre_Copilot_Lite_V1.2 | Power control |
| serial | Raspberry Pi Debug Probe | Debug_Probe__CMSIS-DAP_0101 | USB-to-UART bridge |