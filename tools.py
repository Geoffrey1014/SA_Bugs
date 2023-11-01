#!/usr/bin/python3

import argparse
import os
import re
import subprocess
import time

from config import *
from myutils import *

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = ROOT_DIR + "/config.py"
MYUTILS_FILE = ROOT_DIR + "/myutils.py"

REACHABLE_DIR = "reachable"


def fuzz_fp(args: argparse.Namespace):
    script_path = ROOT_DIR + "/fuzz_sa_fp.py"
    fuzzing_par_dir = args.path
    opt = args.optimize
    analyzer = args.analyzer
    thread_num = args.thread
    iter_times = args.num

    fuzzing_working_dir = create_fuzzing_place(
        fuzzing_par_dir, script_path, analyzer, str(opt), thread_num)
    os.chdir(fuzzing_working_dir)

    for i in range(thread_num):
        os.chdir(f"fuzz_{i}")
        subprocess.Popen(
            ["python3", "fuzz_sa_fp.py", analyzer,
                args.checker, str(iter_times), f"-o={opt}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        os.chdir("..")


def fuzz_fn(args: argparse.Namespace):
    script_path = ROOT_DIR + "/fuzz_sa_fn.py"
    fuzzing_par_dir = args.path
    analyzer = args.analyzer
    opt = args.optimize
    thread_num = args.thread
    iter_times = args.num

    fuzzing_working_dir = create_fuzzing_place(
        fuzzing_par_dir, script_path, analyzer, str(opt), thread_num)
    os.chdir(fuzzing_working_dir)

    for i in range(thread_num):
        os.chdir(f"fuzz_{i}")
        subprocess.Popen(
            ["python3", "fuzz_sa_fn.py", analyzer,
                args.checker, f"-o={opt}", str(iter_times)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        os.chdir("..")


def fuzz_eval(args: argparse.Namespace):
    script_path = ROOT_DIR + "/fuzz_sa_eval.py"
    fuzzing_par_dir = args.path
    analyzer = args.analyzer
    opt = args.optimize
    thread_num = args.thread
    iter_times = args.num

    fuzzing_working_dir = create_fuzzing_place(
        fuzzing_par_dir, script_path, analyzer, str(opt), thread_num)
    os.chdir(fuzzing_working_dir)

    for i in range(thread_num):
        os.chdir(f"fuzz_{i}")
        subprocess.Popen(
            ["python3", "fuzz_sa_eval.py", analyzer,
                f"-o={opt}", str(iter_times)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        os.chdir("..")


def create(args: argparse.Namespace):
    fuzzing_par_dir = args.path
    analyzer = args.analyzer
    num = args.num
    script_path = args.script

    create_fuzzing_place(fuzzing_par_dir, script_path, analyzer, "not", num)


def create_fuzzing_place(fuzzing_par_dir, script_path, analyzer, opt_level, dir_num):
    """
    Create $dir_num directories in fuzzing_par_dir
    and copy script_path to those dirs.
    """
    abs_par_path = os.path.abspath(fuzzing_par_dir)

    if not os.path.exists(script_path) or not os.path.isfile(script_path):
        print(f"{script_path} does not exist or is not a file")
        exit(-1)

    abs_script_path = os.path.abspath(script_path)
    time_now = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())

    if analyzer == "gcc":
        cc = GCC
    elif analyzer == "clang":
        cc = CLANG

    try:
        ret = subprocess.run(
            [cc, "-dumpversion"],
            stderr=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            encoding="utf-8",
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        exit(1)

    abs_working_path = os.path.join(
        abs_par_path,
        f"{analyzer}_{ret.stdout.strip()}_O{opt_level}_{time_now}"
    )

    if not os.path.exists(abs_working_path):
        os.makedirs(abs_working_path)

    for i in range(dir_num):
        fuzz_i = os.path.join(abs_working_path, f"fuzz_{i}")

        if os.path.exists(fuzz_i):
            subprocess.run(["rm", "-rf", fuzz_i])

        os.mkdir(fuzz_i)

        subprocess.run(
            ["cp", abs_script_path, CONFIG_FILE, MYUTILS_FILE, fuzz_i])
        subprocess.run(["chmod", "+x", os.path.join(fuzz_i,
                       os.path.basename(abs_script_path))])

    return abs_working_path


def check_reachable(args: argparse.Namespace):
    if args.cfile and os.path.exists(args.cfile):
        print(args.cfile)

        if check_cfile_warning_line_reachable(args):
            print("warning line reachable")
        else:
            print("warning line not reachable")

    elif args.dir and os.path.exists(args.dir):
        cc, warning_type, opt, saveOutput, rmNonReachable, rmAllReachable, verbose = (
            get_compiler(args.analyzer),
            args.checker,
            str(args.optimize),
            args.saveOutput,
            args.rmNonReachable,
            args.rmAllReachable,
            args.verbose
        )

        if verbose:
            print("analyzer: " + cc)
            version = get_analyzer_version(cc)
            print("version: \n" + version)

        target_dir_abspath = os.path.abspath(args.dir)
        par_dir, dir_name = os.path.split(target_dir_abspath)

        if dir_name.startswith("fuzz"):
            check_dir_warning_line_reachable(
                cc, args.analyzer, warning_type, target_dir_abspath, opt, saveOutput, rmNonReachable, rmAllReachable, verbose
            )
        else:
            files = os.listdir(target_dir_abspath)

            for file in files:
                print(file)
                os.chdir(target_dir_abspath)

                if os.path.isdir(file) and file.startswith("fuzz"):
                    check_dir_warning_line_reachable(
                        cc, args.analyzer, warning_type, os.path.abspath(
                            file), opt, saveOutput, rmNonReachable, rmAllReachable, verbose
                    )

    else:
        print("please make sure the given file/dir exist")
        exit(-1)


def check_cfile_warning_line_reachable(args: argparse.Namespace):
    cc = get_compiler(args.analyzer)

    if args.verbose:
        print(f"analyzer: {cc}")
        version = get_analyzer_version(cc)
        print(f"version: \n{version}")

    cfile_abspath = os.path.abspath(args.cfile)
    par_dir, cfile = os.path.split(cfile_abspath)
    os.chdir(par_dir)

    short_name = get_short_name(cfile)
    report_file = f"{short_name}.txt"
    report_abspath = os.path.join(par_dir, report_file)

    warning_exist = False
    instrumented_cfile = f"instrument_{short_name}.c"
    run_out_file = f"instrument_{short_name}.out"

    if not os.path.exists(report_abspath):
        # TODO: analyze the cfile and get the report
        print("report file does not exist")
        exit(-1)
    else:
        warning_lines = get_warning_lines(
            args.analyzer, args.checker, report_abspath)

        if warning_lines:
            if instrument_cfile(cfile_abspath, warning_lines, instrumented_cfile):
                if compile_and_run_instrument_cfile(cc, str(args.optimize), instrumented_cfile, run_out_file):
                    warning_exist = grep_flag(run_out_file)
                else:
                    print("compile_and_run_instrument_cfile fail")

                clean_check_reach_output(
                    args.saveOutput, instrumented_cfile, run_out_file, warning_exist)

        clean_check_reach_input(args.rmNonReachable, args.rmAllReachable,
                                cfile_abspath, report_abspath, warning_exist)

        return warning_exist


def check_dir_warning_line_reachable(cc, analyzer, warning_type, target_dir_abspath, opt, saveOutput, rmNonReachable, rmAllReachable, verbose):
    os.chdir(target_dir_abspath)
    files = os.listdir(target_dir_abspath)

    if verbose:
        print(f"handling dir: {target_dir_abspath}")
        print(f"file nums: {len(files)}")

    if not os.path.exists(REACHABLE_DIR):
        os.mkdir(REACHABLE_DIR)
    os.chdir(REACHABLE_DIR)

    res_report_not_exist = []
    res_compile_or_run_fail = []
    res_reachable = []
    res_not_reachable = []

    for file in files:
        if file.endswith(".c") and file.startswith(warning_type):
            if verbose:
                print(f"handling file: {file}")

            warning_exist = False
            cfile = file
            cfile_abspath = os.path.join(target_dir_abspath, file)
            short_name = get_short_name(cfile)
            report_file = short_name + ".txt"
            report_abspath = os.path.join(target_dir_abspath, report_file)
            instrumented_cfile = "instrument_" + short_name + ".c"
            run_out_file = "instrument_" + short_name + ".out"

            if os.path.exists(instrumented_cfile):
                continue

            if not os.path.exists(report_abspath):
                if verbose:
                    print("report file does not exist!")
                res_report_not_exist.append(cfile_abspath)
            else:
                warning_lines = get_warning_lines(
                    analyzer, warning_type, report_abspath)

                if warning_lines:
                    if instrument_cfile(cfile_abspath, warning_lines, instrumented_cfile):
                        if compile_and_run_instrument_cfile(cc, opt, instrumented_cfile, run_out_file):
                            warning_exist = grep_flag(run_out_file)
                            if warning_exist:
                                res_reachable.append(cfile_abspath)
                            else:
                                res_not_reachable.append(cfile_abspath)
                        else:
                            res_compile_or_run_fail.append(cfile_abspath)
                        clean_check_reach_output(
                            saveOutput, instrumented_cfile, run_out_file, warning_exist)

            clean_check_reach_input(
                rmNonReachable, rmAllReachable, cfile_abspath, report_abspath, warning_exist)

    write_result_to_file(res_reachable, res_not_reachable, res_report_not_exist,
                         res_compile_or_run_fail, analyzer, warning_type)


def gen_reduce(args: argparse.Namespace):
    template_abspath = os.path.abspath(args.template)

    if not os.path.exists(template_abspath):
        print("template_abspath does not exist: " + template_abspath)
        exit(-1)

    analyzer = args.analyzer
    opt_level = str(args.optimize)

    if args.cfile:
        cfile_abspath = os.path.abspath(args.cfile)

        if not os.path.exists(cfile_abspath):
            print("cfile_path does not exist: " + cfile_abspath)
            exit(-1)

        par_dir, _ = os.path.split(cfile_abspath)
        os.chdir(par_dir)

        reduce_script = gen_reduce_script(
            template_abspath, get_short_name(
                cfile_abspath), opt_level, args.checker
        )

        if not reduce_script:
            print("gen_reduce_script fail")
            exit(-1)

    elif args.dir:
        target_dir_abspath = os.path.abspath(args.dir)

        if not os.path.exists(target_dir_abspath):
            print("dir_path does not exist: " + target_dir_abspath)
            exit(-1)

        print(target_dir_abspath)
        os.chdir(target_dir_abspath)
        par_dir, cur_dir = os.path.split(target_dir_abspath)

        if cur_dir == "reachable":
            files = os.listdir(target_dir_abspath)
            print("file nums: " + str(len(files)))

            for file in files:
                if file.endswith(".c") and file.startswith("instrument"):
                    reduce_script = gen_reduce_script(
                        template_abspath, get_short_name(
                            file), opt_level, args.checker
                    )
                    if not reduce_script:
                        print("gen_reduce_script fail")

        else:
            g = os.walk(target_dir_abspath)

            for path, dir_list, file_list in g:
                for dir_name in dir_list:
                    if dir_name == "reachable":
                        reachable_dir = os.path.join(path, dir_name)
                        print(reachable_dir)
                        os.chdir(reachable_dir)
                        files = os.listdir(reachable_dir)

                        for file in files:
                            if file.endswith(".c") and file.startswith("instrument"):
                                print(file)
                                reduce_script = gen_reduce_script(
                                    template_abspath, get_short_name(
                                        file), opt_level, args.checker
                                )
                                if not reduce_script:
                                    print("gen_reduce_script fail")

        print("gen reduce script done")

    else:
        print("please give a cfile or a dir")
        exit(-1)


def run_reduce_eval(args: argparse.Namespace):
    analyzer = args.analyzer
    opt = str(args.opt)
    thread_num = str(args.thread)

    if args.file:
        file = args.file
        if file.startswith("reduce_eval"):
            print(file)
            serial_num = re.search(r"reduce_eval_(\w+)\..*", file).group(1)
            ret = subprocess.run(
                ["./" + file, f"eval_{serial_num}.c", "--n", thread_num],
                stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL
            )

        return

    if args.dir:
        targer_dir_abspath = os.path.abspath(args.dir)
        if not os.path.exists(targer_dir_abspath):
            print(f"dir_abspath does not exist: {targer_dir_abspath}")
            exit(-1)

        print(targer_dir_abspath)
        os.chdir(targer_dir_abspath)

        reduced_list = []
        not_reduced_list = {}

        if not os.path.exists("reduce"):
            subprocess.run(["mkdir", "reduce"],
                           stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

        files = os.listdir(targer_dir_abspath)
        print(f"file num: {len(files)}")

        for file in files:
            if file.startswith("reduce_eval"):
                print(file)
                rfile = file
                serial_num = re.search(r"reduce_eval_(\w+)\..*", file).group(1)
                cfile = f"eval_{serial_num}.c"

                ret = subprocess.run(
                    ["./" + rfile, cfile, "--n", thread_num],
                    stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL
                )

                if ret.returncode != 0:

                    not_reduced_list[os.path.abspath(rfile)] = ret.returncode
                    ret = subprocess.run(
                        f"rm instrument_eval_{serial_num}.c instrument_p_eval_{serial_num}.c instrument_eval_{serial_num}.log eval_{serial_num}.c reduce_eval_{serial_num}.py",
                        shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE
                    )
                    continue

                ret = subprocess.run(
                    ["creduce", rfile,
                        f"eval_{serial_num}.c", "--n", thread_num],
                    stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL
                )
                reduced_list.append(os.path.abspath(cfile))

                ret = subprocess.run(
                    f"/home/working-space/build-llvm-main/bin/tooling-sample {analyzer} eval_{serial_num}.c -- -I /usr/include/csmith/ > instrument_eval_{serial_num}.c",
                    shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE
                )

                if analyzer == "gcc":
                    ret = subprocess.run(
                        f"gcc -fanalyzer -O{opt} -I /usr/include/csmith/ instrument_eval_{serial_num}.c &> instrument_eval_{serial_num}.log",
                        shell=True
                    )

                elif analyzer == "clang":
                    pass

                ret = subprocess.run(
                    f"mv instrument_eval_{serial_num}.c instrument_eval_{serial_num}.log eval_{serial_num}.c reduce/",
                    shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE
                )

                subprocess.run(
                    f"rm -rf instrument_eval_{serial_num}.o", shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                subprocess.run(
                    f"rm -rf /tmp/instrument_eval_{serial_num}*", shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                subprocess.run("rm -rf /tmp/compcert*", shell=True,
                               stderr=subprocess.PIPE, stdout=subprocess.PIPE)

        os.chdir("reduce")
        reduced_list.sort()

        with open(f"reduce_result-{str(time.strftime('%Y-%m-%d-%H-%M', time.localtime()))}.txt", "w") as f:
            f.write("\nreduced files:\n")
            for i in reduced_list:
                f.write(i + "\n")

            f.write("\n\nnot reduced files:\n")
            for i in not_reduced_list:
                f.write(f"{i}: {str(not_reduced_list[i])}\n")


def run_reduce(args: argparse.Namespace):
    """
    Run every reduce script in the given directory.
    If the intended reduce file has undefined behavior,
    then delete it, otherwise reduce it.
    """
    thread_num = str(args.thread)
    targer_dir_abspath = os.path.abspath(args.dir)

    if not os.path.exists(targer_dir_abspath):
        print("dir_abspath does not exist: " + targer_dir_abspath)
        exit(-1)

    # Handle directory path
    print(targer_dir_abspath)
    os.chdir(targer_dir_abspath)

    # Result list
    ub_list = []
    flag_disappear_list = []
    other_error_list = []
    reduce_list = []

    if not os.path.exists("reduce"):
        os.mkdir("reduce")

    files = os.listdir(targer_dir_abspath)
    print("file num: " + str(len(files)))

    for cfile in files:
        if cfile.endswith(".c") and cfile.startswith("instrument"):
            print(cfile)
            short_name = get_short_name(cfile)
            reduce_script = f"reduce_{short_name}.py"

            # If the reduce script does not return 0, then this cfile is useless
            res = subprocess.run(["./" + reduce_script], stderr=subprocess.DEVNULL,
                                 stdout=subprocess.PIPE, encoding="utf-8")

            # If the intended reduce file has undefined behavior, then delete it
            if UB_STR in res.stdout:
                print(UB_STR)
                ub_list.append(os.path.abspath(reduce_script))
                os.system(f"rm -rf {cfile} {reduce_script} {short_name}.o")
                continue
            elif FLAG_DIS_STR in res.stdout:
                print(FLAG_DIS_STR)
                flag_disappear_list.append(os.path.abspath(reduce_script))
                os.system(f"rm -rf {cfile} {reduce_script} {short_name}.o")
                continue
            elif res.returncode != 0:
                print(res.stdout)
                other_error_list.append(os.path.abspath(reduce_script))
                os.system(f"rm -rf {cfile} {reduce_script} {short_name}.o")
                continue

            ret = subprocess.run(
                ["creduce", reduce_script, cfile, "--n", thread_num],
                stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

            if ret.returncode == 0:
                reduce_list.append(os.path.abspath(cfile))
                os.system(
                    f"mv {cfile} {reduce_script} {short_name}.out reduce/")
                os.remove(f"{short_name}.o")

            subprocess.run(f"rm -rf /tmp/{short_name}*", shell=True,
                           stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            subprocess.run("rm -rf /tmp/compcert*", shell=True,
                           stderr=subprocess.PIPE, stdout=subprocess.PIPE)

    os.chdir("reduce")
    ub_list.sort()
    reduce_list.sort()
    wirte_reduce_result(reduce_list, ub_list,
                        flag_disappear_list, other_error_list)


def do_preprocess(abs_file_path, analyzer):
    subprocess.run(
        "%s %s -- -I %s " % (CFE, abs_file_path, CSMITH_HEADER),
        stderr=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        shell=True,
        check=True
    )

    new_lines = []
    with open(abs_file_path, "r") as f:
        lines = f.readlines()

        if analyzer == "gcc":
            new_lines.extend([
                "#include <stdbool.h>\n",
                "void __analyzer_eval(int a){}\n"
            ])
        elif analyzer == "clang":
            new_lines.extend([
                "#include <stdbool.h>\n",
                "void clang_analyzer_eval(int a){}\n"
            ])

        new_lines.extend(lines)

    with open(abs_file_path, "w") as f:
        f.writelines(new_lines)

    short_name = get_short_name(abs_file_path)
    pat_path, _ = os.path.split(abs_file_path)

    cmd_format = (
        "%s --analyzer=%s %s -- -I %s > %s" % (
            INSTRUMENT_TOOL,
            analyzer,
            abs_file_path,
            CSMITH_HEADER,
            os.path.join(pat_path, "instru_" + short_name + ".c")
        )
    )

    subprocess.run(
        cmd_format,
        stderr=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        shell=True,
        check=True
    )


def preprocess(args: argparse.Namespace):
    """
    Add include head to Csmith-generated program.
    """
    if args.file:
        print(args.file)
        abs_file_path = os.path.abspath(args.file)
        do_preprocess(abs_file_path, args.analyzer)
    elif args.dir:
        print(args.dir)


def handle_args():
    parser = argparse.ArgumentParser(
        description="some tools for testing static analyzer")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true")
    group.add_argument("-q", "--quiet", action="store_true")
    subparsers = parser.add_subparsers(help="sub-command help")

    # add subcommand preprocess
    parser_preprocess = subparsers.add_parser(
        "preprocess", help="preprocess a program")
    parser_preprocess.add_argument("analyzer", type=str, choices={
        "gcc", "clang"}, help="give a analyzer")
    group_preprocess = parser_preprocess.add_mutually_exclusive_group()
    group_preprocess.add_argument("-f", "--file", type=str, help="target file")
    group_preprocess.add_argument(
        "-d", "--dir", type=str, help="give a directory")
    parser_preprocess.set_defaults(func=preprocess)

    # add subcommand gen-reduce
    parser_gen_reduce = subparsers.add_parser(
        "gen-reduce", help="generate reduce script")
    parser_gen_reduce.add_argument(
        "template", type=str, help="specify reduce template")
    parser_gen_reduce.add_argument("analyzer", type=str, choices={
        "gcc", "clang", "pinpoint"}, help="give a analyzer")
    parser_gen_reduce.add_argument(
        "checker", type=str, choices=CHECKER_LIST, help="give a checker")
    parser_gen_reduce.add_argument("optimize", type=int, choices={
                                   0, 1, 2, 3}, help="optimization level")
    group_parser_gen_reduce = parser_gen_reduce.add_mutually_exclusive_group()
    group_parser_gen_reduce.add_argument(
        "-f", "--cfile", type=str, help="specify cfile")
    group_parser_gen_reduce.add_argument(
        "-d", "--dir", type=str, help="give a directory")
    parser_gen_reduce.set_defaults(func=gen_reduce)

    # add subcommand run-reduce
    parser_run_reduce = subparsers.add_parser(
        "run-reduce", help="run reduce script")
    parser_run_reduce.add_argument("dir", type=str, help="give a directory")
    parser_run_reduce.add_argument(
        "thread", type=int, default=0, help="specify thread nums for reducing")
    parser_run_reduce.set_defaults(func=run_reduce)

    # add subcommand run-reduce-eval
    parser_run_reduce_eval = subparsers.add_parser(
        "run-reduce-eval", help="run reduce-eval script")
    parser_run_reduce_eval.add_argument(
        "-d", "--dir", type=str, help="give a directory")
    parser_run_reduce_eval.add_argument(
        "-f", "--file", type=str, help="give a file")
    parser_run_reduce_eval.add_argument(
        "thread", type=int, default=0, help="specify thread nums for reducing")
    parser_run_reduce_eval.add_argument("analyzer", type=str, choices={
        "gcc", "clang"}, help="give a analyzer")
    parser_run_reduce_eval.add_argument("opt", type=int, choices={
        0, 1, 2, 3}, help="optimization level")
    parser_run_reduce_eval.set_defaults(func=run_reduce_eval)

    # add subcommand fuzz-fp
    parser_fuzz_fp = subparsers.add_parser(
        "fuzz-fp", help="fuzzing static analyzer in a given dir")
    parser_fuzz_fp.add_argument(
        "path", help="given a parent dir of fuzzing working dir")
    parser_fuzz_fp.add_argument("analyzer", type=str, choices={
        "gcc", "clang", "pinpoint"}, help="give a analyzer")
    parser_fuzz_fp.add_argument(
        "checker", type=str, choices=CHECKER_LIST, help="give a checker")
    parser_fuzz_fp.add_argument("optimize", type=int, choices={
        0, 1, 2, 3}, default=0, help="optimization level")
    parser_fuzz_fp.add_argument(
        "thread", type=int, default=1, help="specify thread nums for fuzzing")
    parser_fuzz_fp.add_argument(
        "num", type=int, default=1, help="specify iteration times of fuzzing")
    parser_fuzz_fp.set_defaults(func=fuzz_fp)

    # add subcommand fuzz-fn
    parser_fuzz_fn = subparsers.add_parser(
        "fuzz-fn", help="fuzzing static analyzer in a given dir")
    parser_fuzz_fn.add_argument(
        "path", help="given a parent dir of fuzzing working dir")
    parser_fuzz_fn.add_argument("analyzer", type=str, choices={
        "gcc", "clang"}, help="give a analyzer")
    parser_fuzz_fn.add_argument(
        "checker", type=str, choices=CHECKER_LIST, help="give a checker")
    parser_fuzz_fn.add_argument("optimize", type=int, choices={
        0, 1, 2, 3}, default=0, help="optimization level")
    parser_fuzz_fn.add_argument(
        "thread", type=int, default=1, help="specify thread nums for fuzzing")
    parser_fuzz_fn.add_argument(
        "num", type=int, default=1, help="specify iteration times of fuzzing")
    parser_fuzz_fn.set_defaults(func=fuzz_fn)

    # add subcommand fuzz-eval
    parser_fuzz_eval = subparsers.add_parser(
        "fuzz-eval", help="fuzzing static analyzer in a given dir")
    parser_fuzz_eval.add_argument(
        "path", help="given a parent dir of fuzzing working dir")
    parser_fuzz_eval.add_argument("analyzer", type=str, choices={
        "gcc", "clang"}, help="give a analyzer")
    parser_fuzz_eval.add_argument("optimize", type=int, choices={
        0, 1, 2, 3}, default=0, help="optimization level")
    parser_fuzz_eval.add_argument(
        "thread", type=int, default=1, help="specify thread nums for fuzzing")
    parser_fuzz_eval.add_argument(
        "num", type=int, default=1, help="specify iteration times of fuzzing")
    parser_fuzz_eval.set_defaults(func=fuzz_eval)

    # add subcommand create fuzzing working dir
    parser_create = subparsers.add_parser(
        "create", help="create fuzzing working dir")
    parser_create.add_argument("script", help="give a fuzzing script")
    parser_create.add_argument(
        "path", help="give a parent dir of fuzzing working dir")
    parser_create.add_argument("analyzer", type=str, choices={
                               "gcc", "clang", "pinpoint"}, help="give a analyzer")
    parser_create.add_argument(
        "-n", "--num", type=int, required=True, help="number of fuzzing")
    parser_create.set_defaults(func=create)

    # add subcommand check-reach
    parser_reach_warning_lines = subparsers.add_parser(
        "check-reach", help="check whether warning line complained by given analyzer is reachable")
    parser_reach_warning_lines.add_argument("analyzer", type=str, choices={
        "gcc", "clang", "pinpoint"}, help="give a analyzer")
    parser_reach_warning_lines.add_argument(
        "checker", type=str, choices=CHECKER_LIST, help="give a checker")
    parser_reach_warning_lines.add_argument("optimize", type=int, choices={
                                            0, 1, 2, 3}, default=0, help="optimization level")
    parser_reach_warning_lines.add_argument(
        "-s", "--saveOutput", action="store_true", help="do not delete generated files in checking process")
    group_rm_reach_warning_lines = parser_reach_warning_lines.add_mutually_exclusive_group()
    group_rm_reach_warning_lines.add_argument(
        "-mn", "--rmNonReachable", action="store_true", help="remove non-warning-line-reachable test c files")
    group_rm_reach_warning_lines.add_argument(
        "-ma", "--rmAllReachable", action="store_true", help="remove all-warning-line-reachable test c files")
    group_reach_warning_lines = parser_reach_warning_lines.add_mutually_exclusive_group()
    group_reach_warning_lines.add_argument(
        "-cf", "--cfile", type=str, help="give a cfile")
    group_reach_warning_lines.add_argument(
        "-d", "--dir", type=str, help="give a directory")
    parser_reach_warning_lines.set_defaults(func=check_reachable)

    args = parser.parse_args()
    return args


def main():
    args = handle_args()
    if args.verbose:
        print(args)
    args.func(args)


if __name__ == "__main__":
    main()
