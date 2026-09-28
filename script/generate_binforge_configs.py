from pathlib import Path
import re


OPTI = ["O0", "O1", "O2", "O3", "Ofast", "Os"]
ARCH = [
    "x86_32",
    "x86_64",
    "arm_32",
    "arm_64",
    "mips_32",
    "mips_64",
    "mipseb_32",
    "mipseb_64",
    "ppc_64",
    "ppceb_32",
    "ppceb_64",
]
GCC = [
    "gcc-8.5.0",
    "gcc-9.5.0",
    "gcc-10.5.0",
    "gcc-11.5.0",
    "gcc-12.4.0",
    "gcc-13.3.0",
]
CLANG = [
    "clang-7.1.0",
    "clang-8.0.1",
    "clang-9.0.1",
    "clang-10.0.1",
    "clang-11.1.0",
    "clang-12.0.1",
    "clang-13.0.1",
    "clang-14.0.6",
    "clang-15.0.7",
    "clang-16.0.6",
    "clang-17.0.6",
    "clang-18.1.8",
    "clang-19.1.7",
]
COMPILER = GCC + CLANG
OTHERS = ["normal"]

FEATURES = [
    "cfg_size",
    "cfg_avg_degree",
    "cfg_num_degree",
    "cfg_avg_loopintersize",
    "cfg_avg_loopsize",
    "cfg_avg_sccsize",
    "cfg_num_backedges",
    "cfg_num_loops",
    "cfg_num_loops_inter",
    "cfg_num_scc",
    "cfg_sum_loopintersize",
    "cfg_sum_loopsize",
    "cfg_sum_sccsize",
    "cg_num_callees",
    "cg_num_callers",
    "cg_num_imported_callees",
    "cg_num_incalls",
    "cg_num_outcalls",
    "cg_num_imported_calls",
    "inst_avg_abs_dtransfer",
    "inst_avg_abs_arith",
    "inst_avg_abs_ctransfer",
    "inst_num_abs_dtransfer",
    "inst_num_abs_arith",
    "inst_num_abs_ctransfer",
    "inst_avg_total",
    "inst_avg_floatinst",
    "inst_avg_logic",
    "inst_avg_dtransfer",
    "inst_avg_arith",
    "inst_avg_cmp",
    "inst_avg_shift",
    "inst_avg_bitflag",
    "inst_avg_cndctransfer",
    "inst_avg_ctransfer",
    "inst_avg_misc",
    "inst_num_total",
    "inst_num_floatinst",
    "inst_num_logic",
    "inst_num_dtransfer",
    "inst_num_arith",
    "inst_num_cmp",
    "inst_num_shift",
    "inst_num_bitflag",
    "inst_num_cndctransfer",
    "inst_num_ctransfer",
    "inst_num_misc",
]

def fmt_list(items, indent=2):
    prefix = " " * indent + "- "
    return "\n".join(f"{prefix}{item}" for item in items)


def make_config(src, dst, fixed, outdir=""):
    lines = [
        "# output directory where the output data will be stored",
        "# if not given, use the config file name as the output directory.",
        f"outdir: {outdir}" if outdir else "outdir:",
        "",
        "# turn on debug mode or not",
        "debug: False",
        "",
        '# this is a random seed for debugging',
        'seed: "TikNib"',
        "",
        "# if True, perform training to select features, otherwise, just use the given",
        "# features.",
        "do_train: True",
        "",
        "# if you specify options, that option will be fixed when selecting true",
        "# positives and negatives.",
        "fixed_options:",
    ]
    if fixed:
        lines.extend(f"  - {name}" for name in fixed)
    else:
        lines.append("#   - arch")
        lines.append("#   - opti")
        lines.append("#   - compiler")
        lines.append("#   - others")
    lines.extend(
        [
            "",
            "features:",
            fmt_list(FEATURES),
        ]
    )
    lines.extend(
        [
            "",
            "src_options:",
            "  opti:",
            fmt_list(src["opti"], 4),
            "  arch:",
            fmt_list(src["arch"], 4),
            "  compiler:",
            fmt_list(src["compiler"], 4),
            "  others:",
            fmt_list(src["others"], 4),
            "",
            "dst_options:",
            "  opti:",
            fmt_list(dst["opti"], 4),
            "  arch:",
            fmt_list(dst["arch"], 4),
            "  compiler:",
            fmt_list(dst["compiler"], 4),
            "  others:",
            fmt_list(dst["others"], 4),
            "",
        ]
    )
    return "\n".join(lines)


def spec(src_opti, dst_opti, src_arch, dst_arch, src_comp, dst_comp, fixed):
    return (
        {
            "opti": src_opti,
            "arch": src_arch,
            "compiler": src_comp,
            "others": OTHERS,
        },
        {
            "opti": dst_opti,
            "arch": dst_arch,
            "compiler": dst_comp,
            "others": OTHERS,
        },
        fixed,
    )


SPECS = {
    "config_binforge_all": spec(OPTI, OPTI, ARCH, ARCH, COMPILER, COMPILER, []),
    "config_binforge_opti_all": spec(OPTI, OPTI, ARCH, ARCH, COMPILER, COMPILER, ["arch", "compiler", "others"]),
    "config_binforge_opti_O0-O3": spec(["O0"], ["O3"], ARCH, ARCH, COMPILER, COMPILER, ["arch", "compiler", "others"]),
    "config_binforge_opti_O0-Os": spec(["O0"], ["Os"], ARCH, ARCH, COMPILER, COMPILER, ["arch", "compiler", "others"]),
    "config_binforge_opti_O1-Os": spec(["O1"], ["Os"], ARCH, ARCH, COMPILER, COMPILER, ["arch", "compiler", "others"]),
    "config_binforge_opti_O2-O3": spec(["O2"], ["O3"], ARCH, ARCH, COMPILER, COMPILER, ["arch", "compiler", "others"]),
    "config_binforge_opti_O3-Os": spec(["O3"], ["Os"], ARCH, ARCH, COMPILER, COMPILER, ["arch", "compiler", "others"]),
    "config_binforge_arch_all": spec(OPTI, OPTI, ARCH, ARCH, COMPILER, COMPILER, ["opti", "compiler", "others"]),
    "config_binforge_arch_bits": spec(
        OPTI,
        OPTI,
        ["x86_32", "arm_32", "mips_32", "mipseb_32", "ppceb_32"],
        ["x86_64", "arm_64", "mips_64", "mipseb_64", "ppc_64", "ppceb_64"],
        COMPILER,
        COMPILER,
        ["opti", "compiler", "others"],
    ),
    "config_binforge_arch_endian": spec(
        OPTI,
        OPTI,
        ["mips_32", "mips_64", "ppc_64"],
        ["mipseb_32", "mipseb_64", "ppceb_64"],
        COMPILER,
        COMPILER,
        ["opti", "compiler", "others"],
    ),
    "config_binforge_arch_arm_mips": spec(
        OPTI, OPTI, ["arm_64"], ["mips_64"], COMPILER, COMPILER, ["opti", "compiler", "others"]
    ),
    "config_binforge_arch_x64-arm": spec(
        OPTI, OPTI, ["x86_64"], ["arm_64"], COMPILER, COMPILER, ["opti", "compiler", "others"]
    ),
    "config_binforge_arch_x64-mips": spec(
        OPTI, OPTI, ["x86_64"], ["mips_64"], COMPILER, COMPILER, ["opti", "compiler", "others"]
    ),
    "config_binforge_comp_all": spec(OPTI, OPTI, ARCH, ARCH, COMPILER, COMPILER, ["arch", "opti", "others"]),
    "config_binforge_comp_gcc-clang": spec(OPTI, OPTI, ARCH, ARCH, GCC, CLANG, ["arch", "opti", "others"]),
    "config_binforge_comp_clang7-clang19": spec(
        OPTI, OPTI, ARCH, ARCH, [CLANG[0]], [CLANG[-1]], ["arch", "opti", "others"]
    ),
    "config_binforge_comp_gcc8-gcc13": spec(
        OPTI, OPTI, ARCH, ARCH, [GCC[0]], [GCC[-1]], ["arch", "opti", "others"]
    ),
}


def main():
    for compiler in CLANG:
        short = compiler.split("-")[1].split(".")[0]
        SPECS[f"config_binforge_comp_clang{short}"] = spec(
            OPTI, OPTI, ARCH, ARCH, [compiler], [compiler], ["others"]
        )
    for compiler in GCC:
        short = compiler.split("-")[1].split(".")[0]
        SPECS[f"config_binforge_comp_gcc{short}"] = spec(
            OPTI, OPTI, ARCH, ARCH, [compiler], [compiler], ["others"]
        )

    def write_config_set(dir_name, list_name, version_list_name, outdir_prefix=""):
        outdir = Path(dir_name)
        outdir.mkdir(parents=True, exist_ok=True)
        for name, (src, dst, fixed) in SPECS.items():
            path = outdir / f"{name}.yml"
            if outdir_prefix:
                cfg_outdir = f"{outdir_prefix}/{name}"
            else:
                cfg_outdir = ""
            path.write_text(
                make_config(src, dst, fixed, outdir=cfg_outdir), encoding="ascii"
            )
        created = sorted(path.name for path in outdir.glob("*.yml"))
        (Path("config") / list_name).write_text(
            "\n".join(f"{Path(dir_name).name}/{name}" for name in created) + "\n",
            encoding="ascii",
        )
        version_re = re.compile(r"config_binforge_comp_(clang|gcc)\d+\.yml$")
        versioned = sorted(name for name in created if version_re.match(name))
        (Path("config") / version_list_name).write_text(
            "\n".join(f"{Path(dir_name).name}/{name}" for name in versioned) + "\n",
            encoding="ascii",
        )

    write_config_set(
        "config/binforge",
        "config_list_binforge.txt",
        "config_list_binforge_versions.txt",
    )
    write_config_set(
        "config/binforge_popcon",
        "config_list_binforge_popcon.txt",
        "config_list_binforge_popcon_versions.txt",
        outdir_prefix="results_popcon",
    )


if __name__ == "__main__":
    main()
