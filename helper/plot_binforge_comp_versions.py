import glob
import os
import pickle
import re
from collections import defaultdict
from optparse import OptionParser

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import auc


VERSION_RE = re.compile(r"config_binforge_comp_(clang|gcc)(\d+)$")


def find_complete_runs(results_root):
    found = defaultdict(dict)
    for path in glob.glob(os.path.join(results_root, "config_binforge_comp_*")):
        base = os.path.basename(path)
        match = VERSION_RE.fullmatch(base)
        if not match:
            continue
        family, version = match.groups()
        candidates = sorted(glob.glob(os.path.join(path, "*")), reverse=True)
        for candidate in candidates:
            if not os.path.isdir(candidate):
                continue
            if not os.path.exists(os.path.join(candidate, "log.txt")):
                continue
            complete = all(
                os.path.exists(os.path.join(candidate, f"data-{idx}.pickle"))
                for idx in range(10)
            )
            if complete:
                found[family][int(version)] = candidate
                break
    return found


def load_mean_roc(run_dir):
    fprs = []
    tprs = []
    aucs = []
    for idx in range(10):
        path = os.path.join(run_dir, f"data-{idx}.pickle")
        with open(path, "rb") as f:
            data = pickle.load(f)
        _, _, _, test_roc_data = data
        fpr, tpr, _ = test_roc_data
        fprs.append(fpr)
        tprs.append(tpr)
        aucs.append(auc(fpr, tpr))

    all_fpr = np.unique(np.concatenate(fprs))
    mean_tpr = np.zeros_like(all_fpr)
    for fpr, tpr in zip(fprs, tprs):
        mean_tpr += np.interp(all_fpr, fpr, tpr)
    mean_tpr /= len(fprs)
    return all_fpr, mean_tpr, float(np.mean(aucs))


def family_sort_key(item):
    version, _, _, _ = item
    return version


def get_colors(entries):
    aucs = [item[3] for item in entries]
    best = max(aucs)
    worst = min(aucs)
    colors = []
    for _, _, _, mean_auc in entries:
        if mean_auc == best:
            colors.append("#1f77b4")
        elif mean_auc == worst:
            colors.append("#d62728")
        else:
            colors.append("#7f7f7f")
    return colors


def plot_family(ax, family, entries):
    entries = sorted(entries, key=family_sort_key)
    colors = get_colors(entries)
    for (version, fpr, tpr, mean_auc), color in zip(entries, colors):
        ax.plot(
            fpr,
            tpr,
            lw=2,
            color=color,
            alpha=0.9,
            label=f"{family.capitalize()} v{version} (AUC = {mean_auc:.3f})",
        )
    ax.plot([0, 1], [0, 1], "k--", lw=1)
    ax.set_xlim([-0.02, 1.02])
    ax.set_ylim([-0.02, 1.02])
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title(family.capitalize())
    ax.legend(frameon=True, loc="lower right", fontsize=10)


def plot_all(results_root, outdir):
    runs = find_complete_runs(results_root)
    families = []
    for family in ("clang", "gcc"):
        entries = []
        for version, run_dir in sorted(runs.get(family, {}).items()):
            fpr, tpr, mean_auc = load_mean_roc(run_dir)
            entries.append((version, fpr, tpr, mean_auc))
        if entries:
            families.append((family, entries))

    if not families:
        raise SystemExit("No complete versioned compiler ROC results were found.")

    plt.style.use("seaborn-v0_8-white")
    fig, axes = plt.subplots(1, len(families), figsize=(10 * len(families), 8))
    if len(families) == 1:
        axes = [axes]
    for ax, (family, entries) in zip(axes, families):
        plot_family(ax, family, entries)
    fig.tight_layout()
    os.makedirs(outdir, exist_ok=True)
    pdf_path = os.path.join(outdir, "binforge_compiler_versions_roc.pdf")
    png_path = os.path.join(outdir, "binforge_compiler_versions_roc.png")
    fig.savefig(pdf_path, format="pdf")
    fig.savefig(png_path, format="png", dpi=200)
    plt.close(fig)
    print(pdf_path)
    print(png_path)


if __name__ == "__main__":
    op = OptionParser()
    op.add_option(
        "--results_root",
        action="store",
        dest="results_root",
        default="results",
        help="root directory containing result subdirectories",
    )
    op.add_option(
        "--outdir",
        action="store",
        dest="outdir",
        default="results/binforge_compiler_versions",
        help="output directory for the figure",
    )
    opts, _ = op.parse_args()
    plot_all(opts.results_root, opts.outdir)
