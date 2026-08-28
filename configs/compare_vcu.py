#!/usr/bin/env python3
"""Compare two Energica VCU parameter dumps and emit an HTML report.

Reads two ``vcu.json`` files (see CLAUDE.md for the schema), pairs their rows,
and writes a self-contained HTML report with:

  * headline stat tiles (rows compared, params that differ),
  * inline-SVG charts for throttle curves, ride maps and regen maps,
  * a section-grouped table of every differing parameter.

No third-party dependencies — the charts are hand-built SVG so the report opens
in any browser and the repo stays install-free.

Usage:
    python3 compare_vcu.py A/vcu.json B/vcu.json [-o report.html] \
        [--label-a NAME] [--label-b NAME]
"""
from __future__ import annotations

import argparse
import html
import json
import os
from collections import OrderedDict

# --- design tokens (from the dataviz reference palette, validated pair) --------
SERIES_A = "#2a78d6"   # categorical slot 1 (blue)  -> file A
SERIES_B = "#eb6834"   # categorical slot 2 (orange) -> file B
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SURFACE = "#fcfcfb"


def load_rows(path):
    """Return (meta, {identifier: row}) for a vcu.json dump."""
    with open(path) as fh:
        data = json.load(fh)
    rows = {r["identifier"]: r for r in data["rows"]}
    meta = {k: data.get(k) for k in ("readAt", "complete", "micros")}
    return meta, rows


def best_name(rows_a, rows_b, ident):
    """A parameter name, preferring whichever side decoded it (see CLAUDE.md).

    Raw-only rows carry ``name == null``; fall back to the identifier so the
    two dumps still line up.
    """
    for rows in (rows_a, rows_b):
        r = rows.get(ident)
        if r and r.get("name"):
            return r["name"]
    return f"#{ident}"


def curve(rows, prefix):
    """Ordered list of values for a numbered parameter family (e.g. ThrottleCurve1_)."""
    picked = [
        r for r in rows.values()
        if r.get("name") and r["name"].startswith(prefix)
        and r["name"][len(prefix):].isdigit()
    ]
    picked.sort(key=lambda r: int(r["name"][len(prefix):]))
    return [r["value"] for r in picked]


def value_by_name(rows, name):
    for r in rows.values():
        if r.get("name") == name:
            return r["value"]
    return None


# --- tiny SVG chart helpers ----------------------------------------------------
def esc(s):
    return html.escape(str(s))


def series_identical(series):
    """True when every series carries the same values (marks would overlap)."""
    if len(series) < 2:
        return False
    first = series[0][2]
    return all(ys == first for _, _, ys in series)


def identical_badge(width):
    """Top-right pill flagging that the plotted series coincide exactly."""
    w, h = 78, 20
    x, y = width - w - 12, 10
    return (f'<g><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" '
            f'fill="#eef4fc" stroke="rgba(11,11,11,.10)"/>'
            f'<text x="{x+w/2}" y="{y+14}" font-size="11" font-weight="600" '
            f'text-anchor="middle" fill="{SERIES_A}">identical</text></g>')


def line_chart(title, xlabels, series, width=680, height=360):
    """Multi-series line chart. ``series`` = [(label, color, [y...]), ...]."""
    pad_l, pad_r, pad_t, pad_b = 56, 24, 44, 52
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    n = len(xlabels)
    all_y = [y for _, _, ys in series for y in ys]
    ymax = max(all_y) if all_y else 1
    ymax = ymax or 1

    def px(i):
        return pad_l + (plot_w * i / (n - 1) if n > 1 else 0)

    def py(v):
        return pad_t + plot_h - (plot_h * v / ymax)

    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" '
             f'aria-label="{esc(title)}" font-family="system-ui,-apple-system,sans-serif">']
    parts.append(f'<rect width="{width}" height="{height}" fill="{SURFACE}"/>')
    parts.append(f'<text x="{pad_l}" y="24" font-size="15" font-weight="600" '
                 f'fill="{INK}">{esc(title)}</text>')
    if series_identical(series):
        parts.append(identical_badge(width))

    # y gridlines + ticks
    for g in range(5):
        v = ymax * g / 4
        y = py(v)
        parts.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{pad_l+plot_w}" '
                     f'y2="{y:.1f}" stroke="{GRID}" stroke-width="1"/>')
        parts.append(f'<text x="{pad_l-8}" y="{y+4:.1f}" font-size="11" '
                     f'text-anchor="end" fill="{MUTED}" '
                     f'font-variant-numeric="tabular-nums">{v:.0f}</text>')
    # x ticks (label every point; thin out if many)
    step = max(1, n // 11)
    for i, lab in enumerate(xlabels):
        if i % step and i != n - 1:
            continue
        parts.append(f'<text x="{px(i):.1f}" y="{height-pad_b+18}" font-size="11" '
                     f'text-anchor="middle" fill="{MUTED}">{esc(lab)}</text>')
    # baseline
    parts.append(f'<line x1="{pad_l}" y1="{pad_t+plot_h}" x2="{pad_l+plot_w}" '
                 f'y2="{pad_t+plot_h}" stroke="{AXIS}" stroke-width="1"/>')

    # series
    for label, color, ys in series:
        pts = " ".join(f"{px(i):.1f},{py(v):.1f}" for i, v in enumerate(ys))
        parts.append(f'<polyline points="{pts}" fill="none" stroke="{color}" '
                     f'stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>')
        for i, v in enumerate(ys):
            parts.append(f'<circle cx="{px(i):.1f}" cy="{py(v):.1f}" r="4.5" '
                         f'fill="{color}" stroke="{SURFACE}" stroke-width="1.5">'
                         f'<title>{esc(label)} — {esc(xlabels[i])}: {v}</title></circle>')

    # legend
    lx = pad_l + 6
    ly = pad_t - 10
    for label, color, _ in series:
        parts.append(f'<rect x="{lx}" y="{ly-9}" width="11" height="11" rx="2" fill="{color}"/>')
        parts.append(f'<text x="{lx+16}" y="{ly}" font-size="12" fill="{INK_2}">{esc(label)}</text>')
        lx += 20 + 8 * len(label)
    parts.append("</svg>")
    return "".join(parts)


def grouped_bar(title, categories, series, width=680, height=360, unit=""):
    """Grouped bar chart. ``series`` = [(label, color, [v...]), ...]."""
    pad_l, pad_r, pad_t, pad_b = 56, 24, 44, 60
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    ng = len(categories)
    ns = len(series)
    all_v = [v for _, _, vs in series for v in vs]
    vmax = max(all_v) if all_v else 1
    vmax = vmax or 1

    def py(v):
        return pad_t + plot_h - (plot_h * v / vmax)

    group_w = plot_w / ng
    gap = group_w * 0.18
    bar_w = (group_w - gap) / ns

    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" '
             f'aria-label="{esc(title)}" font-family="system-ui,-apple-system,sans-serif">']
    parts.append(f'<rect width="{width}" height="{height}" fill="{SURFACE}"/>')
    parts.append(f'<text x="{pad_l}" y="24" font-size="15" font-weight="600" '
                 f'fill="{INK}">{esc(title)}</text>')
    if series_identical(series):
        parts.append(identical_badge(width))
    for g in range(5):
        v = vmax * g / 4
        y = py(v)
        parts.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{pad_l+plot_w}" '
                     f'y2="{y:.1f}" stroke="{GRID}" stroke-width="1"/>')
        parts.append(f'<text x="{pad_l-8}" y="{y+4:.1f}" font-size="11" '
                     f'text-anchor="end" fill="{MUTED}" '
                     f'font-variant-numeric="tabular-nums">{v:.0f}</text>')
    parts.append(f'<line x1="{pad_l}" y1="{pad_t+plot_h}" x2="{pad_l+plot_w}" '
                 f'y2="{pad_t+plot_h}" stroke="{AXIS}" stroke-width="1"/>')

    for gi, cat in enumerate(categories):
        gx = pad_l + gi * group_w + gap / 2
        for si, (label, color, vs) in enumerate(series):
            v = vs[gi]
            x = gx + si * bar_w
            y = py(v)
            h = pad_t + plot_h - y
            # 2px surface gap between adjacent bars
            parts.append(f'<rect x="{x+1:.1f}" y="{y:.1f}" width="{bar_w-2:.1f}" '
                         f'height="{h:.1f}" rx="3" fill="{color}">'
                         f'<title>{esc(label)} — {esc(cat)}: {v}{esc(unit)}</title></rect>')
        parts.append(f'<text x="{gx+(group_w-gap)/2:.1f}" y="{height-pad_b+18}" '
                     f'font-size="11" text-anchor="middle" fill="{MUTED}">{esc(cat)}</text>')

    lx = pad_l + 6
    ly = pad_t - 10
    for label, color, _ in series:
        parts.append(f'<rect x="{lx}" y="{ly-9}" width="11" height="11" rx="2" fill="{color}"/>')
        parts.append(f'<text x="{lx+16}" y="{ly}" font-size="12" fill="{INK_2}">{esc(label)}</text>')
        lx += 20 + 8 * len(label)
    parts.append("</svg>")
    return "".join(parts)


def fmt(v):
    return "—" if v is None else esc(v)


def name_index(rows):
    """{name: row} for rows that carry a decoded name."""
    idx = {}
    for r in rows.values():
        if r.get("name"):
            idx.setdefault(r["name"], r)
    return idx


def build_report(path_a, path_b, label_a, label_b):
    meta_a, rows_a = load_rows(path_a)
    meta_b, rows_b = load_rows(path_b)

    # Both dumps are decoded, so compare BY PARAMETER NAME, not by identifier
    # (CLAUDE.md): the two bikes run different table versions, so the same
    # identifier slot can decode to different parameters. Diffing by identifier
    # would compare unrelated params that merely share a slot.
    idx_a = name_index(rows_a)
    idx_b = name_index(rows_b)
    common = idx_a.keys() & idx_b.keys()
    only_a = sorted(idx_a.keys() - idx_b.keys())
    only_b = sorted(idx_b.keys() - idx_a.keys())

    # feature diff on shared parameters, grouped by section
    diffs = OrderedDict()
    n_diff = 0
    for name in sorted(common):
        ra, rb = idx_a[name], idx_b[name]
        va, vb = ra["value"], rb["value"]
        if va == vb:
            continue
        n_diff += 1
        section = ra.get("section") or rb.get("section") or "unclassified"
        diffs.setdefault(section, []).append((ra["identifier"], name, va, vb))
    n_common = len(common)

    # Build chart datasets once; render both SVG (HTML) and tables (Markdown)
    # from the same specs so the two reports never drift.
    chart_specs = []

    # 1) throttle curves — output (0..1000) vs pedal position (11 breakpoints)
    xlabels = [f"{int(i*100/10)}%" for i in range(11)]
    for cn in ("1", "2"):
        ca = curve(rows_a, f"ThrottleCurve{cn}_")
        cb = curve(rows_b, f"ThrottleCurve{cn}_")
        if ca and cb and len(ca) == len(cb) == 11:
            chart_specs.append({
                "kind": "line", "unit": "",
                "title": f"Throttle Curve {cn} — output vs. throttle position",
                "cats": xlabels,
                "series": [(label_a, SERIES_A, ca), (label_b, SERIES_B, cb)]})

    # 2) ride maps — power & torque caps per map slot
    map_cats = ["MAP0", "MAP1", "MAP2", "MAP3"]
    pwr_a = [value_by_name(rows_a, f"{m}_PWR") for m in map_cats]
    pwr_b = [value_by_name(rows_b, f"{m}_PWR") for m in map_cats]
    trq_a = [value_by_name(rows_a, f"{m}_TORQUE") for m in map_cats]
    trq_b = [value_by_name(rows_b, f"{m}_TORQUE") for m in map_cats]
    if all(v is not None for v in pwr_a + pwr_b):
        chart_specs.append({
            "kind": "bar", "unit": "",
            "title": "Ride maps — power cap per map", "cats": map_cats,
            "series": [(label_a, SERIES_A, pwr_a), (label_b, SERIES_B, pwr_b)]})
    if all(v is not None for v in trq_a + trq_b):
        chart_specs.append({
            "kind": "bar", "unit": "",
            "title": "Ride maps — torque cap per map", "cats": map_cats,
            "series": [(label_a, SERIES_A, trq_a), (label_b, SERIES_B, trq_b)]})

    # 3) regen maps
    regen_a = [value_by_name(rows_a, f"REGEN_MAP{i}_TRQ") for i in range(4)]
    regen_b = [value_by_name(rows_b, f"REGEN_MAP{i}_TRQ") for i in range(4)]
    if all(v is not None for v in regen_a + regen_b):
        chart_specs.append({
            "kind": "bar", "unit": "",
            "title": "Regen torque per map", "cats": [f"MAP{i}" for i in range(4)],
            "series": [(label_a, SERIES_A, regen_a), (label_b, SERIES_B, regen_b)]})

    charts = []
    for spec in chart_specs:
        if spec["kind"] == "line":
            charts.append(line_chart(spec["title"], spec["cats"], spec["series"]))
        else:
            charts.append(grouped_bar(spec["title"], spec["cats"], spec["series"]))

    # 4) headline limits
    limit_names = ["TORQUE_LIMIT", "REGEN_TORQUE_LIMIT", "ACTIVE_CURRENT_LIMIT",
                   "REGEN_CURRENT_LIMIT", "SPEED_LIMIT", "SPEED_LIMIT_SPORT",
                   "SPEED_LIMIT_ECO", "MOTOR_MAX_SPD"]
    lim_a, lim_b, lim_cats = [], [], []
    for nm in limit_names:
        a, b = value_by_name(rows_a, nm), value_by_name(rows_b, nm)
        if a is not None and b is not None:
            lim_cats.append(nm.replace("_LIMIT", "").replace("_", " "))
            lim_a.append(a)
            lim_b.append(b)
    # scale differs wildly -> keep on one axis is misleading; skip a combined bar
    # and instead surface these in the table. (One axis rule.)

    html_str = render_html(label_a, label_b, path_a, path_b, meta_a, meta_b,
                           n_common, n_diff, charts, diffs, only_a, only_b)
    md_str = render_md(label_a, label_b, path_a, path_b, meta_a, meta_b,
                       n_common, n_diff, chart_specs, diffs, only_a, only_b)
    return html_str, md_str, diffs, only_a, only_b


def render_html(label_a, label_b, path_a, path_b, meta_a, meta_b,
                n_common, n_diff, charts, diffs, only_a, only_b):
    css = """
    :root { color-scheme: light; }
    body { font-family: system-ui,-apple-system,"Segoe UI",sans-serif;
           background:#f9f9f7; color:#0b0b0b; margin:0; padding:32px 24px; }
    .wrap { max-width: 980px; margin: 0 auto; }
    h1 { font-size: 24px; margin: 0 0 4px; }
    .sub { color:#52514e; margin: 0 0 24px; font-size: 14px; }
    .tiles { display:flex; gap:16px; flex-wrap:wrap; margin-bottom:28px; }
    .tile { background:#fcfcfb; border:1px solid rgba(11,11,11,.10); border-radius:12px;
            padding:16px 20px; min-width:150px; }
    .tile .n { font-size:30px; font-weight:650; }
    .tile .l { color:#52514e; font-size:13px; margin-top:2px; }
    .legend-a { color:#2a78d6; font-weight:600; }
    .legend-b { color:#eb6834; font-weight:600; }
    .charts { display:grid; grid-template-columns:repeat(auto-fit,minmax(420px,1fr)); gap:20px; }
    .card { background:#fcfcfb; border:1px solid rgba(11,11,11,.10); border-radius:12px;
            padding:8px; }
    .card svg { width:100%; height:auto; display:block; }
    h2 { font-size:18px; margin:36px 0 12px; }
    table { border-collapse:collapse; width:100%; font-size:13px; margin-bottom:20px;
            background:#fcfcfb; border:1px solid rgba(11,11,11,.10); border-radius:12px;
            overflow:hidden; }
    th,td { text-align:left; padding:7px 12px; border-bottom:1px solid #e1e0d9; }
    th { background:#f2f1ec; font-weight:600; }
    td.num { font-variant-numeric:tabular-nums; text-align:right; }
    .sec { margin:28px 0 8px; font-size:15px; font-weight:650; color:#0b0b0b; }
    .cnt { color:#898781; font-weight:400; font-size:13px; }
    """
    out = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
           '<meta name="viewport" content="width=device-width,initial-scale=1">',
           '<title>VCU comparison</title>', f'<style>{css}</style></head><body><div class="wrap">']
    out.append('<h1>VCU configuration comparison</h1>')

    out.append(f'<p class="sub"><span class="legend-a">{esc(label_a)}</span> '
               f'(read {read_date(meta_a)}, {esc(os.path.dirname(path_a))}) &nbsp;vs&nbsp; '
               f'<span class="legend-b">{esc(label_b)}</span> '
               f'(read {read_date(meta_b)}, {esc(os.path.dirname(path_b))})</p>')

    out.append('<div class="tiles">')
    out.append(f'<div class="tile"><div class="n">{n_common}</div>'
               f'<div class="l">shared parameters compared</div></div>')
    out.append(f'<div class="tile"><div class="n">{n_diff}</div>'
               f'<div class="l">shared params that differ</div></div>')
    out.append(f'<div class="tile"><div class="n">{n_common-n_diff}</div>'
               f'<div class="l">identical</div></div>')
    out.append(f'<div class="tile"><div class="n">{len(only_a)+len(only_b)}</div>'
               f'<div class="l">params unique to one table</div></div>')
    out.append('</div>')
    out.append('<p class="sub">Compared <b>by parameter name</b>: the two bikes '
               'run different VCU table versions, so the same identifier can decode '
               'to a different parameter on each bike. Only parameters present on '
               'both bikes are compared below; the rest are listed as table-layout '
               'differences.</p>')

    out.append('<h2>Charts</h2><div class="charts">')
    for svg in charts:
        out.append(f'<div class="card">{svg}</div>')
    out.append('</div>')

    out.append('<h2>Parameter differences by section</h2>')
    for section, items in diffs.items():
        out.append(f'<div class="sec">{esc(section)} '
                   f'<span class="cnt">({len(items)} differ)</span></div>')
        out.append('<table><thead><tr><th>Parameter</th><th>ID</th>'
                   f'<th class="num">{esc(label_a)}</th>'
                   f'<th class="num">{esc(label_b)}</th></tr></thead><tbody>')
        for ident, name, va, vb in items:
            out.append(f'<tr><td>{esc(name)}</td><td class="num">{ident}</td>'
                       f'<td class="num">{fmt(va)}</td><td class="num">{fmt(vb)}</td></tr>')
        out.append('</tbody></table>')

    if only_a or only_b:
        out.append('<h2>Table-layout differences</h2>')
        out.append('<p class="sub">Parameters that exist on only one bike\'s '
                   'parameter table — not comparable as values.</p>')
        out.append('<div class="charts">')
        for lbl, names in ((label_a, only_a), (label_b, only_b)):
            out.append('<div>')
            out.append(f'<div class="sec">Only in {esc(lbl)} '
                       f'<span class="cnt">({len(names)})</span></div>')
            out.append('<table><tbody>')
            for nm in names:
                out.append(f'<tr><td>{esc(nm)}</td></tr>')
            out.append('</tbody></table></div>')
        out.append('</div>')

    out.append('</div></body></html>')
    return "".join(out)


def read_date(meta):
    """UTC read date (YYYY-MM-DD) from a dump's readAt epoch-ms, or '?'."""
    import datetime
    t = meta.get("readAt")
    if not t:
        return "?"
    return datetime.datetime.fromtimestamp(
        t / 1000, datetime.timezone.utc).strftime("%Y-%m-%d")


def render_md(label_a, label_b, path_a, path_b, meta_a, meta_b,
              n_common, n_diff, chart_specs, diffs, only_a, only_b):
    """GitHub-flavoured Markdown twin of the HTML report.

    GitHub sanitises inline SVG in Markdown, so the hand-built charts can't
    travel; the underlying chart datasets are rendered as plain tables instead,
    which read fine in the repo browser.
    """
    def cell(v):
        return "—" if v is None else str(v)

    out = ["# VCU configuration comparison", ""]
    out.append(f"**{label_a}** (read {read_date(meta_a)}, "
               f"`{os.path.dirname(path_a)}`) vs "
               f"**{label_b}** (read {read_date(meta_b)}, "
               f"`{os.path.dirname(path_b)}`)")
    out.append("")

    # headline stats
    out.append("| Metric | Count |")
    out.append("| --- | ---: |")
    out.append(f"| Shared parameters compared | {n_common} |")
    out.append(f"| Shared params that differ | {n_diff} |")
    out.append(f"| Identical | {n_common - n_diff} |")
    out.append(f"| Params unique to one table | {len(only_a) + len(only_b)} |")
    out.append("")
    out.append("Compared **by parameter name**: the two bikes run different VCU "
               "table versions, so the same identifier can decode to a different "
               "parameter on each bike. Only parameters present on both bikes are "
               "compared below; the rest are listed as table-layout differences.")
    out.append("")

    # chart datasets as tables (SVG doesn't survive GitHub's sanitiser)
    if chart_specs:
        out.append("## Charts")
        out.append("")
        for spec in chart_specs:
            out.append(f"### {spec['title']}")
            out.append("")
            labels = [s[0] for s in spec["series"]]
            out.append("| " + " | ".join([""] + labels) + " |")
            out.append("| " + " | ".join(["---"] + ["---:"] * len(labels)) + " |")
            for i, cat in enumerate(spec["cats"]):
                vals = [cell(s[2][i]) for s in spec["series"]]
                out.append("| " + " | ".join([str(cat)] + vals) + " |")
            out.append("")

    # differences by section
    out.append("## Parameter differences by section")
    out.append("")
    if not diffs:
        out.append("_No differing shared parameters._")
        out.append("")
    for section, items in diffs.items():
        out.append(f"### {section} ({len(items)} differ)")
        out.append("")
        out.append(f"| Parameter | ID | {label_a} | {label_b} |")
        out.append("| --- | ---: | ---: | ---: |")
        for ident, name, va, vb in items:
            out.append(f"| {name} | {ident} | {cell(va)} | {cell(vb)} |")
        out.append("")

    # table-layout differences
    if only_a or only_b:
        out.append("## Table-layout differences")
        out.append("")
        out.append("Parameters that exist on only one bike's parameter table — "
                   "not comparable as values.")
        out.append("")
        for lbl, names in ((label_a, only_a), (label_b, only_b)):
            out.append(f"### Only in {lbl} ({len(names)})")
            out.append("")
            for nm in names:
                out.append(f"- {nm}")
            out.append("")

    return "\n".join(out).rstrip() + "\n"


def main():
    ap = argparse.ArgumentParser(description="Compare two Energica vcu.json dumps.")
    ap.add_argument("file_a")
    ap.add_argument("file_b")
    ap.add_argument("-o", "--out", default="vcu_comparison.html")
    ap.add_argument("--csv", help="also write the differences to this CSV "
                                   "(default: alongside --out)")
    ap.add_argument("--md", help="also write a GitHub-viewable Markdown report "
                                 "(default: alongside --out)")
    ap.add_argument("--label-a")
    ap.add_argument("--label-b")
    args = ap.parse_args()

    def default_label(path):
        # e.g. ./2021-eva-corsa-clienti/stock/vcu.json -> 2021-eva-corsa-clienti
        parts = os.path.normpath(path).split(os.sep)
        return parts[-3] if len(parts) >= 3 else parts[0]

    label_a = args.label_a or default_label(args.file_a)
    label_b = args.label_b or default_label(args.file_b)

    report, md_report, diffs, only_a, only_b = build_report(
        args.file_a, args.file_b, label_a, label_b)
    with open(args.out, "w") as fh:
        fh.write(report)
    print(f"Wrote {args.out}")

    md_path = args.md or (os.path.splitext(args.out)[0] + ".md")
    with open(md_path, "w") as fh:
        fh.write(md_report)
    print(f"Wrote {md_path}")

    csv_path = args.csv or (os.path.splitext(args.out)[0] + ".csv")
    write_csv(csv_path, label_a, label_b, diffs, only_a, only_b)
    print(f"Wrote {csv_path}")


def write_csv(path, label_a, label_b, diffs, only_a, only_b):
    """One tidy row per parameter of interest, machine-readable."""
    import csv
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["kind", "section", "identifier", "parameter", label_a, label_b])
        for section, items in diffs.items():
            for ident, name, va, vb in items:
                w.writerow(["diff", section, ident, name, va, vb])
        for name in only_a:
            w.writerow(["only_a", "", "", name, "present", ""])
        for name in only_b:
            w.writerow(["only_b", "", "", name, "", "present"])


if __name__ == "__main__":
    main()
