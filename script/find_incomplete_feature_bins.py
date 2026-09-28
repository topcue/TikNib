import os
import pickle
from multiprocessing import Pool, cpu_count
from optparse import OptionParser


def feature_path(bin_path):
    return bin_path + ".feature.pickle"


def filtered_path(bin_path):
    return bin_path + ".filtered.pickle"


def classify_bin(bin_path):
    f_filtered = filtered_path(bin_path)
    f_feature = feature_path(bin_path)

    if not os.path.exists(f_filtered):
        return "missing_filtered"

    if not os.path.exists(f_feature):
        return "missing_feature"

    try:
        with open(f_feature, "rb") as f:
            data = pickle.load(f)
    except Exception:
        return "corrupt_feature"

    if not isinstance(data, list):
        return "invalid_feature"

    return None


def classify_bin_worker(bin_path):
    return bin_path, classify_bin(bin_path)


def main():
    op = OptionParser()
    op.add_option("--input_list", dest="input_list", help="input list of binaries")
    op.add_option(
        "--output_list",
        dest="output_list",
        help="write bins needing rerun to this file",
    )
    op.add_option(
        "--delete_bad_features",
        action="store_true",
        dest="delete_bad_features",
        default=False,
        help="delete corrupt/invalid .feature.pickle files",
    )
    op.add_option(
        "--delete_from_list",
        dest="delete_from_list",
        help="delete .feature.pickle files for bins listed in this file without rescanning",
    )
    op.add_option(
        "--jobs",
        dest="jobs",
        type="int",
        default=max(1, cpu_count() or 1),
        help="number of parallel workers for scanning [default: %default]",
    )
    op.add_option(
        "--progress_every",
        dest="progress_every",
        type="int",
        default=1000,
        help="print progress every N bins while scanning [default: %default]",
    )
    opts, _ = op.parse_args()

    if opts.delete_from_list:
        if not os.path.isfile(opts.delete_from_list):
            raise SystemExit("Missing --delete_from_list")
        deleted = 0
        with open(opts.delete_from_list, "r") as f:
            bins = [line.strip() for line in f if line.strip()]
        for bin_path in bins:
            path = feature_path(bin_path)
            if os.path.exists(path):
                os.remove(path)
                deleted += 1
        print(f"listed_bins {len(bins)}")
        print(f"deleted_feature_files {deleted}")
        return

    if not opts.input_list or not os.path.isfile(opts.input_list):
        raise SystemExit("Missing --input_list")

    with open(opts.input_list, "r") as f:
        bins = [line.strip() for line in f if line.strip()]

    rerun_bins = []
    counts = {
        "missing_filtered": 0,
        "missing_feature": 0,
        "corrupt_feature": 0,
        "invalid_feature": 0,
    }

    total_bins = len(bins)
    jobs = max(1, opts.jobs)
    progress_every = max(1, opts.progress_every)
    chunk_size = max(1, min(256, total_bins // (jobs * 8) if total_bins else 1))

    print(f"total_bins {total_bins}")
    print(f"scan_jobs {jobs}")
    print(f"scan_chunk_size {chunk_size}")

    processed = 0
    with Pool(processes=jobs) as pool:
        for bin_path, status in pool.imap_unordered(
            classify_bin_worker, bins, chunksize=chunk_size
        ):
            processed += 1
            if processed == 1 or processed % progress_every == 0 or processed == total_bins:
                print(f"progress {processed}/{total_bins}")

            if not status:
                continue
            counts[status] += 1
            rerun_bins.append(bin_path)
            if opts.delete_bad_features and status in ("corrupt_feature", "invalid_feature"):
                path = feature_path(bin_path)
                if os.path.exists(path):
                    os.remove(path)

    if opts.output_list:
        with open(opts.output_list, "w") as f:
            for bin_path in rerun_bins:
                f.write(bin_path + "\n")

    print(f"rerun_bins {len(rerun_bins)}")
    for key in ("missing_filtered", "missing_feature", "corrupt_feature", "invalid_feature"):
        print(f"{key} {counts[key]}")


if __name__ == "__main__":
    main()
