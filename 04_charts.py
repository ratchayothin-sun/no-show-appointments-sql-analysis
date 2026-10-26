"""
04_charts.py
Build the README charts from results/*.csv (run run_analysis.py and 03_model.py first).

Chart rules followed (see the dataviz skill): one series = one colour, two series =
palette slots 1-2 with a legend, thin bars (<= 24 px) with rounded data-ends, hairline
solid grid, value labels only on the points the story is about, text in ink colours
(never the series colour).
Sizes are in logical px (100 dpi) and saved at 2x for sharp README images.
"""
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon

ROOT = Path(__file__).resolve().parent
RES, OUT = ROOT / "results", ROOT / "charts"
OUT.mkdir(exist_ok=True)

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"
BLUE, ORANGE = "#2a78d6", "#eb6834"  # categorical slots 1 and 2

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Helvetica", "Arial", "DejaVu Sans"]
DPI = 100
PX = 0.72  # 1 logical px in points (1 px = 0.72 pt at 100 dpi)
LH = 18.8  # px per subtitle line (9.2 pt text at 1.45 line spacing)
SOURCE = (
    "Source: Kaggle 'Medical Appointment No Shows' (Brazil, appointments 29 Apr - 8 Jun 2016), "
    "110,521 appointments after cleaning. no-show = patient did not attend."
)


def strip_num(s: str) -> str:
    return s.split(". ", 1)[1] if s[:1].isdigit() and ". " in s else s


def header(fig, w, h, title, subtitle, sub_lines):
    fig.text(24 / w, 1 - 26 / h, title, fontsize=13.5, fontweight="bold", color=INK, va="top")
    fig.text(24 / w, 1 - 52 / h, subtitle, fontsize=9.2, color=INK2, va="top", linespacing=1.45)
    foot = textwrap.fill(SOURCE, 118)
    fig.text(24 / w, 12 / h, foot, fontsize=7.2, color=MUTED, va="bottom", linespacing=1.4)


def rbar(ax, x_end, y_top, t, color, dpx, r=4):
    """Horizontal bar: square at the baseline (x=0), 4 px rounded at the data end."""
    if not x_end or x_end <= 0:
        return
    rx = min(r * dpx, x_end)
    th_a, th_b = np.linspace(-np.pi / 2, 0, 8), np.linspace(0, np.pi / 2, 8)
    cx, cy_top, cy_bot = x_end - rx, y_top + r, y_top + t - r
    pts = [(0, y_top)]
    pts += [(cx + rx * np.cos(a), cy_top + r * np.sin(a)) for a in th_a]
    pts += [(cx + rx * np.cos(a), cy_bot + r * np.sin(a)) for a in th_b]
    pts += [(0, y_top + t)]
    ax.add_patch(Polygon(pts, closed=True, facecolor=color, edgecolor="none", zorder=3))


def hbar_chart(fname, title, subtitle, cats, series, xmax, xticks, ref=None, counts=None,
               label_cats=None, w=720, bar_t=20, left_px=178):
    """series = [(name, values, colour), ...]; one series -> no legend box."""
    k, n = len(series), len(cats)
    gap = 2
    group_h = k * bar_t + (k - 1) * gap
    pitch = group_h + 20
    sub = textwrap.fill(subtitle, 92)
    sub_lines = sub.count("\n") + 1
    left, right = left_px, 64
    plot_top = 52 + sub_lines * LH + 12 + (24 if k > 1 else 0) + (18 if ref else 6)
    plot_h = n * pitch
    h = int(plot_top + plot_h + 26 + 52)

    fig = plt.figure(figsize=(w / DPI, h / DPI), dpi=DPI, facecolor=SURFACE)
    header(fig, w, h, title, sub, sub_lines)
    ax = fig.add_axes([left / w, 1 - (plot_top + plot_h) / h, (w - left - right) / w, plot_h / h],
                      facecolor=SURFACE)
    ax.set_xlim(0, xmax)
    ax.set_ylim(plot_h, 0)  # y in px, top-down
    dpx = xmax / (w - left - right)  # data units per px
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_yticks([])
    ax.set_xticks(xticks)
    ax.set_xticklabels([f"{t:g}%" for t in xticks], fontsize=8.3, color=MUTED)
    ax.tick_params(axis="x", length=0, pad=8)
    for t in xticks:
        if ref is not None and abs(t - ref) < 1:  # the reference line replaces this gridline
            continue
        ax.axvline(t, color=GRID, lw=PX, zorder=0)
    ax.axvline(0, color=AXIS, lw=PX, zorder=1)
    if ref is not None:
        ax.axvline(ref, color=INK2, lw=PX, zorder=1)
        ax.text(ref, -7, f"Overall {ref:.1f}%", ha="center", va="bottom", fontsize=8, color=INK2,
                clip_on=False)

    for i, cat in enumerate(cats):
        y0 = i * pitch + (pitch - group_h) / 2
        yc = y0 + group_h / 2
        if counts is not None:
            ax.text(-12 * dpx, yc - 6, cat, ha="right", va="center", fontsize=9.4, color=INK2,
                    clip_on=False)
            ax.text(-12 * dpx, yc + 8, f"n = {counts[i]:,}", ha="right", va="center", fontsize=7.6,
                    color=MUTED, clip_on=False)
        else:
            ax.text(-12 * dpx, yc, cat, ha="right", va="center", fontsize=9.4, color=INK2,
                    clip_on=False)
        for j, (_, vals, color) in enumerate(series):
            v = vals[i]
            if pd.isna(v):
                continue
            yj = y0 + j * (bar_t + gap)
            rbar(ax, v, yj, bar_t, color, dpx)
            if label_cats is None or i in label_cats:
                ax.text(v + 7 * dpx, yj + bar_t / 2, f"{v:.1f}%", ha="left", va="center",
                        fontsize=8.8, color=INK, clip_on=False, zorder=5,
                        bbox=dict(facecolor=SURFACE, edgecolor="none", pad=1.5))

    if k > 1:  # legend row (always present for >= 2 series)
        x = 24
        y = 1 - (52 + sub_lines * LH + 14) / h
        for name, _, color in series:
            fig.add_artist(Line2D([(x + 4) / w], [y], marker="o", markersize=8 * PX, mfc=color,
                                  mec=color, ls="none", transform=fig.transFigure))
            t = fig.text((x + 14) / w, y, name, fontsize=8.8, color=INK2, va="center")
            x += 14 + 7.0 * len(name) + 22
    fig.savefig(OUT / fname, dpi=DPI * 2, facecolor=SURFACE)
    plt.close(fig)


def short_label(f: str) -> str:
    if f.startswith("Lead time: "):
        return "Booked " + f.split(": ")[1].split(" (vs")[0] + " ahead"
    if f.startswith("Age: "):
        return "Age " + f.split(": ")[1].split(" (vs")[0]
    if f.startswith("History: "):
        return f.split(": ")[1].split(" (vs")[0].replace("Two+", "Two or more")
    return f


def forest(fname):
    t = pd.read_csv(RES / "model_odds_ratios.csv")
    metrics = pd.read_csv(RES / "model_metrics.csv").set_index("model")["test_auc"]
    t["label"] = t.factor.map(short_label)
    t["group"] = t.factor.str.extract(r"^(Lead time|Age|History)")[0].fillna("Other")
    story = {"Booked 31+ days ahead", "Age 13-17", "Two or more earlier no-shows",
             "SMS reminder received", "Hypertension", "Alcoholism"}

    w, pitch, group_gap = 760, 24, 12
    left, right = 232, 70
    sub = textwrap.fill(
        "Odds ratio of missing the appointment, from one logistic regression with every factor "
        "included (95% CI). Blue = clearly different from 1; gray = not distinguishable from "
        "no effect. Reference groups: same-day booking, age 45-59, no earlier visit.", 98)
    sub_lines = sub.count("\n") + 1
    plot_top = 52 + sub_lines * LH + 30
    ys, y, prev = [], 0.0, None
    for g in t.group:
        if prev is not None and g != prev:
            y += group_gap
        ys.append(y + pitch / 2)
        y += pitch
        prev = g
    plot_h = y
    h = int(plot_top + plot_h + 128)

    fig = plt.figure(figsize=(w / DPI, h / DPI), dpi=DPI, facecolor=SURFACE)
    header(fig, w, h, "What predicts a no-show once everything else is held equal", sub, sub_lines)
    ax = fig.add_axes([left / w, 1 - (plot_top + plot_h) / h, (w - left - right) / w, plot_h / h],
                      facecolor=SURFACE)
    ax.set_xscale("log")
    ax.set_xlim(0.6, 18)
    ax.set_ylim(plot_h, 0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_yticks([])
    ticks = [0.75, 1, 1.5, 2, 4, 8, 16]
    ax.set_xticks(ticks)
    ax.set_xticklabels([f"{x:g}" for x in ticks], fontsize=8.3, color=MUTED)
    ax.minorticks_off()
    ax.tick_params(axis="x", length=0, pad=8)
    for x in ticks:
        ax.axvline(x, color=GRID, lw=PX, zorder=0)
    ax.axvline(1, color=INK2, lw=PX, zorder=1)
    ax.text(1, -7, "1 = no effect", ha="center", va="bottom", fontsize=8, color=INK2, clip_on=False)

    for (_, r), yy in zip(t.iterrows(), ys):
        sig = not (r.ci_low <= 1 <= r.ci_high)
        c = BLUE if sig else MUTED
        ax.plot([r.ci_low, r.ci_high], [yy, yy], color=c, lw=2 * PX, solid_capstyle="round", zorder=3)
        # same colour as its CI line, so no surface ring (the ring would hide narrow CIs)
        ax.plot([r.odds_ratio], [yy], marker="o", ms=9 * PX, mfc=c, mec=c, mew=0,
                ls="none", zorder=4, clip_on=False)
        ax.text(-0.02, yy, r.label, transform=ax.get_yaxis_transform(), ha="right", va="center",
                fontsize=9.2, color=INK2)
        if r.label in story:
            ax.text(r.ci_high * 1.08, yy, f"{r.odds_ratio:.2f}", ha="left", va="center",
                    fontsize=8.8, color=INK)

    y_note = 1 - (plot_top + plot_h + 38) / h
    fig.text((left + 4) / w, y_note, "< fewer no-shows", fontsize=8.2, color=MUTED, va="center")
    fig.text((w - right) / w, y_note, "more no-shows >", fontsize=8.2, color=MUTED, va="center",
             ha="right")
    fig.text(24 / w, 50 / h,
             f"Check on later appointments: AUC {metrics['Lead time only']:.2f} with lead time "
             f"alone, {metrics['All factors']:.2f} with all factors (0.50 = coin flip).",
             fontsize=8.2, color=INK2, va="bottom")
    fig.savefig(OUT / fname, dpi=DPI * 2, facecolor=SURFACE)
    plt.close(fig)


# ---------------------------------------------------------------- build charts
base = pd.read_csv(RES / "q01_baseline.csv").no_show_pct[0]

lead = pd.read_csv(RES / "q02_by_lead_bucket.csv")
hbar_chart(
    "01_lead_time.png",
    "No-show rate climbs with booking lead time",
    f"Share of appointments missed, by days between booking and appointment. Same-day bookings "
    f"are missed {lead.no_show_pct.iloc[0]:.1f}% of the time; booked 15+ days ahead, about one in three.",
    [strip_num(c) for c in lead.lead_bucket],
    [("No-show rate", lead.no_show_pct.tolist(), BLUE)],
    xmax=40, xticks=[0, 10, 20, 30, 40], ref=base, counts=lead.appointments.tolist(),
)

age = pd.read_csv(RES / "q03_by_age_group.csv")
hbar_chart(
    "02_age.png",
    "Teens and young adults miss the most; 60+ the least",
    "Share of appointments missed, by patient age. Rates alone, before controlling for lead time "
    "or other factors.",
    [strip_num(c) for c in age.age_group],
    [("No-show rate", age.no_show_pct.tolist(), BLUE)],
    xmax=30, xticks=[0, 10, 20, 30], ref=base, counts=age.appointments.tolist(),
)

sms = pd.read_csv(RES / "q05_sms_by_lead_bucket.csv")
sms = sms[sms.n_sms > 0].reset_index(drop=True)  # same-day bookings never got an SMS
naive = pd.read_csv(RES / "q04_sms_naive.csv").set_index("sms_received").no_show_pct
hbar_chart(
    "03_sms_by_lead_time.png",
    "At the same lead time, SMS goes with fewer no-shows",
    f"Naively SMS looks harmful ({naive[1]:.1f}% missed with SMS vs {naive[0]:.1f}% without) only "
    f"because reminders mostly go to appointments booked far ahead. Compared within each lead-time "
    f"group the gap reverses. Same-day bookings had no SMS and are left out.",
    [strip_num(c) for c in sms.lead_bucket],
    [("No SMS reminder", sms.no_show_pct_no_sms.tolist(), ORANGE),
     ("SMS reminder", sms.no_show_pct_sms.tolist(), BLUE)],
    xmax=50, xticks=[0, 10, 20, 30, 40, 50], ref=None, label_cats={len(sms) - 1},
)

hist = pd.read_csv(RES / "q09_patient_history.csv")
hbar_chart(
    "04_patient_history.png",
    "Patients who missed before are more likely to miss again",
    "Share of appointments missed, by how many earlier no-shows the patient had. Counts only "
    "earlier days inside this 6-week window, so real history is longer than what is visible.",
    [strip_num(c) for c in hist.history],
    [("No-show rate", hist.no_show_pct.tolist(), BLUE)],
    xmax=40, xticks=[0, 10, 20, 30, 40], ref=base, counts=hist.appointments.tolist(),
    left_px=240,
)

forest("05_adjusted_odds_ratios.png")
print("charts written:", sorted(p.name for p in OUT.glob("*.png")))
