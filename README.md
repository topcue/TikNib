# Description
TikNib is a binary code similarity analysis (BCSA) tool. TikNib enables
evaluating the effectiveness of features used in BCSA. One can extend it to
evaluate other interesting features as well as similarity metrics.

Currently, TikNib supports features as listed below. TikNib also employs an
interpretable feature engineering model, which essentially measures the relative
difference between each feature. In other words, it captures how much each
feature differs across different compile options. Note that this model and its
internal similarity scoring metric is not the best approach for addressing BCSA
problems, but it can help analyze how the way of compilation affects each
feature.

TikNib currently focuses on function-level similarity analysis, which is a
fundamental unit of binary analysis.

For more details, please check [our
paper](https://arxiv.org/abs/2011.10749).

# Dataset
For building the cross-compiling environment and dataset, please check
[BinKit](https://github.com/SoftSec-KAIST/BinKit).

# Supported features

### CFG features
- cfg_size
- cfg_avg_degree
- cfg_num_degree
- cfg_avg_loopintersize
- cfg_avg_loopsize
- cfg_avg_sccsize
- cfg_num_backedges
- cfg_num_loops
- cfg_num_loops_inter
- cfg_num_scc
- cfg_sum_loopintersize
- cfg_sum_loopsize
- cfg_sum_sccsize

### CG features
- cg_num_callees
- cg_num_callers
- cg_num_imported_callees
- cg_num_incalls
- cg_num_outcalls
- cg_num_imported_calls

### Instruction features
- inst_avg_abs_dtransfer
- inst_avg_abs_arith
- inst_avg_abs_ctransfer
- inst_num_abs_dtransfer (dtransfer + misc)
- inst_num_abs_arith (arith + shift)
- inst_num_abs_ctransfer (ctransfer + cond ctransfer)
- inst_avg_inst
- inst_avg_floatinst
- inst_avg_logic
- inst_avg_dtransfer
- inst_avg_arith
- inst_avg_cmp
- inst_avg_shift
- inst_avg_bitflag
- inst_avg_cndctransfer
- inst_avg_ctransfer
- inst_avg_misc
- inst_num_inst
- inst_num_floatinst
- inst_num_logic
- inst_num_dtransfer
- inst_num_arith
- inst_num_cmp
- inst_num_shift
- inst_num_bitflag
- inst_num_cndctransfer
- inst_num_ctransfer
- inst_num_misc

### Type features
- data_mul_arg_type
- data_num_args
- data_ret_type

# How to use
TikNib has two parts: ground truth building and feature extraction.

## Scripts Used for Our Evaluation

To see the scripts used in our evaluation, please check the shell scripts under
[/helper](/helper/). For example, [run_gnu.sh](/helper/run_gnu.sh) builds ground
truth and extracts features for GNU packages. Then,
[run_gnu_roc.sh](/helper/run_gnu_roc.sh) computes the ROC AUC for the results.
You have to run these scripts sequentially as the second one utilizes the cached
results obtained from the first one.
We also added top-k results for the OpenSSL package, which is described in
Sec 5.3 in [our paper](https://arxiv.org/abs/2011.10749).
Please check [run_openssl_roc.sh](/helper/run_openssl_roc.sh) and
[run_openssl_roc_topk.sh](/helper/run_openssl_roc_topk.sh) in the same
directory, of which should also be executed sequentially.

## Building Ground Truth
TikNib includes scripts for building ground truth for evaluation, as described
in Sec 3.2 in [our paper](https://arxiv.org/abs/2011.10749). After compiling the
datasets using [BinKit](https://github.com/SoftSec-KAIST/BinKit), we build
ground truth as below.

Given two functions of the same name, we check if they originated from the same
source files and if their line numbers are the same. We also check if both
functions are from the same package and from the binaries of the same name to
confirm their equivalence. Based on these criteria we conducted several steps to
build ground truth and clean the datasets. For more details, please check [our
paper](https://arxiv.org/abs/2011.10749).

### 1. Configure path variables for IDA Pro and this repository.

Configure path variables for your environment at `config/path_variables.py`.


### 2. Run IDA Pro to extract preliminary data for each functions.

**This step takes the most time.**

This step fetches preliminary data for the functions in each binary and stores
the data in a `pickle` format. For a given binary, it generates a pickle file on
the same path with a suffix of `.pickle`. Please configure the `chunk_size` for
parallel processing.

For IDA Pro v6.95 (original version in the paper), use
`tiknib/ida/fetch_funcdata.py`.

```bash
$ python helper/do_idascript.py \
    --idapath "/home/dongkwan/.tools/ida-6.95" \
    --idc "tiknib/ida/fetch_funcdata.py" \
    --input_list "example/input_list_find.txt" \
    --log
```

For IDA Pro v7.5, use `tiknib/ida/fetch_funcdata_v7.5.py`.

```bash
$ python helper/do_idascript.py \
    --idapath "/home/dongkwan/.tools/ida-7.5" \
    --idc "tiknib/ida/fetch_funcdata_v7.5.py" \
    --input_list "example/input_list_find.txt" \
    --log
```

Additionally, **you can use this script to run any idascript for numerous
binaries in parallel.**


### 3. Extract source file names and line numbers to build ground truth.
This extracts source file name and line number by parsing the debugging
information in a given binary. The binary must have been compiled with
the `-g` option.

```bash
$ python helper/extract_lineno.py \
    --input_list "example/input_list_find.txt" \
    --threshold 1
```

### 4. Filter functions.
This filters functions by checking the source file name and line number.
This removes compiler intrinsic functions and duplicate functions spread
over multiple binaries within the same package.

```bash
$ python helper/filter_functions.py \
    --input_list "example/input_list_find.txt" \
    --threshold 1
```

### (Optional) 5. Counting the number of functions.
This counts the number of functions and generates a graph of that function
on the same path of `input_list`. This also prints the numbers separated
by `','`. In the below example, a pdf file containing the graph will be
created in `example/input_list_find.pdf`

```bash
$ python helper/count_functions.py \
    --input_list "example/input_list_find.txt" \
    --threshold 1
```


## Extracting Features

### 1. Run IDA Pro to extract preliminary data for each functions.
This is the exact same step as the one described above.

### 2. Extract function type information for type features.
By utilizing `ctags`, this will extract type information. This will add
`abstract_args_type` and `abstract_ret_type` into the previously created
`.pickle` file.

```bash
$ python helper/extract_functype.py \
    --source_list "example/source_list.txt" \
    --input_list "example/input_list_find.txt" \
    --ctags_dir "data/ctags" \
    --threshold 1
```

For example, for a function type of `mode_change *__usercall@<rax>(const char
*ref_file@<rsi>)` extracted from IDA Pro, it will follow the ctags and
recognizes `mode_change` represents for a custom `struct`. Consequently, it adds
new data as below.

``` python
    'abstract_args_type': ['char *'],
    'abstract_ret_type': 'struct *',
```

### 3. Extract numeric presemantic features and type features.

This extracts numeric presemantic features as stated above.

```bash
$ python helper/extract_features.py \
    --input_list "example/input_list_find.txt" \
    --threshold 1
```

The extracted features will be stored in each `.pickle` file. Below is an
example showing a part of extracted features for the `mode_create_from_ref`
function in the `find` binary in `findutils`.

```python
{
    'package': 'findutils-4.6.0',
    'bin_name': 'find.elf',
    'name': 'mode_create_from_ref',
    'arch': 'x86_64',
    'opti': 'O3',
    'compiler': 'gcc-8.2.0',
    'others': 'normal',
    'func_type': 'mode_change *__usercall@<rax>(const char *ref_file@<rsi>)',
    'abstract_args_type': ['char *'],
    'ret_type': 'mode_change *',
    'abstract_ret_type': 'struct *',
    'cfg': [(0, 1), (0, 2), (1, 2)],
    'cfg_size': 3,
    'feature': {
        'cfg_avg_degree': 2,
        'cfg_avg_indegree': 1,
        'cfg_avg_loopintersize': 0,
        'cfg_avg_loopsize': 0,
        'cfg_avg_outdegree': 1,
        'cfg_avg_sccsize': 1,
        'cfg_max_depth': 2,
        'cfg_max_width': 2,
        'cfg_num_backedges': 0,
        'cfg_num_bfs_edges': 2,
        'cfg_num_degree': 6,
        'cfg_num_indegree': 3,
        'cfg_num_loops': 0,
        'cfg_num_loops_inter': 0,
        'cfg_num_outdegree': 3,
        'cfg_num_scc': 3,
        'cfg_size': 3,
        'cfg_sum_loopintersize': 0,
        'cfg_sum_loopsize': 0,
        'cfg_sum_sccsize': 3,
        'cg_num_callees': 2,
        'cg_num_callers': 0,
        'cg_num_imported_callees': 1,
        'cg_num_imported_calls': 1,
        'cg_num_incalls': 0,
        'cg_num_outcalls': 2,
        'data_avg_abs_strings': 0,
        'data_avg_arg_type': 2,
        'data_avg_consts': 144,
        'data_avg_strlen': 0,
        'data_mul_arg_type': 2,
        'data_num_args': 1,
        'data_num_consts': 1,
        'data_num_strings': 0,
        'data_ret_type': 2,
        'data_sum_abs_strings': 0,
        'data_sum_abs_strings_seq': 0,
        'data_sum_arg_type': 2,
        'data_sum_arg_type_seq': 2,
        'data_sum_consts_seq': 144,
        'data_sum_strlen': 0,
        'data_sum_strlen_seq': 0,
        'inst_avg_abs_arith': 0.6666666666666666,
        'inst_avg_abs_ctransfer': 1.3333333333333333,
        'inst_avg_abs_dtransfer': 4.666666666666667,
        'inst_avg_arith': 0.6666666666666666,
        'inst_avg_bitflag': 0.3333333333333333,
        'inst_avg_cmp': 0.3333333333333333,
        'inst_avg_cndctransfer': 0.3333333333333333,
        'inst_avg_ctransfer': 1.0,
        'inst_avg_dtransfer': 4.666666666666667,
        'inst_avg_grp_call': 0.6666666666666666,
        'inst_avg_grp_jump': 0.3333333333333333,
        'inst_avg_grp_ret': 0.3333333333333333,
        'inst_avg_logic': 0.3333333333333333,
        'inst_avg_total': 7.333333333333333,
        'inst_num_abs_arith': 2.0,
        'inst_num_abs_ctransfer': 4.0,
        'inst_num_abs_dtransfer': 14.0,
        'inst_num_arith': 2.0,
        'inst_num_bitflag': 1.0,
        'inst_num_cmp': 1.0,
        'inst_num_cndctransfer': 1.0,
        'inst_num_ctransfer': 3.0,
        'inst_num_dtransfer': 14.0,
        'inst_num_grp_call': 2.0,
        'inst_num_grp_jump': 1.0,
        'inst_num_grp_ret': 1.0,
        'inst_num_logic': 1.0,
        'inst_num_total': 22
    },
    ...
}
```

### 4. Evaluate target configuration

```bash
$ python helper/test_roc.py \
    --input_list "example/input_list_find.txt" \
    --train_funcs_limit 200000 \
    --config "config/gnu/config_gnu_normal_all.yml"
```

For more details, please check `example/`. All configuration files for our
experiments are in `config/`. The time spent for running `example/example.sh`
took as below.

- Processing IDA analysis: 1384 s
- Extracting function types: 102 s
- Extracting features: 61 s
- Training: 31 s
- Testing: 0.8 s

You can obtain below information after running `test_roc.py`.

```
Features:
inst_num_abs_ctransfer (inter): 0.4749
inst_num_cmp (inter): 0.5500
inst_num_cndctransfer (inter): 0.5906
...
...
...
Avg \# of selected features: 13.0000
Avg. TP-TN Gap: 0.3866
Avg. TP-TN Gap of Grey: 0.4699
Avg. ROC: 0.9424
Std. of ROC: 0.0056
Avg. AP: 0.9453
Std. of AP: 0.0058
Avg. Train time: 30.4179
AVg. Test time: 1.4817
Avg. # of Train Pairs: 155437
Avg. # of Test Pairs: 17270
```

# Use Case
One may use BCSA for several tasks such as malware detectio, plagiarism
detection, authorship identification, or vulnerability discovery.

You can take a look at [this repo](https://github.com/SysSec-KAIST/FirmKit)
for an example of IoT vulnerability discovery.


# Issues

### Tested environment
We ran all our experiments on a server equipped with four Intel Xeon E7-8867v4
2.40 GHz CPUs (total 144 cores), 896 GB DDR4 RAM, and 4 TB SSD. We setup Ubuntu
16.04 with IDA Pro v6.95 on the server.

Currently, it works on IDA Pro v6.95 and v7.5 with Python 3.8.0 on the system.

# Authors
This project has been conducted by the below authors at KAIST.
* [Dongkwan Kim](https://0xdkay.me/)
* [Eunsoo Kim](https://hahah.kim)
* [Sang Kil Cha](https://softsec.kaist.ac.kr/~sangkilc/)
* [Sooel Son](https://sites.google.com/site/ssonkaist/home)
* [Yongdae Kim](https://syssec.kaist.ac.kr/~yongdaek/)

# Citation
We would appreciate if you consider citing [our
paper](https://ieeexplore.ieee.org/document/9813408) when using BinKit.
```bibtex
@ARTICLE{kim:tse:2022,
  author={Kim, Dongkwan and Kim, Eunsoo and Cha, Sang Kil and Son, Sooel and Kim, Yongdae},
  journal={IEEE Transactions on Software Engineering}, 
  title={Revisiting Binary Code Similarity Analysis using Interpretable Feature Engineering and Lessons Learned}, 
  year={2022},
  volume={},
  number={},
  pages={1-23},
  doi={10.1109/TSE.2022.3187689}
}
```

---

# How to use (WIP)

This repository is a local fork of TikNib. The original README above is kept as
reference. The notes below describe the current layout and replay steps for
this workspace.

The key difference from upstream TikNib is the execution model:

- upstream TikNib documentation assumes a Linux environment with IDA available
  in that environment
- this fork is operated from WSL
- IDA Pro itself is installed on Windows
- the WSL-side Python helpers invoke the Windows IDA installation and use a
  Windows-visible dataset path

## Current local environment

- WSL repo path: `/home/user/TikNib`
- WSL-visible Windows workspace path: `/home/user/win_workspace`
- Windows workspace path: `C:/Users/user/workspace`
- Windows IDA path exposed through WSL: `/home/user/win_workspace/IDA`
- Dataset root used in local tests: `/home/user/win_workspace/storage/tiknib`
- Python environment used in local tests: `venv/`
- Tested IDA script in this fork: `tiknib/ida/fetch_funcdata_v7.5.py`

The important relationship here is that:

- `/home/user/win_workspace` is a symlink to `/mnt/c/Users/user/workspace`
- that same location is seen by Windows as `C:/Users/user/workspace`

In other words, the helpers in WSL and IDA Pro on Windows are operating on the
same underlying files through two different path syntaxes.

This is one of the core requirements for the current implementation. The code
assumes the following mapping:

- WSL prefix: `/home/user/win_workspace`
- Windows prefix: `C:/Users/user/workspace`

That mapping is used in two places:

- `tiknib/idascript.py`: converts WSL dataset paths into Windows paths before
  invoking IDA Pro
- `script/handle_pickle.py`: converts Windows paths embedded in pickle files
  back into WSL-visible paths when needed

This fork currently assumes a mixed WSL/Windows layout:

- The repository is opened from WSL.
- IDA Pro is installed on Windows and is invoked from WSL.
- The binaries analyzed by IDA must live on a Windows-visible path.
- Test datasets are stored under `/home/user/win_workspace/storage/...`.

## Current replay inputs

Example replay inputs live under `example/`.

- `example/test1/`
- `example/test2/`

Each example directory contains:

- `list.txt`: absolute binary paths, one per line
- `sources.txt`: absolute source root paths, one per line

## File and directory conventions

### 1. Binary naming

TikNib parses binary metadata from the filename. The local examples follow:

`<package>_<compiler>_<arch>_<bits>_<opti>_<binary>.elf`

Examples:

- `coreutils_clang-18.1.8_x86_64_O0_cat.elf`
- `openssl_gcc-14.2.0_x86_64_O0_openssl.elf`

If the filename format does not match this pattern, helpers such as
`parse_fname()` and downstream grouping logic will fail or misclassify data.

### 2. Dataset directory layout

The local replay datasets are grouped by test set name under:

- `/home/user/win_workspace/storage/tiknib/test1`
- `/home/user/win_workspace/storage/tiknib/test2`

Each test set contains one or more package subdirectories, such as:

- `coreutils/`
- `openssl/`

Each package directory is expected to contain at least:

- the original `.elf`
- `<name>.elf.done`
- `<name>.elf.output`
- `<name>.elf.pickle`

Later steps generate:

- `<name>.elf.filtered.pickle`
- `<name>.elf.feature.pickle`

### 3. Path handling

The local helper `script/handle_pickle.py` validates a dataset directory and can
rewrite Windows-style paths inside `.elf.pickle` files into WSL paths.

In the current local replay runs, the `.pickle` files produced by Windows IDA
did contain Windows paths and were rewritten to WSL paths before the later
stages.

## Pipeline used in this fork

The local replay order is:

1. `helper/do_idascript.py`
2. `script/handle_pickle.py`
3. `helper/extract_lineno.py`
4. `helper/filter_functions.py`
5. `helper/extract_functype.py`
6. `helper/extract_features.py`

### Step 1 notes

`do_idascript.py` writes files next to the target ELF, so the dataset
directory must be writable.

This fork does not use a Linux-native IDA installation. The expected setup is:

- WSL runs the helper scripts
- Windows runs IDA Pro
- the dataset is accessed through a path that both sides agree on

When IDA is involved, this fork relies on paths that are visible from the
Windows side. In past successful runs, IDA loaded files from:

- `C:\Users\user\workspace\storage\tiknib\...`

If a new dataset is prepared, matching that path convention is the safest
option.

## Replay script

The local replay helper is:

- `script/test.sh`

It accepts a test set name and runs the full local replay pipeline up to
feature extraction:

```bash
bash script/test.sh test1
bash script/test.sh test2
```

By default, running it without arguments uses `test1`.

What the script does:

1. checks that the selected input files and dataset directory exist
2. checks that the current WSL session can launch Windows executables
3. removes previous generated files only for the selected test set
4. runs `do_idascript.py`
5. runs `handle_pickle.py --yes`
6. runs `extract_lineno.py`
7. runs `filter_functions.py`
8. runs `extract_functype.py`
9. runs `extract_features.py`

Operational notes:

- only one `script/test.sh` run is allowed at a time
- the script is intended for a Windows-launched WSL terminal
- an SSH-created WSL shell may not have working Windows interop even on the
  same machine

Verified local runs:

- `2026-04-28`: `bash script/test.sh test1` completed successfully
- `2026-04-28`: `bash script/test.sh test2` completed successfully
- both runs finished through `extract_features.py`
- both runs produced `220` `.feature.pickle` files

## Step-by-step replay

If you do not want to run the whole helper script at once, replay `test1` or
`test2` step by step.

The examples below use `test1`. Replace `test1` with `test2` if needed.

### Step 0: Check the inputs

Confirm that these files exist:

- `example/test1/list.txt`
- `example/test1/sources.txt`
- `/home/user/win_workspace/storage/tiknib/test1`

`list.txt` is the list of target binaries. `sources.txt` is the list of source
roots used later by `ctags`.

### Step 1: Run IDA and create base pickle files

```bash
python helper/do_idascript.py \
  --idapath "/home/user/win_workspace/IDA" \
  --idc "tiknib/ida/fetch_funcdata_v7.5.py" \
  --input_list "example/test1/list.txt"
```

What this step reads:

- `example/test1/list.txt`
- each `.elf` listed in that file

What this step writes next to each ELF:

- `<name>.elf.done`
- `<name>.elf.output`
- `<name>.elf.pickle`

Purpose:

- run IDA
- collect function-level raw data
- save the initial function list in pickle form

This is the most environment-sensitive step in this fork because it crosses the
WSL/Windows boundary.

Things to verify after step 1:

- `.done` exists
- `.output` exists
- `.pickle` exists

If this step fails, check:

- whether the dataset directory is writable
- whether the ELF path is visible from the Windows side
- whether the Windows IDA installation path is correct
- whether the IDA script path matches the local setup
- whether `echo $WSL_INTEROP` is non-empty
- whether `cmd.exe /c echo ok` works in the current shell
- the corresponding `.output` log

### Step 2: Normalize paths inside pickle files if needed

```bash
python script/handle_pickle.py /home/user/win_workspace/storage/tiknib/test1
```

Purpose:

- validate the dataset directory layout
- scan `.elf.pickle` files for embedded Windows paths
- optionally rewrite them to WSL paths

What this step reads:

- all `.elf.pickle` files under `/home/user/win_workspace/storage/tiknib/test1`

What this step may modify:

- the same `.elf.pickle` files, but only if path replacement is needed

In the current local replay runs, this step rewrote Windows paths in all
generated `.elf.pickle` files.

If you want the same non-interactive behavior used by `script/test.sh`, run:

```bash
python script/handle_pickle.py --yes /home/user/win_workspace/storage/tiknib/test1
```

### Step 3: Add source file and line number information

```bash
python helper/extract_lineno.py \
  --input_list "example/test1/list.txt" \
  --threshold 1000
```

Purpose:

- read debug information from each binary
- map function addresses to source path and line number
- update the base `.pickle`

What this step reads:

- `example/test1/list.txt`
- each `<name>.elf.pickle`
- debug information from the ELF

What this step writes:

- updated `<name>.elf.pickle`

Fields added or updated in function records:

- `src_path`
- `src_file`
- `src_line`

### Step 4: Filter functions and build the local oracle

```bash
python helper/filter_functions.py \
  --input_list "example/test1/list.txt" \
  --threshold 1
```

Purpose:

- keep only `.text` functions
- drop entries without source mapping
- drop functions outside the package source path
- drop `sub_...` names
- build a per-package oracle to keep unique source locations

What this step reads:

- `example/test1/list.txt`
- each updated `<name>.elf.pickle`

What this step writes:

- `<name>.elf.filtered.pickle`

Terminal output from this step is useful. It prints per-package counts in this
order:

- original functions
- `.text` functions
- functions with source info
- functions whose source path matches the package
- functions after removing `sub_...`
- functions after oracle filtering
- readelf-based count placeholder

### Step 5: Build ctags and add abstracted type information

```bash
python helper/extract_functype.py \
  --input_list "example/test1/list.txt" \
  --source_list "example/test1/sources.txt" \
  --ctags_dir "data/test1" \
  --threshold 1
```

Purpose:

- run `ctags` on the source roots
- build a type map
- enrich each filtered function with abstract argument and return types

What this step reads:

- `example/test1/list.txt`
- `example/test1/sources.txt`
- each `<name>.elf.filtered.pickle`

What this step writes:

- `data/test1/*.tags`
- updated `<name>.elf.filtered.pickle`

Fields added in function records:

- `abstract_args_type`
- `abstract_ret_type`

Expected tag files:

- `data/test1/coreutils.tags`
- `data/test1/openssl.tags`
- `data/test1/include.tags`

### Step 6: Extract numeric features

```bash
python helper/extract_features.py \
  --input_list "example/test1/list.txt" \
  --threshold 1
```

Purpose:

- load each `.filtered.pickle`
- compute ASM, CFG, CG, data, and type-related features
- store them in a separate feature pickle

What this step reads:

- `example/test1/list.txt`
- each `<name>.elf.filtered.pickle`

What this step writes:

- `<name>.elf.feature.pickle`

Field added in function records:

- `feature`

### Step 7: Optional evaluation

The local replay notes above stop at feature extraction. If you want to proceed
to model evaluation, use `helper/test_roc.py` with one of the YAML files in
`config/`.

## Cleanup notes

- `script/cleanup_tiknib_test.py test1` removes generated files only from
  `test1` while keeping the original `.elf`
- `script/cleanup_tiknib_test.py test2` does the same for `test2`
- running it without an argument cleans both `test1` and `test2`
