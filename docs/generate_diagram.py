#!/usr/bin/env python3
"""
generate_diagram.py
Convert network.yaml → network.mmd (Mermaid) + bom.md (Bill of Materials)

Usage:
    python generate_diagram.py [--yaml network.yaml] [--mmd network.mmd] [--bom bom.md]

Requirements:
    pip install pyyaml
Render:
    npm install -g @mermaid-js/mermaid-cli
    mmdc -i network.mmd -o network.svg
    mmdc -i network.mmd -o network.png -w 2400
"""

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML not found. Run: pip install pyyaml")

# ── Styles ────────────────────────────────────────────────────────────────────

STYLES = {
    "machine":  "fill:#dbeafe,stroke:#3b82f6,color:#1e3a5f",
    "planned":  "fill:#f0fdf4,stroke:#86efac,color:#14532d",
    "external": "fill:#f3f4f6,stroke:#9ca3af,color:#374151",
    "service":  "fill:#fef9c3,stroke:#d97706,color:#713f12",
    "board":    "fill:#fce7f3,stroke:#ec4899,color:#831843",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def clean(val):
    """Return val if it's a non-null, non-tilde string, else None."""
    if val is None or val == "~":
        return None
    return str(val)


def svc_label(svc):
    """Label for a service node: name + tailscale FQDN (if set) + protocol/port."""
    parts = []
    ts     = clean(svc.get("tailscale_name"))
    domain = svc.get("_tailnet_domain", "")
    if ts and domain:
        parts.append(f"<i>{ts}.{domain}</i>")
    elif ts:
        parts.append(f"<i>{ts}</i>")
    proto = clean(svc.get("protocol"))
    port  = clean(svc.get("port"))
    if proto and port:
        parts.append(f"{proto}:{port}")
    elif proto:
        parts.append(proto)

    # fallback when no Tailscale name is present
    return "<br/>".join(parts) if parts else svc["label"]  # fallback when no Tailscale name is present


def machine_label(m):
    ts_domain = m.get("_tailnet_domain", "")
    label = m["label"]

    parts = []
    if ts_domain and m.get("status") != "planned":
        parts.append(f"<i>{m['tailscale_name']}.{ts_domain}</i>")
    else:
        parts.append(label)

    hw = m.get("hardware", {})
    if hw:
        model = clean(hw.get("model"))
        if model:
            parts.append(model)
        for spec in hw.get("specs", []):
            s = clean(spec)
            if s:
                parts.append(s)

    return "<br/>".join(parts)


def link_arrow(lnk):
    style = lnk.get("style", "solid")
    ltype = lnk.get("type", "logical")
    if ltype == "physical":
        return "==>"           # thick solid — physical cable
    if style == "dashed":
        return "-..->"
    return "-->"


def link_label(lnk):
    label = lnk.get("label", "")
    interfaces = lnk.get("interfaces", [])
    if interfaces:
        parts = [i["label"] for i in interfaces if i.get("label")]
        label = " / ".join(parts)
    else:
        hw = lnk.get("hardware", [])
        hw_str = ", ".join(h["part"] for h in hw if clean(h.get("part")))
        if hw_str:
            label = f"{label} ({hw_str})" if label else hw_str
    return label


# ── Mermaid ───────────────────────────────────────────────────────────────────

def generate_mermaid(data):
    net      = data.get("network", {})
    machines = data.get("machines", [])
    services = data.get("services", [])
    boards   = data.get("boards", [])
    links    = data.get("links", [])

    tailnet_domain = clean(net.get("tailnet_domain", ""))

    # Annotate machines and services with tailnet domain for label rendering
    for m in machines:
        m["_tailnet_domain"] = tailnet_domain if clean(m.get("tailscale_name")) else ""
    for svc in services:
        svc["_tailnet_domain"] = tailnet_domain

    lines = [
        '%%{init: {"theme": "default", "flowchart": {"htmlLabels": true, "nodeSpacing": 30, "rankSpacing": 60, "defaultRenderer": "elk"}, "themeVariables": {"fontSize": "20px", "fontFamily": "New Computer Modern"}} }%%' "flowchart LR",
    ]

    # ── Tailnet boundary ──────────────────────────────────────────────
    lines.append('  subgraph tailnet["🔒 Tailnet"]')

    # ── Machine nodes ─────────────────────────────────────────────────
    machine_ids, planned_ids, external_ids = [], [], []
    for m in machines:
        mid    = m["id"]
        label  = machine_label(m)
        status = m.get("status", "")
        mtype  = m.get("type", "machine")

        if mtype == "external":
            lines.append(f'    {mid}{{{{"{label}"}}}}')
            external_ids.append(mid)
        elif status == "planned":
            lines.append(f'    {mid}["{label}<br/><i>(planned)</i>"]')
            planned_ids.append(mid)
        else:
            lines.append(f'    {mid}["{label}"]')
            machine_ids.append(mid)

    # ── Service nodes ─────────────────────────────────────────────────
    svc_ids = []
    for svc in services:
        sid   = svc["id"]
        label = svc_label(svc)
        lines.append(f'    {sid}(("{label}"))')   # double-circle = service endpoint
        svc_ids.append(sid)

    # ── Board subgraph ────────────────────────────────────────────────
    board_ids = []
    if boards:
        lines.append('    subgraph boards["Test Targets"]')
        lines.append("      direction TB")
        for b in boards:
            bid   = b["id"]
            label = clean(b.get("label")) or clean(b.get("model")) or bid
            arch  = clean(b.get("arch"))
            # Extract extension profile from inside parentheses if present,
            # e.g. "riscv64 (RVA22 + RVV 1.0)" → "RVA22 + RVV 1.0"; else use as-is.
            if arch and "(" in arch:
                arch = arch[arch.index("(") + 1 : arch.rindex(")")].strip()
            full  = f"{label}<br/>{arch}" if arch else label
            lines.append(f'      {bid}["{full}"]')
            board_ids.append(bid)
        lines.append("    end")

    lines.append("  end")  # end tailnet

    # ── hosted-on edges (service → machine) ──────────────────────────
    lines.append("")
    lines.append("  %% ── Hosted-on relationships ──")
    for svc in services:
        host = svc.get("host")
        if host:
            lines.append(f"  {svc['id']} -.-|hosted on| {host}")

    # ── Explicit links ────────────────────────────────────────────────
    if links:
        lines.append("")
        lines.append("  %% ── Links ──")
        for lnk in links:
            arrow = link_arrow(lnk)
            label = link_label(lnk)
            src, dst = (lnk["to"], lnk["from"]) if lnk.get("reverse") else (lnk["from"], lnk["to"])
            if label:
                lines.append(f'  {src} {arrow}|"{label}"| {dst}')
            else:
                lines.append(f'  {src} {arrow} {dst}')

    # ── Styles ────────────────────────────────────────────────────────
    lines.append("")
    lines.append("  %% ── Styles ──")

    for cls, ids in [
        ("machine",  machine_ids),
        ("planned",  planned_ids),
        ("external", external_ids),
        ("service",  svc_ids),
        ("board",    board_ids),
    ]:
        if ids:
            lines.append(f'  classDef {cls} {STYLES[cls]}')
            lines.append(f'  class {",".join(ids)} {cls}')

    return "\n".join(lines)


# ── BOM ───────────────────────────────────────────────────────────────────────

def generate_bom(data):
    net      = data.get("network", {})
    machines = data.get("machines", [])
    services = data.get("services", [])
    boards   = data.get("boards", [])
    links    = data.get("links", [])
    real_boards = [b for b in boards if b.get("type") != "connector"]

    tailnet_domain = clean(net.get("tailnet_domain", ""))

    out = ["# Bill of Materials\n"]

    # Network
    out.append("## Network\n")
    if clean(net.get("name")):
        out.append(f'**Project:** {net["name"]}  ')
    if tailnet_domain:
        out.append(f'**Tailnet:** {tailnet_domain}  ')
    out.append("")

    # Machines
    out.append("## Machines\n")
    out.append("| ID | Hostname | Tailscale FQDN | OS | Model | Specs | Status |")
    out.append("|----|----------|----------------|----|-------|-------|--------|")
    for m in machines:
        ts = clean(m.get("tailscale_name"))
        fqdn = f"{ts}.{tailnet_domain}" if ts and tailnet_domain else (ts or "—")
        os_  = clean(m.get("os")) or "—"
        status = m.get("status", "active")
        hw = m.get("hardware", {})
        model = clean(hw.get("model")) if hw else None
        url   = clean(hw.get("url"))   if hw else None
        if model and url:
            model_cell = f"[{model}]({url})"
        elif model:
            model_cell = model
        else:
            model_cell = "—"
        specs_list = [clean(s) for s in hw.get("specs", [])] if hw else []
        specs_cell = "<br/>".join(s for s in specs_list if s) or "—"
        out.append(f'| `{m["id"]}` | {m["label"]} | {fqdn} | {os_} | {model_cell} | {specs_cell} | {status} |')
    out.append("")

    # Services
    out.append("## Services\n")
    out.append("| ID | Service | Tailscale FQDN | Host | Protocol | Port | Role |")
    out.append("|----|---------|----------------|------|----------|------|------|")
    for svc in services:
        ts    = clean(svc.get("tailscale_name"))
        fqdn  = f"{ts}.{tailnet_domain}" if ts and tailnet_domain else (ts or "—")
        proto = clean(svc.get("protocol")) or "—"
        port  = clean(svc.get("port")) or "—"
        out.append(
            f'| `{svc["id"]}` | {svc["label"]} | {fqdn} | `{svc.get("host","—")}` '
            f'| {proto} | {port} | {svc.get("role","—")} |'
        )
    out.append("")

    # Software
    out.append("## Software\n")
    out.append("| Host | Service | Package | Version | Role |")
    out.append("|------|---------|---------|---------|------|")
    for svc in services:
        for sw in svc.get("software", []):
            name = clean(sw.get("name"))
            if not name:
                continue
            ver  = clean(sw.get("version")) or "—"
            out.append(
                f'| `{svc.get("host","—")}` | {svc["label"]} '
                f'| {name} | {ver} | {svc.get("role","—")} |'
            )
    out.append("")

    # Boards
    if boards:
        out.append("## Target Boards\n")
        out.append("| ID | Label | Vendor | Model | Arch | Connection |")
        out.append("|----|-------|--------|-------|------|------------|")
        for b in boards:
            label  = clean(b.get("label"))  or "—"
            vendor = clean(b.get("vendor")) or "—"
            model  = clean(b.get("model"))  or "—"
            url    = clean(b.get("url"))
            model_cell = f"[{model}]({url})" if url and model != "—" else model
            out.append(
                f'| `{b["id"]}` | {label} | {vendor} | {model_cell} '
                f'| {b.get("arch","—")} | {b.get("connection","—")} |'
            )
        out.append("")

        # Per-board hardware accessories
        board_links = [l for l in links if l.get("type") == "physical"
                       and (l.get("hardware") or l.get("interfaces"))]
        for board in real_boards:
            board_hw = []
            for lnk in board_links:
                if lnk["to"] != board["id"]:
                    continue
                for iface in lnk.get("interfaces", []):
                    for hw in iface.get("hardware", []):
                        board_hw.append((iface["label"], hw))
                for hw in lnk.get("hardware", []):
                    board_hw.append((lnk.get("label", "—"), hw))
            if board_hw:
                label = clean(board.get("label")) or board["id"]
                out.append(f"### {label}\n")
                out.append("| Interface | Part | Part Number | Role |")
                out.append("|-----------|------|-------------|------|")
                for iface_label, hw in board_hw:
                    pn   = clean(hw.get("pn"))  or "—"
                    part = hw["part"]
                    url  = clean(hw.get("url"))
                    part_cell = f"[{part}]({url})" if url else part
                    out.append(f'| {iface_label} | {part_cell} | {pn} | {hw.get("role","—")} |')
                out.append("")

    return "\n".join(out)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="network.yaml → Mermaid + BOM")
    parser.add_argument("--yaml", default="network.yaml")
    parser.add_argument("--mmd",  default="network.mmd")
    parser.add_argument("--bom",  default="bom.md")
    args = parser.parse_args()

    yaml_path = Path(args.yaml)
    if not yaml_path.exists():
        sys.exit(f"YAML file not found: {yaml_path}")

    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    Path(args.mmd).write_text(generate_mermaid(data))
    Path(args.bom).write_text(generate_bom(data))

    print(f"✓ Mermaid diagram → {args.mmd}")
    print(f"✓ Bill of Materials → {args.bom}")
    print()
    print("To render:")
    print(f"  mmdc -i {args.mmd} -o network.svg")
    print(f"  mmdc -i {args.mmd} -o network.png -w 2400")


if __name__ == "__main__":
    main()
