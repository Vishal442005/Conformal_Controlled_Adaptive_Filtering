"""
export_all_plots_to_pdf.py
Converts and exports all 16 figures in the paper to publication-grade PDF format
in both results/ and paper_latex/figures/.
Ensures RGB color-space, high-DPI preservation, and direct PDF embedding compatibility
for lightning-fast compilation in Overleaf and local LaTeX engines.
"""

import os
import shutil
from PIL import Image

FIGURE_NAMES = [
    "fig_ccaf_architecture",
    "fig_ccaf_flowchart",
    "fig_ccaf_architecture_and_flowchart",
    "fig_ccaf_multidomain_pipeline",
    "s3_benchmark_comparison",
    "monte_carlo_S1",
    "monte_carlo_S2",
    "monte_carlo_S4",
    "monte_carlo_S5",
    "monte_carlo_S6",
    "friedman_cd_diagram",
    "s7_ecg_validation",
    "s7_eeg_validation",
    "air_database_aec_benchmark",
    "phase6_ablation_gamma_and_p",
    "computational_complexity_benchmark",
    "comparative_study_benchmark",
    "microsoft_aec_benchmark",
    "fig_conformal_calibration_and_reliability",
    "fig_conformal_calibration_and_reliability_col",
    "fig_state_space_phase_portrait",
    "fig_state_space_phase_portrait_col",
    "fig_hyperparameter_landscape_nomogram",
    "fig_multicriteria_radar_benchmark",
    "fig_acoustic_rir_energy_decay_and_tracking"
]

RESULTS_DIR = os.path.abspath("results")
LATEX_FIG_DIR = os.path.abspath("paper_latex/figures")

os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(LATEX_FIG_DIR, exist_ok=True)

def convert_png_to_pdf(png_path, pdf_path):
    img = Image.open(png_path)
    # Ensure RGB without alpha channel to prevent slow decompression in pdfLaTeX
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba_img = img.convert("RGBA")
        background = Image.new("RGB", rgba_img.size, (255, 255, 255))
        background.paste(rgba_img, mask=rgba_img.split()[3])
        rgb_img = background
    elif img.mode != "RGB":
        rgb_img = img.convert("RGB")
    else:
        rgb_img = img

    rgb_img.save(pdf_path, "PDF", resolution=300.0)
    print(f"  [CONVERTED] {os.path.basename(png_path)} -> {os.path.basename(pdf_path)} ({os.path.getsize(pdf_path)/1024:.1f} KB)")

def main():
    print("=" * 70)
    print("EXPORTING ALL 16 PAPER PLOTS TO PDF (results/ and paper_latex/figures/)")
    print("=" * 70)

    for base_name in FIGURE_NAMES:
        # Check source PNG in paper_latex/figures or results
        latex_png = os.path.join(LATEX_FIG_DIR, f"{base_name}.png")
        results_png = os.path.join(RESULTS_DIR, f"{base_name}.png")

        src_png = None
        if os.path.exists(latex_png):
            src_png = latex_png
        elif os.path.exists(results_png):
            src_png = results_png
        else:
            print(f"  [WARNING] PNG source not found for {base_name}!")
            continue

        latex_pdf = os.path.join(LATEX_FIG_DIR, f"{base_name}.pdf")
        results_pdf = os.path.join(RESULTS_DIR, f"{base_name}.pdf")

        # Convert to PDF
        convert_png_to_pdf(src_png, latex_pdf)
        # Also copy / sync to results
        shutil.copy2(latex_pdf, results_pdf)

    print("\nVerifying all 16 PDF figures in paper_latex/figures/:")
    missing = []
    for base_name in FIGURE_NAMES:
        pdf_file = os.path.join(LATEX_FIG_DIR, f"{base_name}.pdf")
        if os.path.exists(pdf_file):
            size_kb = os.path.getsize(pdf_file) / 1024.0
            print(f"  OK: {base_name}.pdf ({size_kb:.1f} KB)")
        else:
            missing.append(base_name)

    if missing:
        print(f"\nERROR: Missing PDF files: {missing}")
    else:
        print("\nALL 16 PAPER FIGURES SUCCESSFULLY SAVED AS HIGH-RES PDFS!")

if __name__ == "__main__":
    main()
