import os
import sys
import csv
from datetime import datetime

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# (type, reason_prefix_or_None, legend_label, color, marker, scatter_size)
_MARKER_DEFS = [
    ('RESET', 'POWER ON',  'Reset – Power On',  '#2ca02c', '*', 140),
    ('RESET', 'BROWN OUT', 'Reset – Brown Out', '#d62728', 'D',  60),
    ('RESET',  None,       'Reset – Other',     '#7f7f7f', 's',  60),
    ('PUMP',  'AUTO',      'Pump – Auto',       '#ff7f0e', 'v',  60),
    ('PUMP',  'MANUAL',    'Pump – Manual',     '#111111', 'o',  45),
]


def _match_marker(row_type, row_reason):
    rt = row_type.strip().upper()
    rr = row_reason.strip().upper()
    for t, r_prefix, label, color, marker, size in _MARKER_DEFS:
        if rt != t:
            continue
        if r_prefix is None or rr.startswith(r_prefix):
            return label, color, marker, size
    return None


def plot_log(csv_path, save_path=None):
    """Read a log CSV and save a dual-axis Volts / PCB-Temp figure.

    Returns the path of the saved PNG.
    """
    if save_path is None:
        save_path = os.path.splitext(csv_path)[0] + '.png'

    device_id = os.path.splitext(os.path.basename(csv_path))[0]

    times, volts, temps, events = [], [], [], []

    with open(csv_path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            try:
                dt = datetime.strptime(
                    f"{row['DATE']} {row['TIME']}", '%y-%m-%d %H:%M')
                v  = float(row['VOLTS'])
                tc = float(row['PCB TEMP C'])
            except (ValueError, KeyError):
                continue
            times.append(dt)
            volts.append(v)
            temps.append(tc)

            m = _match_marker(row.get('TYPE', ''), row.get('REASON', ''))
            if m:
                events.append((dt, v, *m))

    if not times:
        raise ValueError(f"No valid data rows found in {csv_path}")

    fig, ax1 = plt.subplots(figsize=(14, 5.5))
    fig.suptitle(device_id, fontsize=13, fontweight='bold', y=0.99)

    # ── Left axis: Volts ────────────────────────────────────────────────────
    ax1.plot(times, volts, color='steelblue', linewidth=1.4, label='Volts')
    ax1.set_xlabel('Date / Time', fontsize=10)
    ax1.set_ylabel('Volts', color='steelblue', fontsize=10)
    ax1.tick_params(axis='y', labelcolor='steelblue')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %d\n%H:%M'))
    fig.autofmt_xdate(rotation=30, ha='right')

    # ── Right axis: PCB Temp ────────────────────────────────────────────────
    ax2 = ax1.twinx()
    ax2.plot(times, temps, color='salmon', linewidth=1.4,
             linestyle='--', label='PCB Temp (°C)')
    ax2.set_ylabel('PCB Temp (°C)', color='salmon', fontsize=10)
    ax2.tick_params(axis='y', labelcolor='salmon')

    # ── Event markers (on ax1 so they use the Volts Y scale) ───────────────
    seen_labels = set()
    legend_handles = []
    for dt, v, label, color, marker, size in events:
        kw = dict(color=color, marker=marker, s=size, zorder=5,
                  linewidths=0.6, edgecolors='white')
        if label not in seen_labels:
            kw['label'] = label
            seen_labels.add(label)
        sc = ax1.scatter([dt], [v], **kw)
        if 'label' in kw:
            legend_handles.append(sc)

    # ── Combined legend ─────────────────────────────────────────────────────
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2,
               loc='lower left', ncol=4, fontsize=8, framealpha=0.88)

    plt.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return save_path


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python visualize_log.py <log.csv>")
        sys.exit(1)
    out = plot_log(sys.argv[1])
    print(f"Saved: {out}")
