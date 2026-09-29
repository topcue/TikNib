import os
import sys
from optparse import OptionParser

sys.path.insert(0, os.path.join(sys.path[0], ".."))
from tiknib.idascript import IDAScript
from config.path_variables import IDA_PATH, IDA_FETCH_FUNCDATA, IDA_POOL_SIZE
from tiknib.ida_environment import check_ida_environment

import logging
import coloredlogs

logger = logging.getLogger(__name__)
coloredlogs.install(level=logging.INFO, logger=logger)


if __name__ == "__main__":
    op = OptionParser()
    op.add_option(
        "--indir", action="store", type=str, dest="indir", help="Input directory"
    )
    op.add_option(
        "--idapath",
        action="store",
        type=str,
        dest="idapath",
        default=IDA_PATH,
        help="IDA directory path",
    )
    op.add_option(
        "--idc",
        action="store",
        type=str,
        dest="idc",
        default=IDA_FETCH_FUNCDATA,
        help="IDA script file",
    )
    op.add_option(
        "--idcargs",
        action="store",
        type=str,
        dest="idcargs",
        default="",
        help="arguments seperated by ',' (e.g. --idcargs a,b,c,d)",
    )
    op.add_option("--force", action="store_true", dest="force")
    op.add_option(
        "--pool_size",
        action="store",
        type="int",
        dest="pool_size",
        default=IDA_POOL_SIZE,
        help="maximum number of concurrent IDA processes (from local config)",
    )
    op.add_option(
        "--preflight",
        action="store_true",
        dest="preflight",
        help="also run one pending input synchronously before the worker pool",
    )
    op.add_option("--log", action="store_true", dest="log")
    op.add_option("--stdout", action="store_true", dest="stdout")
    op.add_option("--debug", action="store_true", dest="debug")
    op.add_option(
        "--input_list",
        action="store",
        type=str,
        dest="input_list",
        help="A file containing paths of target binaries",
    )
    op.add_option(
        "--failed_list",
        action="store",
        type=str,
        dest="failed_list",
        help="write IDA failures to this file and exit non-zero",
    )

    (opts, args) = op.parse_args()
    if not opts.input_list or not os.path.exists(opts.input_list):
        op.error("--input_list must name an existing file")
    if opts.pool_size < 1:
        op.error("--pool_size must be at least 1")

    # A retry list describes only the current invocation. Do not leave a stale
    # failure behind after a later successful run.
    if opts.failed_list:
        with open(opts.failed_list, "w"):
            pass

    errors, warnings, details = check_ida_environment(opts.idapath, opts.idc)
    for name, value in sorted(details.items()):
        logger.info("[ENV] %s: %s", name, value)
    for warning in warnings:
        logger.warning("[ENV] %s", warning)
    if errors:
        for error in errors:
            logger.error("[ENV] %s", error)
        sys.exit(2)

    idascript = IDAScript(
        idapath=opts.idapath,
        idc=opts.idc,
        idcargs=opts.idcargs,
        pool_size=opts.pool_size,
        force=opts.force,
        log=opts.log,
        stdout=opts.stdout,
        debug=opts.debug,
    )

    logger.info(f"[DEBUG] idapath   : {idascript.idapath}")
    logger.info(f"[DEBUG] idc       : {idascript.idc}")
    logger.info(f"[DEBUG] idcargs   : {idascript.idcargs}")
    logger.info(f"[DEBUG] pool_size: {idascript.pool_size}")
    logger.info(f"[DEBUG] force     : {idascript.force}")
    logger.info(f"[DEBUG] log       : {idascript.log}")
    logger.info(f"[DEBUG] stdout    : {idascript.stdout}")
    logger.info(f"[DEBUG] debug     : {idascript.debug}")
    print()
    logger.info(f"[DEBUG] input_list: {opts.input_list}")

    if opts.preflight:
        inputs = idascript.get_elf_files(opts.input_list)
        pending = next((path for path in inputs if not idascript.is_done(path)), None)
        if pending is not None:
            logger.info("[PREFLIGHT] probing IDA with %s", pending)
            path, succeeded = idascript.run_helper(pending)
            if succeeded is not True:
                logger.error(
                    "[PREFLIGHT] IDA probe failed; the worker pool was not started"
                )
                if opts.failed_list:
                    with open(opts.failed_list, "w") as failed_file:
                        failed_file.write(path + "\n")
                sys.exit(1)
            logger.info("[PREFLIGHT] IDA probe succeeded")
        else:
            logger.info("[PREFLIGHT] all inputs already have .done markers")

    results = idascript.run(opts.input_list)
    failed = [path for path, succeeded in results if succeeded is not True]
    if failed:
        logger.error("IDA failed for %d input(s)", len(failed))
        if opts.failed_list:
            with open(opts.failed_list, "w") as failed_file:
                failed_file.write("\n".join(failed) + "\n")
            logger.error("Failure list written to %s", opts.failed_list)
        sys.exit(1)
