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
# MAX_PROGRAM_SIZE = 8000

# kill Csmith after this many seconds
CSMITH_TIMEOUT = 90

# kill a compiler after this many seconds
COMPILER_TIMEOUT = 120

# kill a compiler's output after this many seconds
PROG_TIMEOUT = 8

# These options are more important and need to be singled out
CSMITH_USER_OPTIONS = "--no-global-variables --no-safe-math --max-pointer-depth 2"
# CSMITH_USER_OPTIONS = " --no-global-variables --max-funcs 1 "
# CSMITH_USER_OPTIONS = " --no-global-variables --max-funcs 1 --no-safe-math"
# CSMITH_USER_OPTIONS = " --no-bitfields --packed-struct --no-global-variables --max-pointer-depth 2 "

# Command line options:
# ...

#############
# end user-configurable stuff
#############

CSMITH_HEADER = "/usr/include/csmith"

GCC_ANALYZER = "gcc -fanalyzer -fanalyzer-call-summaries -Wanalyzer-too-complex -fdiagnostics-format=text "

# CLANG_ANALYZER = "clang --analyze -Xclang -analyzer-stats -Xclang -setup-static-analyzer -Xclang -analyzer-config -Xclang eagerly-assume=false -Xclang -analyzer-checker=core,alpha.security.taint,debug.ExprInspection,debug.TaintTest"

CLANG_ANALYZER = "/usr/local/llvm-0407/bin/clang --analyze -Xclang -analyzer-stats -Xclang -setup-static-analyzer -Xclang -analyzer-config -Xclang eagerly-assume=false -Xclang -analyzer-checker=core,alpha.security.taint,debug.ExprInspection,debug.TaintTest -Xanalyzer -analyzer-config -Xanalyzer crosscheck-with-z3=true"

TOOLING_EVAL = "/home/working-space/build-llvm-main/bin/tooling-sample"
TOOLING_CFE = "/home/working-space/build-llvm-main/bin/cfe_preprocess"
# CLANG_OPTIONS = " "

CSMITH_ERROR = 0
EVAL_NUM = 0
TIMEOUT_NUM = 0
CRASH_NUM = 0
ANALYZER_TIMEOUT = "timeout 60 "


def read_value_from_file(file, match):
    '''
    extract the group(1) of searched pattern
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
    os.system("mv test_%s.c crash%s.c " % (num, CRASH_NUM))
    os.system("mv instrument_test_%s.c instrument_crash%s.c " % (num, CRASH_NUM))
    os.system("mv instrument_test_%s.log instrument_crash%s.log " % (num, CRASH_NUM))


def do_preprocess(file_path, analyzer):
    subprocess.run("%s %s -- -I %s "%(TOOLING_CFE, file_path, CSMITH_HEADER),
                               stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, shell=True, check=True)

    new_lines = []
    with open(file_path, "r") as f:
        lines = f.readlines()
        if analyzer == "gcc":
            new_lines.append("#include <stdbool.h>\n")
            new_lines.append("void __analyzer_eval(int a){}\n")
        elif analyzer == "clang":
            new_lines.append("#include <stdbool.h>\n")
            new_lines.append("void clang_analyzer_eval(int a){}\n")

        for line in lines:
            new_lines.append(line)
    with open(file_path, "w") as f:
        f.writelines(new_lines)   

    instrument_file = "instrument_" + file_path
    if analyzer == "gcc":
        subprocess.run("%s gcc %s -- -I %s > %s"%(TOOLING_EVAL, file_path, CSMITH_HEADER, instrument_file),
                               stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, shell=True , check=True )
    elif analyzer == "clang":
        subprocess.run("%s clang %s -- -I %s > %s"%(TOOLING_EVAL, file_path, CSMITH_HEADER, instrument_file),
                               stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, shell=True , check=True )
    return instrument_file

# csmith --> test_0.c --> instrument_test_0.c -->instrument_test_0.log
def analyze_with_gcc(num, optimization_level, args):
    '''
    use gcc to analyze Csmith-generated c program
    '''
    global TIMEOUT_NUM
    global CRASH_NUM
    report_file = "instrument_test_%s.log" % num
    cfile = "test_%s.c" % num
    instrument_cfile = do_preprocess(cfile, args.analyzer)

    ret = os.system(ANALYZER_TIMEOUT + GCC_ANALYZER + " -O" + optimization_level +
                    " -c -I " + CSMITH_HEADER + " " + instrument_cfile + " > " + report_file + " 2>&1")
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
        CRASH_NUM += 1
        return None

    return report_file


def process_gcc_report(num, report_file, args):
    '''
    check whether the given report contains the target error
    '''
    global EVAL_NUM
    save_products_flag = args.saveProducts

    if not os.path.exists(report_file):
        print("report does not exist: " + str(report_file))
        clean_gcc_products(num, save_products_flag)
        return

    check_cmd = 'grep "warning: FALSE"'
    ret = os.system(check_cmd + " < " + report_file)
    ret >>= 8

    if ret == 0:
        os.system("mv instrument_test_%s.c instrument_eval_%s.c " % (num, EVAL_NUM))
        os.system("mv test_%s.c eval_%s.c " % (num, EVAL_NUM))
        os.system("mv instrument_test_%s.log instrument_eval_%s.log " % (num, EVAL_NUM))
        EVAL_NUM += 1

    clean_gcc_products(num, save_products_flag)


def clean_gcc_products(num, save_products_flag):
    if not save_products_flag:
        os.system("rm -f instrument_test_%s* test_%s*" % (num, num))


def analyze_with_clang(num, optimization_level, args):
    '''
    use clang to analyze Csmith-generated c program
    '''
    global CRASH_NUM
    global TIMEOUT_NUM
    report_file = "instrument_test_%s.log" % num
    cfile = "test_%s.c" % num

    instrument_cfile = do_preprocess(cfile, args.analyzer)

    ret = os.system(ANALYZER_TIMEOUT + CLANG_ANALYZER + " -O" + optimization_level +
                    " -c -I " + CSMITH_HEADER + " " + instrument_cfile + " > " + report_file + " 2>&1")
    ret >>= 8
    print("clang ret: " + str(ret))

    if ret == 124:
        TIMEOUT_NUM += 1
        print(ANALYZER_TIMEOUT)
        clean_clang_products(num, args.saveProducts)
        return None
    elif ret != 0:
        # TODO: 该处的逻辑是否有问题？返回值既不是 0 也不是 124 一定是 analyzer crash 吗？
        save_crashing_file(num)
        clean_clang_products(num, args.saveProducts)
        return None

    return report_file


def process_clang_report(num, report_file, args):
    '''
    check whether the given report contains the target error
    '''
    global EVAL_NUM
    save_products_flag = args.saveProducts

    if not os.path.exists(report_file):
        print("report does not exist: " + str(report_file))
        clean_clang_products(num, save_products_flag)
        return

    check_cmd = 'grep "warning: FALSE"'
    ret = os.system(check_cmd + " < " + report_file)
    ret >> 8

    if ret == 0:
        os.system("mv instrument_test_%s.c instrument_eval_%s.c " % (num, EVAL_NUM))
        os.system("mv test_%s.c eval_%s.c " % (num, EVAL_NUM))
        os.system("mv instrument_test_%s.log instrument_eval_%s.log " % (num, EVAL_NUM))
        EVAL_NUM += 1

    clean_clang_products(num, save_products_flag)


def clean_clang_products(num, save_products_flag):
    if not save_products_flag:
        os.system("rm -f test_%s* instrument_test_%s*" % (num, num))
        



def generate_code(num, args):
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
            return None

        ctrl_max = args.max
        if ctrl_max:
            print("ctrl_max %d"%ctrl_max)
            if file_size < ctrl_max and file_size > MIN_PROGRAM_SIZE:
                print("succ generated a file whose size is larger than %s and smaller than %s, seed %s: " % (
                    MIN_PROGRAM_SIZE, ctrl_max, seed))
                break
        else:
            if file_size > MIN_PROGRAM_SIZE:
                print("succ generated a file whose size is larger than %s, seed %s: " % (
                    MIN_PROGRAM_SIZE, seed))
                break

    print(cfile + ' ' + seed)
    return cfile


def gcc_test_one(num, args):
    global CSMITH_ERROR
    cfile = generate_code(num, args)
    if cfile:
        report_file = analyze_with_gcc(num, str(args.optimize), args)
        if report_file is not None:
            process_gcc_report(num, report_file, args)
    else:
        CSMITH_ERROR += 1

    


def clang_test_one(num, args):
    global CSMITH_ERROR
    cfile = generate_code(num, args)
    if cfile:
        report_file = analyze_with_clang(num, str(args.optimize), args)
        if report_file is not None:
            process_clang_report(num, report_file, args)
    else:
        CSMITH_ERROR += 1

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
        f.write("\n\nanalyzer info:\n" + get_analyzer_version(args.analyzer))
        # if args.compiler == "clang":
        #     f.write("\n\nanalyzer options:\n" + CLANG_OPTIONS)


def write_fuzzing_result(stop_message):
    '''
    write down short statistic of fuzzing
    '''
    with open('fuzzing_result.txt', 'w') as f:
        f.write("STOP: %s\n" % stop_message)
        f.write("EVAL_NUM: %s\n" % EVAL_NUM)
        f.write("\nTIMEOUT_NUM: %s\n" % TIMEOUT_NUM)
        f.write("\nCRASH_NUM: %s\n" % CRASH_NUM)


def handle_args():
    parser = argparse.ArgumentParser(
        description="fuzz static analyzer with csmith-generated c program")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true")
    group.add_argument("-q", "--quiet", action="store_true")
    parser.add_argument('analyzer', type=str, help='choose a analyzer')
    parser.add_argument("-o", '--optimize', type=int,
                        choices={0, 1, 2, 3}, default=0, help='choose an optimize level')
    parser.add_argument('num', type=int, help='number of generated c programs')
    parser.add_argument("-m", "--max", type=int,
                        help="set the max size of generated c programs")
    parser.add_argument("--min", type=int, default=MIN_PROGRAM_SIZE,
                        help="set the min size of generated c programs is no more than %s" % MIN_PROGRAM_SIZE)
    parser.add_argument("-s", "--saveProducts", action="store_true",
                        help="do not delete generated files in analyzing process")

    args = parser.parse_args()

    if args.max and args.max <= args.min:
        sys.stderr.write("max size should larger than min size\n")
        exit(-1)
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
    target_analyzer = args.analyzer
    num = args.num

    signal.signal(signal.SIGINT, bye)
    signal.signal(signal.SIGTERM, bye)
    # signal.signal(signal.SIGKILL, bye)

    if target_analyzer == "gcc":
        for i in range(int(num)):
            gcc_test_one(i, args)
    elif target_analyzer == 'clang':
        
        for i in range(int(num)):
            clang_test_one(i, args)
    else:
        print("target analyzer: %s is not supported" % target_analyzer)

    write_fuzzing_result("Over")


if __name__ == "__main__":
    main()
