import argparse
import glob
import os
import pickle
import re

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d


VERSION_RE = re.compile(r"config_binforge_comp_(clang|gcc)(\d+)$")


def find_completed_runs(results_root, compiler):
    pattern = os.path.join(results_root, f"config_binforge_comp_{compiler}*", "*")
    run_dirs = sorted(glob.glob(pattern))
    runs = []
    for run_dir in run_dirs:
        cfg_name = os.path.basename(os.path.dirname(run_dir))
        match = VERSION_RE.match(cfg_name)
        if not match or match.group(1) != compiler:
            continue
        version = int(match.group(2))
        log_path = os.path.join(run_dir, "log.txt")
        data_paths = sorted(glob.glob(os.path.join(run_dir, "data-*.pickle")))
        if not os.path.isfile(log_path) or len(data_paths) != 10:
            continue
        auc_value = load_avg_roc(log_path)
        if auc_value is None:
            continue
        mean_fpr, mean_tpr = load_mean_roc(data_paths)
        runs.append(
            {
                "version": version,
                "auc": auc_value,
                "fpr": mean_fpr,
                "tpr": mean_tpr,
                "run_dir": run_dir,
            }
        )
    return sorted(runs, key=lambda x: x["version"])


def load_avg_roc(log_path):
    text = open(log_path, "r", errors="ignore").read()
    match = re.search(r"Avg\. ROC:\s*([0-9.]+)", text)
    if not match:
        return None
    return float(match.group(1))


def load_mean_roc(data_paths):
    grid = np.linspace(0.0, 1.0, 500)
    tprs = []
    for data_path in data_paths:
        data = pickle.load(open(data_path, "rb"))
        fpr, tpr, _ = data[3]
        order = np.argsort(fpr)
        fpr = np.asarray(fpr)[order]
        tpr = np.asarray(tpr)[order]
        uniq_fpr, uniq_idx = np.unique(fpr, return_index=True)
        uniq_tpr = tpr[uniq_idx]
        interp_func = interp1d(
            uniq_fpr,
            uniq_tpr,
            kind="linear",
            bounds_error=False,
            fill_value=(uniq_tpr[0], uniq_tpr[-1]),
        )
        tprs.append(interp_func(grid))
    mean_tpr = np.mean(np.vstack(tprs), axis=0)
    mean_tpr[0] = 0.0
    mean_tpr[-1] = 1.0
    return grid, mean_tpr


def plot_roc_curves(runs, title, output_file, compiler):
    if not runs:
        raise SystemExit(f"No completed {compiler} runs found.")

    plt.figure(figsize=(10, 5.5))
    linestyles = [
        "dotted",
        "dashed",
        "dashdot",
        (0, (3, 5, 1, 5)),
        (0, (5, 10)),
    ]

    auc_values = [run["auc"] for run in runs]
    best_version = runs[int(np.argmax(auc_values))]["version"]
    worst_version = runs[int(np.argmin(auc_values))]["version"]

    for idx, run in enumerate(runs):
        version = run["version"]
        fpr = run["fpr"]
        tpr = run["tpr"]
        interp_func = interp1d(fpr, tpr, kind="quadratic")
        fpr_smooth = np.linspace(float(np.min(fpr)), float(np.max(fpr)), 500)
        tpr_smooth = interp_func(fpr_smooth)

        if version == best_version:
            color = "blue"
            linestyle = "solid"
            linewidth = 2.5
            alpha = 1.0
        elif version == worst_version:
            color = "red"
            linestyle = "solid"
            linewidth = 2.5
            alpha = 1.0
        else:
            color = "black"
            linestyle = linestyles[idx % len(linestyles)]
            linewidth = 1.0
            alpha = 0.8

        label = f"{compiler.upper()} v{version} (AUC = {run['auc']:.3f})"
        plt.plot(
            fpr_smooth,
            tpr_smooth,
            label=label,
            linewidth=linewidth,
            alpha=alpha,
            color=color,
            linestyle=linestyle,
        )

    plt.xlabel("False Positive Rate", fontsize=22)
    plt.ylabel("True Positive Rate", fontsize=22)
    plt.ylim(0.0, 1.0)
    plt.xlim(0.0, 1.0)
    plt.tick_params(axis="both", which="major", labelsize=16)
    plt.legend(loc="lower right", fontsize=15, ncol=2)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--results_root",
        default="results",
        help="root directory containing config_binforge_comp_* result dirs",
    )
    parser.add_argument(
        "--output_dir",
        default="scripts_binforge_paper",
        help="directory to write generated pdfs",
    )
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    clang_runs = find_completed_runs(args.results_root, "clang")
    gcc_runs = find_completed_runs(args.results_root, "gcc")

    plot_roc_curves(
        clang_runs,
        "ROC AUCs for Different Versions of the Clang Compiler",
        os.path.join(args.output_dir, "clang_roc_curves_mixed.pdf"),
        "clang",
    )
    plot_roc_curves(
        gcc_runs,
        "ROC AUCs for Different Versions of the GCC Compiler",
        os.path.join(args.output_dir, "gcc_roc_curves_mixed.pdf"),
        "gcc",
    )

    print(f"clang_completed_versions {len(clang_runs)}")
    print(f"gcc_completed_versions {len(gcc_runs)}")


if __name__ == "__main__":
    main()
