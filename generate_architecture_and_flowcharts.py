"""
generate_architecture_and_flowcharts.py
Generates publication-grade 300-DPI system architecture diagrams and procedural flowcharts
for the Conformal-Controlled Adaptive Filter with Dead-Band Control (CCAF-DB).
Generates:
1. fig_ccaf_architecture.png / .pdf (Standalone System Architecture)
2. fig_ccaf_flowchart.png / .pdf (Standalone Algorithmic Flowchart)
3. fig_ccaf_architecture_and_flowchart.png / .pdf (High-Res Combined 2-Panel Figure)
4. fig_ccaf_multidomain_pipeline.png / .pdf (3-Domain Application Pipeline)
Zero text overflow, generous internal box margins, clean typography, publication grade.
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch

# Publication typography & style
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['mathtext.fontset'] = 'cm'
plt.rcParams['axes.edgecolor'] = '#1E293B'
plt.rcParams['axes.linewidth'] = 1.0

os.makedirs("results", exist_ok=True)
os.makedirs("paper_latex/figures", exist_ok=True)

# Helper function for process blocks with generous margins
def draw_block(ax, x, y, w, h, text, subtext="", ec='#1E293B', fc='#FFFFFF', lw=1.5, text_color='#0F172A', title_size=10.0, sub_size=8.5, radius=0.10):
    box = FancyBboxPatch((x - w/2, y - h/2), w, h, boxstyle=f"round,pad={radius}",
                         ec=ec, fc=fc, lw=lw, zorder=3)
    ax.add_patch(box)
    if subtext:
        ax.text(x, y + 0.17*h, text, ha='center', va='center', fontsize=title_size, fontweight='bold', color=text_color, zorder=4)
        ax.text(x, y - 0.19*h, subtext, ha='center', va='center', fontsize=sub_size, color='#475569', zorder=4)
    else:
        ax.text(x, y, text, ha='center', va='center', fontsize=title_size, fontweight='bold', color=text_color, zorder=4)
    return box

# Helper function for summation circles
def draw_sum(ax, x, y, radius=0.28, text="+", ec='#1E293B', fc='#FFFFFF'):
    circle = Circle((x, y), radius, ec=ec, fc=fc, lw=1.6, zorder=3)
    ax.add_patch(circle)
    ax.text(x, y, text, ha='center', va='center', fontsize=13, fontweight='bold', color='#0F172A', zorder=4)
    return circle

# Helper function for directional arrows
def draw_arrow(ax, p1, p2, label="", label_pos=(0.5, 0.5), label_offset=(0, 0.22), color='#334155', lw=1.5, ls='-', font_size=8.5):
    arrow = FancyArrowPatch(p1, p2, arrowstyle='-|>', mutation_scale=14, color=color, lw=lw, ls=ls, zorder=2)
    ax.add_patch(arrow)
    if label:
        lx = p1[0] + (p2[0] - p1[0]) * label_pos[0] + label_offset[0]
        ly = p1[1] + (p2[1] - p1[1]) * label_pos[1] + label_offset[1]
        ax.text(lx, ly, label, ha='center', va='center', fontsize=font_size, fontweight='bold', color=color, zorder=5,
                bbox=dict(boxstyle='round,pad=0.14', fc='#FFFFFF', ec='#CBD5E1', lw=0.7, alpha=0.96))

# Helper function for decision diamonds
def draw_diamond(ax, x, y, w, h, text, subtext="", ec='#D97706', fc='#FFFBEB', lw=1.8, title_size=10.0, sub_size=8.5):
    diamond = patches.Polygon([
        (x, y + h/2),
        (x + w/2, y),
        (x, y - h/2),
        (x - w/2, y)
    ], closed=True, ec=ec, fc=fc, lw=lw, zorder=3)
    ax.add_patch(diamond)
    if subtext:
        ax.text(x, y + 0.15*h, text, ha='center', va='center', fontsize=title_size, fontweight='bold', color='#B45309', zorder=4)
        ax.text(x, y - 0.16*h, subtext, ha='center', va='center', fontsize=sub_size, color='#78350F', zorder=4)
    else:
        ax.text(x, y, text, ha='center', va='center', fontsize=title_size, fontweight='bold', color='#B45309', zorder=4)
    return diamond


# ==============================================================================
# 1. STANDALONE SYSTEM ARCHITECTURE FIGURE
# ==============================================================================
def render_standalone_architecture():
    print("[1/4] Rendering Standalone System Architecture (fig_ccaf_architecture.png / .pdf)...")
    fig, ax = plt.subplots(figsize=(15.5, 8.5), dpi=300)
    ax.set_xlim(-0.5, 15.5)
    ax.set_ylim(0, 10.0)
    ax.axis('off')

    c_main = '#0284C7'       # Ocean Blue
    c_conformal = '#0D9488'  # Deep Teal
    c_deadband = '#D97706'   # Amber / Gold
    c_signal = '#475569'     # Slate Gray

    # Title
    ax.text(7.5, 9.60, "Closed-Loop System Architecture of CCAF-DB", 
            ha='center', va='center', fontsize=14.5, fontweight='bold', color='#0F172A')

    # Subsystem Background Cards
    # 1. Conformal Uncertainty Core Card
    card_uq = FancyBboxPatch((5.8, 4.3), 9.2, 4.8, boxstyle="round,pad=0.25",
                             ec='#0D9488', fc='#F0FDFA', lw=1.6, ls='--', zorder=1)
    ax.add_patch(card_uq)
    ax.text(10.4, 8.75, "CONFORMAL UNCERTAINTY CORE (Online ACI)", 
            ha='center', va='center', fontsize=11, fontweight='bold', color='#0F766E', zorder=2)

    # 2. Dead-Band Step-Size Governor Card
    card_db = FancyBboxPatch((5.8, 0.6), 9.2, 3.2, boxstyle="round,pad=0.25",
                             ec='#D97706', fc='#FFFBEB', lw=1.6, ls='--', zorder=1)
    ax.add_patch(card_db)
    ax.text(10.4, 3.45, "DEAD-BAND STEP-SIZE GOVERNOR", 
            ha='center', va='center', fontsize=11, fontweight='bold', color='#B45309', zorder=2)

    # Primary Filter Loop Elements
    # Input signal
    ax.text(0.5, 7.3, "Input Signal\n" + r"$\mathbf{u}(n)$", ha='center', va='center', fontsize=10, fontweight='bold', color='#0284C7')
    # Target signal
    ax.text(4.9, 9.2, "Desired Target\n" + r"$d(n)$", ha='center', va='center', fontsize=10, fontweight='bold', color='#0F172A')

    # Adaptive Filter Block
    draw_block(ax, 2.6, 7.3, 2.3, 1.15, "Adaptive Filter", r"Linear Combiner $\hat{y}(n)$", ec=c_main, fc='#F0F9FF', lw=1.8, text_color='#0369A1', title_size=10.5, sub_size=9.0)

    # Summation Node
    draw_sum(ax, 4.9, 7.3, radius=0.28, text=r"$\Sigma$", ec='#0F172A', fc='#FFFFFF')
    ax.text(4.9, 7.80, "+", ha='center', va='center', fontsize=11, fontweight='bold', color='#0F172A')
    ax.text(4.55, 7.3, "-", ha='right', va='center', fontsize=12, fontweight='bold', color='#DC2626')

    # Conformal Uncertainty Engine Blocks
    # Scale Estimator
    draw_block(ax, 7.4, 7.3, 2.2, 1.15, "Scale Estimator", "Causal RMS $s(n-1)$", ec=c_conformal, fc='#FFFFFF', title_size=10.0, sub_size=8.5)
    # Score Evaluator
    draw_block(ax, 10.4, 7.3, 2.2, 1.15, "Score Evaluator", r"Relative Error $|e|/s$", ec=c_conformal, fc='#FFFFFF', title_size=10.0, sub_size=8.5)
    # Miss Detector
    draw_block(ax, 13.4, 7.3, 2.2, 1.15, "Miss Detector", r"Test $r > q_{\mathrm{norm}}$", ec=c_conformal, fc='#FFFFFF', title_size=10.0, sub_size=8.5)

    # Quantile Tracker
    draw_block(ax, 13.4, 5.2, 2.2, 1.05, "Quantile Tracker", r"Adapt Error Level $a_n$", ec=c_conformal, fc='#FFFFFF', title_size=10.0, sub_size=8.5)

    # Conformal Prediction Ribbon
    draw_block(ax, 9.2, 5.2, 4.2, 1.05, "Conformal Prediction Ribbon", r"Guaranteed Band $[\hat{y}(n) \pm q \cdot s]$", ec=c_conformal, fc='#E6FFFA', text_color='#0F766E', title_size=10.0, sub_size=8.5)

    # Dead-Band Step-Size Governor Blocks
    # Deficit Monitor
    draw_block(ax, 13.4, 1.9, 2.2, 1.05, "Deficit Monitor", r"$\Delta_n = \alpha - a_{n+1}$", ec=c_deadband, fc='#FFFFFF', title_size=10.0, sub_size=8.5)
    # Dead-Band Gate
    draw_block(ax, 10.4, 1.9, 2.2, 1.05, "Dead-Band Gate", r"Threshold with $\tau$", ec=c_deadband, fc='#FEF3C7', title_size=10.0, sub_size=8.5)
    # Step Controller
    draw_block(ax, 7.4, 1.9, 2.2, 1.05, "Step Controller", r"Compute Step $\mu(n)$", ec=c_deadband, fc='#FFFFFF', title_size=10.0, sub_size=8.5)

    # Weight Update Block
    draw_block(ax, 2.6, 3.8, 2.5, 1.30, "Weight Update", "Normalized LMS\n" + r"$\mathbf{w}(n+1) \leftarrow \mathbf{w}(n)$", ec=c_main, fc='#E0F2FE', lw=1.8, text_color='#0369A1', title_size=10.5, sub_size=8.8)

    # Connecting Arrows
    # Input u(n) -> Filter
    draw_arrow(ax, (1.1, 7.3), (1.45, 7.3))
    # Input u(n) down to Weight Update
    draw_arrow(ax, (0.5, 6.7), (0.5, 3.8), color=c_main)
    draw_arrow(ax, (0.5, 3.8), (1.35, 3.8), label=r"$\mathbf{u}(n)$", label_pos=(0.5, 0.5), label_offset=(0, 0.24), color=c_main)

    # Filter -> Sum (y_hat)
    draw_arrow(ax, (3.75, 7.3), (4.62, 7.3), label=r"$\hat{y}$", label_pos=(0.5, 0.5), label_offset=(0, 0.24), color=c_main)
    # d(n) -> Sum
    draw_arrow(ax, (4.9, 8.7), (4.9, 7.58))

    # Sum -> Scale Estimator (e(n))
    draw_arrow(ax, (5.18, 7.3), (6.30, 7.3), label=r"$e(n)$", label_pos=(0.5, 0.5), label_offset=(0, 0.24))

    # Scale Estimator -> Score Evaluator
    draw_arrow(ax, (8.50, 7.3), (9.30, 7.3), label=r"$s$", label_pos=(0.5, 0.5), label_offset=(0, 0.24))
    # Score Evaluator -> Miss Detector
    draw_arrow(ax, (11.50, 7.3), (12.30, 7.3), label=r"$r$", label_pos=(0.5, 0.5), label_offset=(0, 0.24))

    # Miss Detector -> Quantile Tracker
    draw_arrow(ax, (13.4, 6.72), (13.4, 5.73), label=r"$m(n)$", label_offset=(0.48, 0))

    # Quantile Tracker -> Prediction Ribbon
    draw_arrow(ax, (12.30, 5.2), (11.30, 5.2), label=r"$q$", label_pos=(0.5, 0.5), label_offset=(0, 0.24))

    # Safe Prediction Interval Output
    draw_arrow(ax, (9.2, 4.67), (9.2, 3.75), label=r"Safe Interval $\mathcal{C}(n)$", label_offset=(1.4, 0), color=c_conformal)

    # Quantile Tracker -> Deficit Monitor
    draw_arrow(ax, (13.4, 4.67), (13.4, 2.43), label=r"$a_{n+1}$", label_offset=(0.50, 0))

    # Deficit Monitor -> Dead-Band Gate
    draw_arrow(ax, (12.30, 1.9), (11.50, 1.9), label=r"$\Delta_n$", label_pos=(0.5, 0.5), label_offset=(0, 0.28))
    # Dead-Band Gate -> Step Controller
    draw_arrow(ax, (9.30, 1.9), (8.50, 1.9), label=r"$c_{\mathrm{DB}}$", label_pos=(0.5, 0.5), label_offset=(0, 0.28))

    # Step Controller -> Weight Update
    draw_arrow(ax, (6.30, 1.9), (2.6, 1.9), label=r"Adaptive Step $\mu(n)$", label_pos=(0.45, 0.5), label_offset=(0, 0.28), color=c_deadband)
    draw_arrow(ax, (2.6, 1.9), (2.6, 3.15), color=c_deadband)

    # Error tap down to Weight Update
    draw_arrow(ax, (5.7, 7.3), (5.7, 4.1), ls='--', color=c_signal)
    draw_arrow(ax, (5.7, 4.1), (3.85, 4.1), label=r"$e(n)$", label_pos=(0.5, 0.5), label_offset=(0, 0.24), ls='--', color=c_signal)

    # Weight Update -> Filter feedback loop
    draw_arrow(ax, (2.6, 4.45), (2.6, 6.72), label=r"$\mathbf{w}(n+1)$", label_offset=(-0.65, 0), color=c_main)

    # Cleaned Signal Output (e(n))
    draw_arrow(ax, (4.9, 7.02), (4.9, 5.8), color='#DC2626', lw=1.8)
    ax.text(4.9, 5.45, "Cleaned Signal\n" + r"$e(n)$", ha='center', va='center', fontsize=9.2, fontweight='bold', color='#DC2626')

    plt.tight_layout()
    fig.savefig("results/fig_ccaf_architecture.png", dpi=300, bbox_inches='tight')
    fig.savefig("paper_latex/figures/fig_ccaf_architecture.png", dpi=300, bbox_inches='tight')
    fig.savefig("results/fig_ccaf_architecture.pdf", bbox_inches='tight')
    fig.savefig("paper_latex/figures/fig_ccaf_architecture.pdf", bbox_inches='tight')
    plt.close(fig)
    print("  [SAVED] Standalone Architecture (PNG & PDF)")


# ==============================================================================
# 2. STANDALONE PROCEDURAL FLOWCHART FIGURE
# ==============================================================================
def render_standalone_flowchart():
    print("[2/4] Rendering Standalone Procedural Flowchart (fig_ccaf_flowchart.png / .pdf)...")
    fig, ax = plt.subplots(figsize=(9.2, 12.0), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 12.2)
    ax.axis('off')

    # Title
    ax.text(5.0, 11.80, "Procedural Execution Flowchart of CCAF-DB", 
            ha='center', va='center', fontsize=14, fontweight='bold', color='#0F172A')

    # 1. Start Node
    pill_start = FancyBboxPatch((2.6, 10.90), 4.8, 0.52, boxstyle="round,pad=0.15",
                                ec='#0F172A', fc='#F1F5F9', lw=1.6, zorder=3)
    ax.add_patch(pill_start)
    ax.text(5.0, 10.90 + 0.26, "START: Initialize Filter & States", ha='center', va='center', fontsize=10.0, fontweight='bold', color='#0F172A', zorder=4)

    # 2. Ingest Sample Pair
    draw_block(ax, 5.0, 9.80, 6.6, 0.88, "1. Ingest Streaming Signal Pair", 
               "Receive regressor vector u(n) and desired target d(n)", 
               ec='#0284C7', fc='#F0F9FF', lw=1.6, title_size=10.5, sub_size=8.8)

    # 3. Filter Prediction & Safe Bounds
    draw_block(ax, 5.0, 8.60, 6.6, 0.88, "2. Point Estimation & Prediction Interval", 
               "Compute estimate y_hat(n) and safe conformal bounds", 
               ec='#0284C7', fc='#FFFFFF', lw=1.6, title_size=10.5, sub_size=8.8)

    # 4. Error Residual & Miss Evaluation
    draw_block(ax, 5.0, 7.40, 6.6, 0.88, "3. Error Residual & Miss Evaluation", 
               "Evaluate error e(n) and check conformal miss indicator", 
               ec='#0D9488', fc='#F0FDFA', lw=1.6, title_size=10.5, sub_size=8.8)

    # 5. ACI Quantile Update
    draw_block(ax, 5.0, 6.20, 6.6, 0.88, "4. Adaptive Conformal Quantile Update", 
               "Update empirical coverage tracking state a_{n+1}", 
               ec='#0D9488', fc='#FFFFFF', lw=1.6, title_size=10.5, sub_size=8.8)

    # 6. Dead-Band Condition Decision Diamond
    draw_diamond(ax, 5.0, 4.75, 5.8, 1.40, r"Dead-Band Criterion Test", 
                 r"Is Deficit $(\alpha - a_{n+1}) > \tau$ ?", 
                 ec='#D97706', fc='#FEF3C7', lw=1.8, title_size=10.5, sub_size=9.2)

    # 7. Dual Decision Branches
    # Left Branch (NO / Steady-State Mode)
    draw_block(ax, 2.3, 3.20, 3.7, 0.95, "Steady-State Mode (Safe)", 
               "Clamp mu(n) = mu_min\n(Zero Misadjustment Penalty)", 
               ec='#10B981', fc='#ECFDF5', lw=1.6, title_size=9.5, sub_size=8.2)

    # Right Branch (YES / Tracking Acceleration)
    draw_block(ax, 7.7, 3.20, 3.7, 0.95, "Tracking Burst (Agile)", 
               "Surge mu(n) -> mu_max\n(Rapid Weight Re-convergence)", 
               ec='#EF4444', fc='#FEF2F2', lw=1.6, title_size=9.5, sub_size=8.2)

    # 8. Weight Update & Scale Recursion (Merge)
    draw_block(ax, 5.0, 1.75, 6.8, 0.90, "5. Weight Recursion & Scale Update", 
               "Apply normalized LMS update and update causal scale s(n)", 
               ec='#0284C7', fc='#F8FAFC', lw=1.6, title_size=10.5, sub_size=8.8)

    # 9. Next Sample Pill
    pill_next = FancyBboxPatch((3.2, 0.50), 3.6, 0.48, boxstyle="round,pad=0.15",
                               ec='#475569', fc='#F1F5F9', lw=1.4, zorder=3)
    ax.add_patch(pill_next)
    ax.text(5.0, 0.50 + 0.24, "Next Sample: n <- n + 1", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#334155', zorder=4)

    # Vertical Flow Arrows
    draw_arrow(ax, (5.0, 10.90), (5.0, 10.24))
    draw_arrow(ax, (5.0, 9.36), (5.0, 9.04))
    draw_arrow(ax, (5.0, 8.16), (5.0, 7.84))
    draw_arrow(ax, (5.0, 6.96), (5.0, 6.64))
    draw_arrow(ax, (5.0, 5.76), (5.0, 5.45))

    # Decision Branches Arrows
    # NO Branch (Left)
    draw_arrow(ax, (2.1, 4.75), (2.3, 4.75), color='#10B981', lw=1.8)
    draw_arrow(ax, (2.3, 4.75), (2.3, 3.68), color='#10B981', lw=1.8)
    ax.text(2.3, 5.05, "NO (Calm)", ha='center', va='center', fontsize=8.8, fontweight='bold', color='#047857')

    # YES Branch (Right)
    draw_arrow(ax, (7.9, 4.75), (7.7, 4.75), color='#EF4444', lw=1.8)
    draw_arrow(ax, (7.7, 4.75), (7.7, 3.68), color='#EF4444', lw=1.8)
    ax.text(7.7, 5.05, "YES (Shift)", ha='center', va='center', fontsize=8.8, fontweight='bold', color='#B91C1C')

    # Merge branches into Step 5
    draw_arrow(ax, (2.3, 2.72), (2.3, 2.20), color='#10B981', lw=1.6)
    draw_arrow(ax, (2.3, 2.20), (3.6, 2.20), color='#10B981', lw=1.6)

    draw_arrow(ax, (7.7, 2.72), (7.7, 2.20), color='#EF4444', lw=1.6)
    draw_arrow(ax, (7.7, 2.20), (6.4, 2.20), color='#EF4444', lw=1.6)

    # Step 5 -> Next Sample Pill
    draw_arrow(ax, (5.0, 1.30), (5.0, 0.98))

    # Loopback arrow from Next Sample back to Ingest
    draw_arrow(ax, (6.8, 0.74), (9.0, 0.74), color='#94A3B8', ls='--', lw=1.4)
    draw_arrow(ax, (9.0, 0.74), (9.0, 9.80), color='#94A3B8', ls='--', lw=1.4)
    draw_arrow(ax, (9.0, 9.80), (8.3, 9.80), color='#94A3B8', ls='--', lw=1.4)
    ax.text(9.0, 5.5, "Streaming Loop", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#64748B',
            rotation=90, bbox=dict(boxstyle='round,pad=0.2', fc='#FFFFFF', ec='#CBD5E1', lw=0.6))

    plt.tight_layout()
    fig.savefig("results/fig_ccaf_flowchart.png", dpi=300, bbox_inches='tight')
    fig.savefig("paper_latex/figures/fig_ccaf_flowchart.png", dpi=300, bbox_inches='tight')
    fig.savefig("results/fig_ccaf_flowchart.pdf", bbox_inches='tight')
    fig.savefig("paper_latex/figures/fig_ccaf_flowchart.pdf", bbox_inches='tight')
    plt.close(fig)
    print("  [SAVED] Standalone Flowchart (PNG & PDF)")


# ==============================================================================
# 3. HIGH-RES COMBINED 2-PANEL FIGURE (SPACIOUS, ZERO OVERFLOW)
# ==============================================================================
def render_combined_architecture_and_flowchart():
    print("[3/4] Rendering Spacious Combined 2-Panel Figure (fig_ccaf_architecture_and_flowchart.png / .pdf)...")
    fig = plt.figure(figsize=(19.0, 10.5), dpi=300)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 0.85], wspace=0.15)

    c_main = '#0284C7'
    c_conformal = '#0D9488'
    c_deadband = '#D97706'
    c_signal = '#475569'

    # PANEL A
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_xlim(-0.6, 12.5)
    ax1.set_ylim(0, 10.0)
    ax1.axis('off')

    ax1.text(5.95, 9.75, "(a) Closed-Loop System Architecture of CCAF-DB", 
             ha='center', va='center', fontsize=13.5, fontweight='bold', color='#0F172A')

    # Cards
    card_uq = FancyBboxPatch((4.7, 4.2), 7.6, 4.8, boxstyle="round,pad=0.2",
                             ec='#0D9488', fc='#F0FDFA', lw=1.6, ls='--', zorder=1)
    ax1.add_patch(card_uq)
    ax1.text(8.5, 8.65, "CONFORMAL UNCERTAINTY CORE (Online ACI)", 
             ha='center', va='center', fontsize=10.5, fontweight='bold', color='#0F766E', zorder=2)

    card_db = FancyBboxPatch((4.7, 0.5), 7.6, 3.2, boxstyle="round,pad=0.2",
                             ec='#D97706', fc='#FFFBEB', lw=1.6, ls='--', zorder=1)
    ax1.add_patch(card_db)
    ax1.text(8.5, 3.35, "DEAD-BAND STEP-SIZE GOVERNOR", 
             ha='center', va='center', fontsize=10.5, fontweight='bold', color='#B45309', zorder=2)

    # Left Column
    ax1.text(0.0, 7.3, "Input Signal\n" + r"$\mathbf{u}(n)$", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#0284C7')
    ax1.text(3.8, 9.2, "Desired Target\n" + r"$d(n)$", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#0F172A')

    draw_block(ax1, 2.0, 7.3, 2.0, 1.05, "Adaptive Filter", r"Linear Combiner $\hat{y}$", ec=c_main, fc='#F0F9FF', lw=1.8, text_color='#0369A1', title_size=9.5, sub_size=8.2)

    draw_sum(ax1, 3.8, 7.3, radius=0.26, text=r"$\Sigma$", ec='#0F172A', fc='#FFFFFF')
    ax1.text(3.8, 7.75, "+", ha='center', va='center', fontsize=10, fontweight='bold', color='#0F172A')
    ax1.text(3.48, 7.3, "-", ha='right', va='center', fontsize=11, fontweight='bold', color='#DC2626')

    # Core Blocks
    draw_block(ax1, 6.0, 7.3, 1.9, 1.05, "Scale Estimator", "Causal RMS $s(n-1)$", ec=c_conformal, fc='#FFFFFF', title_size=9.2, sub_size=7.8)
    draw_block(ax1, 8.5, 7.3, 1.9, 1.05, "Score Evaluator", r"Relative Error $|e|/s$", ec=c_conformal, fc='#FFFFFF', title_size=9.2, sub_size=7.8)
    draw_block(ax1, 11.0, 7.3, 1.9, 1.05, "Miss Detector", r"Test $r > q_{\mathrm{norm}}$", ec=c_conformal, fc='#FFFFFF', title_size=9.2, sub_size=7.8)

    draw_block(ax1, 11.0, 5.2, 1.9, 0.95, "Quantile Tracker", r"Adapt Level $a_n$", ec=c_conformal, fc='#FFFFFF', title_size=9.2, sub_size=7.8)
    draw_block(ax1, 7.5, 5.2, 3.8, 0.95, "Conformal Prediction Ribbon", r"Guaranteed Band $[\hat{y} \pm q \cdot s]$", ec=c_conformal, fc='#E6FFFA', text_color='#0F766E', title_size=9.5, sub_size=8.0)

    # Dead-band Blocks
    draw_block(ax1, 11.0, 1.8, 1.9, 0.95, "Deficit Monitor", r"$\Delta_n = \alpha - a_{n+1}$", ec=c_deadband, fc='#FFFFFF', title_size=9.2, sub_size=7.8)
    draw_block(ax1, 8.5, 1.8, 1.9, 0.95, "Dead-Band Gate", r"Threshold with $\tau$", ec=c_deadband, fc='#FEF3C7', title_size=9.2, sub_size=7.8)
    draw_block(ax1, 6.0, 1.8, 1.9, 0.95, "Step Controller", r"Compute $\mu(n)$", ec=c_deadband, fc='#FFFFFF', title_size=9.2, sub_size=7.8)

    draw_block(ax1, 2.0, 3.8, 2.1, 1.20, "Weight Update", "Normalized LMS\n" + r"$\mathbf{w}(n+1) \leftarrow \mathbf{w}(n)$", ec=c_main, fc='#E0F2FE', lw=1.8, text_color='#0369A1', title_size=9.5, sub_size=8.0)

    # Arrows
    draw_arrow(ax1, (0.5, 7.3), (1.0, 7.3))
    draw_arrow(ax1, (0.0, 6.7), (0.0, 3.8), color=c_main)
    draw_arrow(ax1, (0.0, 3.8), (0.95, 3.8), label=r"$\mathbf{u}(n)$", label_pos=(0.5, 0.5), label_offset=(0, 0.22), color=c_main)

    draw_arrow(ax1, (3.0, 7.3), (3.54, 7.3), label=r"$\hat{y}$", label_pos=(0.5, 0.5), label_offset=(0, 0.22), color=c_main)
    draw_arrow(ax1, (3.8, 8.7), (3.8, 7.56))

    draw_arrow(ax1, (4.06, 7.3), (5.05, 7.3), label=r"$e(n)$", label_pos=(0.5, 0.5), label_offset=(0, 0.22))
    draw_arrow(ax1, (6.95, 7.3), (7.55, 7.3), label=r"$s$", label_pos=(0.5, 0.5), label_offset=(0, 0.22))
    draw_arrow(ax1, (9.45, 7.3), (10.05, 7.3), label=r"$r$", label_pos=(0.5, 0.5), label_offset=(0, 0.22))

    draw_arrow(ax1, (11.0, 6.775), (11.0, 5.675), label=r"$m(n)$", label_offset=(0.44, 0))
    draw_arrow(ax1, (10.05, 5.2), (9.4, 5.2), label=r"$q$", label_pos=(0.5, 0.5), label_offset=(0, 0.22))
    draw_arrow(ax1, (7.5, 4.725), (7.5, 3.9), label=r"Safe Interval $\mathcal{C}(n)$", label_offset=(1.25, 0), color=c_conformal)

    draw_arrow(ax1, (11.0, 4.725), (11.0, 2.275), label=r"$a_{n+1}$", label_offset=(0.45, 0))
    draw_arrow(ax1, (10.05, 1.8), (9.45, 1.8), label=r"$\Delta_n$", label_pos=(0.5, 0.5), label_offset=(0, 0.26))
    draw_arrow(ax1, (7.55, 1.8), (6.95, 1.8), label=r"$c_{\mathrm{DB}}$", label_pos=(0.5, 0.5), label_offset=(0, 0.26))

    draw_arrow(ax1, (5.05, 1.8), (2.0, 1.8), label=r"Step $\mu(n)$", label_pos=(0.5, 0.5), label_offset=(0, 0.26), color=c_deadband)
    draw_arrow(ax1, (2.0, 1.8), (2.0, 3.2), color=c_deadband)

    draw_arrow(ax1, (4.5, 7.3), (4.5, 4.1), ls='--', color=c_signal)
    draw_arrow(ax1, (4.5, 4.1), (3.05, 4.1), label=r"$e(n)$", label_pos=(0.5, 0.5), label_offset=(0, 0.22), ls='--', color=c_signal)

    draw_arrow(ax1, (2.0, 4.4), (2.0, 6.775), label=r"$\mathbf{w}(n+1)$", label_offset=(-0.58, 0), color=c_main)

    draw_arrow(ax1, (3.8, 7.04), (3.8, 5.8), color='#DC2626', lw=1.6)
    ax1.text(3.8, 5.5, "Cleaned Signal\n" + r"$e(n)$", ha='center', va='center', fontsize=8.2, fontweight='bold', color='#DC2626')

    # PANEL B
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 10)
    ax2.axis('off')

    ax2.text(5.0, 9.75, "(b) Procedural Execution Flowchart of CCAF-DB", 
             ha='center', va='center', fontsize=13.5, fontweight='bold', color='#0F172A')

    pill_start = FancyBboxPatch((2.6, 8.95), 4.8, 0.45, boxstyle="round,pad=0.12",
                                ec='#0F172A', fc='#F1F5F9', lw=1.5, zorder=3)
    ax2.add_patch(pill_start)
    ax2.text(5.0, 8.95 + 0.225, "START: Initialize Filter & States", ha='center', va='center', fontsize=9.0, fontweight='bold', color='#0F172A', zorder=4)

    draw_block(ax2, 5.0, 8.10, 6.2, 0.72, "1. Ingest Streaming Signal Pair", 
               "Receive regressor u(n) and target d(n)", 
               ec='#0284C7', fc='#F0F9FF', lw=1.5, title_size=9.5, sub_size=8.0)

    draw_block(ax2, 5.0, 7.05, 6.2, 0.72, "2. Point Estimation & Prediction Interval", 
               "Compute estimate y_hat(n) and safe conformal bounds", 
               ec='#0284C7', fc='#FFFFFF', lw=1.5, title_size=9.5, sub_size=8.0)

    draw_block(ax2, 5.0, 6.00, 6.2, 0.72, "3. Error Residual & Miss Evaluation", 
               "Evaluate error e(n) and check conformal miss indicator", 
               ec='#0D9488', fc='#F0FDFA', lw=1.5, title_size=9.5, sub_size=8.0)

    draw_block(ax2, 5.0, 4.95, 6.2, 0.72, "4. Adaptive Conformal Quantile Update", 
               "Update empirical coverage tracking state a_{n+1}", 
               ec='#0D9488', fc='#FFFFFF', lw=1.5, title_size=9.5, sub_size=8.0)

    draw_diamond(ax2, 5.0, 3.65, 5.4, 1.25, r"Dead-Band Deficit Test", 
                 r"Is Deficit $(\alpha - a_{n+1}) > \tau$ ?", 
                 ec='#D97706', fc='#FEF3C7', lw=1.6, title_size=9.5, sub_size=8.2)

    draw_block(ax2, 2.3, 2.25, 3.4, 0.85, "Steady-State Mode (Safe)", 
               "Clamp mu(n) = mu_min\n(Zero Misadjustment)", 
               ec='#10B981', fc='#ECFDF5', lw=1.5, title_size=8.8, sub_size=7.5)

    draw_block(ax2, 7.7, 2.25, 3.4, 0.85, "Tracking Burst (Agile)", 
               "Surge mu(n) -> mu_max\n(Fast Re-convergence)", 
               ec='#EF4444', fc='#FEF2F2', lw=1.5, title_size=8.8, sub_size=7.5)

    draw_block(ax2, 5.0, 1.05, 6.4, 0.75, "5. Weight Recursion & Scale Update", 
               "Apply normalized LMS update and update causal scale s(n)", 
               ec='#0284C7', fc='#F8FAFC', lw=1.6, title_size=9.5, sub_size=8.0)

    pill_next = FancyBboxPatch((3.4, 0.12), 3.2, 0.40, boxstyle="round,pad=0.12",
                               ec='#475569', fc='#F1F5F9', lw=1.3, zorder=3)
    ax2.add_patch(pill_next)
    ax2.text(5.0, 0.12 + 0.20, "Next Sample: n <- n + 1", ha='center', va='center', fontsize=8.8, fontweight='bold', color='#334155', zorder=4)

    draw_arrow(ax2, (5.0, 8.95), (5.0, 8.46))
    draw_arrow(ax2, (5.0, 7.74), (5.0, 7.41))
    draw_arrow(ax2, (5.0, 6.69), (5.0, 6.36))
    draw_arrow(ax2, (5.0, 5.64), (5.0, 5.31))
    draw_arrow(ax2, (5.0, 4.59), (5.0, 4.28))

    draw_arrow(ax2, (2.3, 3.65), (2.3, 2.68), color='#10B981', lw=1.6)
    draw_arrow(ax2, (2.7, 3.65), (2.3, 3.65), color='#10B981', lw=1.6)
    ax2.text(2.3, 3.90, "NO (Calm)", ha='center', va='center', fontsize=8.0, fontweight='bold', color='#047857')

    draw_arrow(ax2, (7.7, 3.65), (7.7, 2.68), color='#EF4444', lw=1.6)
    draw_arrow(ax2, (7.3, 3.65), (7.7, 3.65), color='#EF4444', lw=1.6)
    ax2.text(7.7, 3.90, "YES (Shift)", ha='center', va='center', fontsize=8.0, fontweight='bold', color='#B91C1C')

    draw_arrow(ax2, (2.3, 1.82), (2.3, 1.42), color='#10B981', lw=1.5)
    draw_arrow(ax2, (2.3, 1.42), (3.6, 1.42), color='#10B981', lw=1.5)

    draw_arrow(ax2, (7.7, 1.82), (7.7, 1.42), color='#EF4444', lw=1.5)
    draw_arrow(ax2, (7.7, 1.42), (6.4, 1.42), color='#EF4444', lw=1.5)

    draw_arrow(ax2, (5.0, 0.67), (5.0, 0.52))

    draw_arrow(ax2, (6.6, 0.32), (9.1, 0.32), color='#94A3B8', ls='--', lw=1.3)
    draw_arrow(ax2, (9.1, 0.32), (9.1, 8.10), color='#94A3B8', ls='--', lw=1.3)
    draw_arrow(ax2, (9.1, 8.10), (8.1, 8.10), color='#94A3B8', ls='--', lw=1.3)
    ax2.text(9.1, 4.4, "Streaming Loop", ha='center', va='center', fontsize=8.0, fontweight='bold', color='#64748B',
            rotation=90, bbox=dict(boxstyle='round,pad=0.2', fc='#FFFFFF', ec='#CBD5E1', lw=0.6))

    plt.tight_layout()
    fig.savefig("results/fig_ccaf_architecture_and_flowchart.png", dpi=300, bbox_inches='tight')
    fig.savefig("paper_latex/figures/fig_ccaf_architecture_and_flowchart.png", dpi=300, bbox_inches='tight')
    fig.savefig("results/fig_ccaf_architecture_and_flowchart.pdf", bbox_inches='tight')
    fig.savefig("paper_latex/figures/fig_ccaf_architecture_and_flowchart.pdf", bbox_inches='tight')
    plt.close(fig)
    print("  [SAVED] Spacious Combined 2-Panel Figure (PNG & PDF)")


# ==============================================================================
# 4. MULTI-DOMAIN REAL-WORLD APPLICATION PIPELINE
# ==============================================================================
def render_multidomain_pipeline():
    print("[4/4] Rendering Multi-Domain Pipeline (fig_ccaf_multidomain_pipeline.png / .pdf)...")
    fig2 = plt.figure(figsize=(15.5, 7.2), dpi=300)
    gs2 = fig2.add_gridspec(1, 3, wspace=0.16)

    domains = [
        {
            "title": "(a) Acoustic Echo Cancellation",
            "subtitle": "Aachen AIR 1.4 & Microsoft AEC Datasets",
            "color": "#0284C7",
            "bg": "#F0F9FF",
            "badge_tag": "Acoustic Audio Systems",
            "steps": [
                ("1. Loudspeaker Signal x(n)", "Far-end audio playback feeding acoustic room impulse response."),
                ("2. Room Impulse Response", "Acoustic path h_o(n) undergoes sudden shifts during speaker movement."),
                ("3. Microphone Pickup d(n)", "Near-end speech + ambient room noise + reflected echo."),
                ("4. CCAF-DB Echo Cancellation", "Dead-band prevents step-size explosion during double-talk periods."),
                ("5. Performance Highlights", "ERLE: 38.6 dB  |  Re-adaptation Delay: < 28 ms at 16 kHz")
            ]
        },
        {
            "title": "(b) Clinical ECG Motion Denoising",
            "subtitle": "PhysioNet MIT-BIH & NSTDB Record 118",
            "color": "#0D9488",
            "bg": "#F0FDFA",
            "badge_tag": "Cardiovascular Telemetry",
            "steps": [
                ("1. ECG Reference u(n)", "Calibrated reference lead capturing cardiac activity baseline."),
                ("2. Electrode Motion Artifacts", "Skin-electrode stretch generates massive baseline wander bursts."),
                ("3. Contaminated Signal d(n)", "Severe non-stationary noise obscuring diagnostic ST-T wave segment."),
                ("4. CCAF-DB Artifact Removal", "Provides 90% confidence ribbon around true clinical cardiac waveform."),
                ("5. Performance Highlights", "MSE: 1.44  |  Coverage: 89.9%  |  Preserves ST morphology")
            ]
        },
        {
            "title": "(c) Neurological EEG Artifacts",
            "subtitle": "EEGdenoiseNet Benchmark (-2 dB SNR)",
            "color": "#7C3AED",
            "bg": "#FAF5FF",
            "badge_tag": "Brain-Computer Interfaces",
            "steps": [
                ("1. EOG Reference u(n)", "Frontal electrooculogram lead tracking ocular saccades and eye blinks."),
                ("2. Cranial Volume Conduction", "Blink spikes spread across scalp EEG channels with extreme amplitude."),
                ("3. Noise-Dominant EEG d(n)", "Severe -2 dB SNR condition completely burying cortical rhythms."),
                ("4. CCAF-DB Ocular Filtering", "Scale normalization prevents filter weight destabilization."),
                ("5. Performance Highlights", "53.9% lower error than NLMS (MSE: 31,765 vs 72,824)")
            ]
        }
    ]

    for idx, d in enumerate(domains):
        ax = fig2.add_subplot(gs2[0, idx])
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis('off')

        card = FancyBboxPatch((0.2, 0.2), 9.6, 9.6, boxstyle="round,pad=0.25",
                              ec=d["color"], fc=d["bg"], lw=1.8, zorder=1)
        ax.add_patch(card)

        pill = FancyBboxPatch((1.5, 9.05), 7.0, 0.50, boxstyle="round,pad=0.12",
                              ec=d["color"], fc='#FFFFFF', lw=1.4, zorder=2)
        ax.add_patch(pill)
        ax.text(5.0, 9.30, d["badge_tag"].upper(), ha='center', va='center', 
                fontsize=8.5, fontweight='bold', color=d["color"], zorder=3)

        ax.text(5.0, 8.55, d["title"], ha='center', va='center', fontsize=11.5, fontweight='bold', color='#0F172A', zorder=2)
        ax.text(5.0, 8.12, d["subtitle"], ha='center', va='center', fontsize=8.5, color='#475569', zorder=2)

        y_positions = [6.85, 5.35, 3.85, 2.35, 0.95]
        for step_idx, (stitle, sdesc) in enumerate(d["steps"]):
            y_pos = y_positions[step_idx]
            is_highlight = (step_idx == 4)

            box_fc = '#FFFFFF' if not is_highlight else '#FEF3C7'
            box_ec = '#CBD5E1' if not is_highlight else '#D97706'
            title_color = d["color"] if not is_highlight else '#B45309'

            step_box = FancyBboxPatch((0.6, y_pos - 0.50), 8.8, 1.05, boxstyle="round,pad=0.12",
                                      ec=box_ec, fc=box_fc, lw=1.2 if not is_highlight else 1.5, zorder=2)
            ax.add_patch(step_box)

            ax.text(1.0, y_pos + 0.22, stitle, ha='left', va='center', 
                    fontsize=9.2, fontweight='bold', color=title_color, zorder=3)
            ax.text(1.0, y_pos - 0.18, sdesc, ha='left', va='center', 
                    fontsize=8.0, color='#334155', zorder=3)

            if step_idx < 4:
                arrow = FancyArrowPatch((5.0, y_pos - 0.52), (5.0, y_positions[step_idx + 1] + 0.55),
                                        arrowstyle='-|>', mutation_scale=11, color=d["color"], lw=1.3, zorder=3)
                ax.add_patch(arrow)

    plt.tight_layout()
    fig2.savefig("results/fig_ccaf_multidomain_pipeline.png", dpi=300, bbox_inches='tight')
    fig2.savefig("paper_latex/figures/fig_ccaf_multidomain_pipeline.png", dpi=300, bbox_inches='tight')
    fig2.savefig("results/fig_ccaf_multidomain_pipeline.pdf", bbox_inches='tight')
    fig2.savefig("paper_latex/figures/fig_ccaf_multidomain_pipeline.pdf", bbox_inches='tight')
    plt.close(fig2)
    print("  [SAVED] Multi-Domain Pipeline (PNG & PDF)")


if __name__ == "__main__":
    print("=" * 80)
    print("GENERATING ZERO-OVERFLOW SYSTEM ARCHITECTURE & FLOWCHARTS (STANDALONE + COMBINED)")
    print("=" * 80)
    render_standalone_architecture()
    render_standalone_flowchart()
    render_combined_architecture_and_flowchart()
    render_multidomain_pipeline()
    print("=" * 80)
    print("ALL ARCHITECTURE & FLOWCHART FIGURES SUCCESSFULLY GENERATED!")
    print("=" * 80)
