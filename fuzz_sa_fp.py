#!/usr/bin/python3
import argparse
import os
import re
import signal
import subprocess
import sys
import time

#############
# user-configurable stuff
#############

# programs shorter than this many bytes are too boring to test
MIN_PROGRAM_SIZE = 8000
MAX_PROGRAM_SIZE = 8000

# kill Csmith after this many seconds
CSMITH_TIMEOUT = 90

# kill a compiler after this many seconds
COMPILER_TIMEOUT = 120

# kill a compiler's output after this many seconds
PROG_TIMEOUT = 8

# These options are more important and need to be singled out
CSMITH_USER_OPTIONS = " --no-global-variables --max-pointer-depth 2"
# CSMITH_USER_OPTIONS = " --no-global-variables --max-funcs 1 "
# CSMITH_USER_OPTIONS = " --no-global-variables --max-funcs 1 --no-safe-math"
# CSMITH_USER_OPTIONS = " --no-bitfields --packed-struct --no-global-variables --max-pointer-depth 2 "

# Command line options:
# ...

#############
# end user-configurable stuff
#############

CSMITH_HEADER = "/usr/include/csmith"

GCC_ANALYZER = "gcc -fanalyzer -fanalyzer-call-summaries -Wno-analyzer-double-fclose -Wno-analyzer-double-free -Wno-analyzer-exposure-through-output-file -Wno-analyzer-file-leak -Wno-analyzer-free-of-non-heap -Wno-analyzer-malloc-leak -Wno-analyzer-mismatching-deallocation -Wno-analyzer-null-argument -Wno-analyzer-possible-null-argument -Wno-analyzer-possible-null-dereference -Wno-analyzer-shift-count-negative -Wno-analyzer-shift-count-overflow -Wno-analyzer-stale-setjmp-buffer -Wno-analyzer-unsafe-call-within-signal-handler -Wno-analyzer-use-after-free -Wno-analyzer-use-of-pointer-in-stale-stack-frame -Wno-analyzer-use-of-uninitialized-value -Wno-analyzer-write-to-const -Wno-analyzer-write-to-string-literal -fdiagnostics-plain-output -fdiagnostics-format=text "

# CLANG_ANALYZER = " "

# CLANG_OPTIONS = " "

NPD_NUM = 0
TIMEOUT_NUM = 0
CRASH_NUM = 0
ANALYZER_TIMEOUT = "timeout 30 "


def read_value_from_file(file, match):
    '''
    extra the group(1) of searched pattern
    '''
    with open(file, 'r') as f:
        pattern = re.compile(r''+match)
        for line in f.readlines():
            seed = pattern.search(line)
            if seed:
                return seed.group(1)

    return ""


def save_crashing_file(num):
    '''
    save the cfile crashing analyzer
    '''
    global CRASH_NUM
    os.system("mv test_%s.c crash%s.c " % (num, NPD_NUM))
    os.system("mv test_%s.txt crash%s.txt " % (num, NPD_NUM))
    CRASH_NUM += 1


def analyze_with_gcc(num, optimization_level, args):
    '''
    use gcc to analyze Csmith-generated c program
    '''
    global TIMEOUT_NUM
    report_file = "test_%s.txt" % num
    cfile = "test_%s.c" % num

    ret = os.system(ANALYZER_TIMEOUT + GCC_ANALYZER + " -O" + optimization_level +
                    "  -msse4.2 -c -I " + CSMITH_HEADER + " " + cfile + " > " + report_file + " 2>&1")
    ret >>= 8
    print("gcc analyzer ret: " + str(ret))

    if ret == 124:
        TIMEOUT_NUM += 1
        print(ANALYZER_TIMEOUT)
        clean_gcc_products(num, args.saveProducts)
        return None
    elif ret != 0:
        # TODO: 该处的逻辑是否有问题？返回值既不是 0 也不是 124 一定是 analyzer crash 吗？
        save_crashing_file(num)
        clean_gcc_products(num, args.saveProducts)
        return None

    return report_file


# def analyze_with_clang(num, report_html, optimization_level, args):
#     '''
#     use clang to analyze Csmith-generated c program
#     '''
#     global TIMEOUT_NUM
#     report_file = "test_%s.txt" % num
#     cfile = "test_%s.c" % num

#     ret = os.system(ANALYZER_TIMEOUT + CLANG_ANALYZER + " -o " + report_html + " clang " + CLANG_OPTIONS +
#                     " -0" + optimization_level + " -msse4.2 -c -I " + CSMITH_HEADER + " " + cfile + " > " + report_file + " 2>&1")
#     ret >>= 8
#     print("clang ret: " + str(ret))

#     if ret == 124:
#         TIMEOUT_NUM += 1
#         print(ANALYZER_TIMEOUT)
#         clean_clang_products(num, report_html, args.saveProducts)
#         return None
#     elif ret != 0:
#         # TODO: 该处的逻辑是否有问题？返回值既不是 0 也不是 124 一定是 analyzer crash 吗？
#         save_crashing_file(num)
#         clean_clang_products(num, report_html, args.saveProducts)
#         return None

#     return report_file


# def process_clang_report(num, report_file, report_html, args):
#     '''
#     check whether the given report contains the target CWE(NPD)
#     '''
#     global NPD_NUM
#     save_products_flag = args.saveProducts

#     if not os.path.exists(report_file):
#         print("report does not exist: " + str(report_file))
#         clean_clang_products(num, report_html, save_products_flag)
#         return

#     check_cmd = 'grep "\[core\.NullDereference\]"'
#     ret = os.system(check_cmd + " < " + report_file)
#     ret >> 8

#     if ret == 0:
#         os.system("mv test_%s.c npd%s.c " % (num, NPD_NUM))
#         os.system("mv test_%s.txt npd%s.txt " % (num, NPD_NUM))
#         NPD_NUM += 1

#     clean_clang_products(num, report_html, save_products_flag)


# def clean_clang_products(num, report_html, save_products_flag):
#     if not save_products_flag:
#         os.system("rm -f test_%s*" % num)
#         ret = os.system("rm -rf %s/*" % report_html)
#         # print("clean ret: %s" % (ret >> 8))


def process_gcc_report(num, report_file, args):
    '''
    check whether the given report contains the target CWE (NPD)
    '''
    global NPD_NUM
    save_products_flag = args.saveProducts

    if not os.path.exists(report_file):
        print("report does not exist: " + str(report_file))
        clean_gcc_products(num, save_products_flag)
        return

    # TODO: 进一步优化
    check_cmd = 'grep "\[CWE\-476\]"'
    ret = os.system(check_cmd + " < " + report_file)
    ret >>= 8

    if ret == 0:
        os.system("mv test*.c npd%s.c " % (NPD_NUM))
        os.system("mv test*.txt npd%s.txt " % (NPD_NUM))
        NPD_NUM += 1

    clean_gcc_products(num, save_products_flag)


def clean_gcc_products(num, save_products_flag):
    if not save_products_flag:
        os.system("rm -f test_%s*" % num)


def generate_code(num, ctrl_max):
    '''
    generate wanted-size code with csmith
    '''
    cfile = "test_%s.c" % num
    os.system("rm -f %s" % cfile)

    while True:
        cmd = "csmith %s --output %s" % (CSMITH_USER_OPTIONS, cfile)
        os.system(cmd)
        file_size = os.stat(cfile).st_size
        seed = read_value_from_file(cfile, 'Seed:\s+(\d+)')
        # print("generated a file, Seed: " + seed)

        if len(seed) <= 0:
            print("Random program %s has no seed information!\n" % cfile)
            sys.exit()

        if ctrl_max:
            if file_size < MAX_PROGRAM_SIZE:
                print("succ generated a file whose size is no more than %s, seed %s: " % (
                    MAX_PROGRAM_SIZE, seed))
                break
        else:
            if file_size > MIN_PROGRAM_SIZE:
                print("succ generated a file whose size is no more than %s, seed %s: " % (
                    MIN_PROGRAM_SIZE, seed))
                break

    print(cfile + ' ' + seed)
    return cfile


def gcc_test_one(num, args):
    cfile = generate_code(num, args.max)
    report_file = analyze_with_gcc(num, str(args.optimize), args)

    if report_file is not None:
        process_gcc_report(num, report_file, args)


# def clang_test_one(num, report_html, args):
#     cfile = generate_code(num, args.max)
#     report_file = analyze_with_clang(
#         num, report_html, str(args.optimize), args)

#     if report_file is not None:
#         process_clang_report(num, report_file, report_html, args)


def get_analyzer_version(analyzer):
    res = subprocess.run([analyzer, "-v"], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, encoding='utf-8')

    return res.stderr


def write_script_run_args(args):
    '''
    write doen script running args
    '''
    with open('script_run_args.info', 'w') as f:
        f.write("Time: %s\n" % str(time.strftime(
            "%Y-%m-%d %H:%M:%S %a", time.localtime())))
        f.write("\nTimeout: %s\n" % ANALYZER_TIMEOUT)
        f.write("\nCsmit options: \n" + CSMITH_USER_OPTIONS)
        f.write("\n\nargs:\n" + str(args))
        f.write("\n\nanalyzer info:\n" + get_analyzer_version(args.compiler))
        # if args.compiler == "clang":
        #     f.write("\n\nanalyzer options:\n" + CLANG_OPTIONS)


def write_fuzzing_result(stop_message):
    '''
    write down short statistic of fuzzing
    '''
    with open('fuzzing_result.txt', 'w') as f:
        f.write("STOP: %s\n" % stop_message)
        f.write("NPD_NUM: %s\n" % NPD_NUM)
        f.write("\nTIMEOUT_NUM: %s\n" % TIMEOUT_NUM)
        f.write("\nCRASH_NUM: %s\n" % CRASH_NUM)


def handle_args():
    parser = argparse.ArgumentParser(
        description="fuzz static analyzer with csmith-generated c program")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true")
    group.add_argument("-q", "--quiet", action="store_true")
    parser.add_argument('compiler', type=str, help='choose a compiler')
    parser.add_argument("-o", '--optimize', type=int,
                        choices={0, 1, 2, 3}, default=0, help='choose an optimize level')
    parser.add_argument('num', type=int, help='number of generated c programs')
    parser.add_argument("-m", "--max", action="store_true",
                        help="set the size of generated c programs is no more than %s" % MAX_PROGRAM_SIZE)
    parser.add_argument("-s", "--saveProducts", action="store_true",
                        help="do not delete generated files in analyzing process")

    args = parser.parse_args()
    return args


def bye(signum, frame):
    '''
    responsible func of signal.SIGINT and signal.SIGTERM
    '''
    # print("Bye bye")
    write_fuzzing_result("Interrupted")
    exit(0)


def main():
    args = handle_args()
    print(args)
    write_script_run_args(args)
    target_analyzer = args.compiler
    num = args.num

    signal.signal(signal.SIGINT, bye)
    signal.signal(signal.SIGTERM, bye)
    # signal.signal(signal.SIGKILL, bye)

    if target_analyzer == "gcc":
        for i in range(int(num)):
            gcc_test_one(i, args)
    # elif target_analyzer == 'clang':
    #     if not os.path.exists("report_html"):
    #         ret = os.system("mkdir report_html")
    #         if ret != 0:
    #             print("fail to mkdir report_html")
    #             exit(ret >> 8)

    #     for i in range(int(num)):
    #         clang_test_one(i, "report_html", args)
    else:
        print("target analyzer: %s is not supported" % target_analyzer)

    write_fuzzing_result("Over")


if __name__ == "__main__":
    main()
