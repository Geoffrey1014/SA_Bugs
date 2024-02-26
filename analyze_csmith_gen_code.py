#!/usr/bin/python3
import argparse
import os,json
import signal
import time
from myutils import get_analyzer_version, generate_code
from config import *
from config import SEG_CMD, CHECK_CMD, CLANG_CMD, TRANS_CMD
CRASH_NUM = 0
NPD_NUM = 0
OOB_NUM = 0
DZ_NUM = 0
SCO_NUM = 0
UPOS_NUM = 0
TIMEOUT_NUM = 0


def analyze_with_gcc(num, optimization_level, args):
    '''
    use gcc to analyze csmith-generated c program
    '''
    global TIMEOUT_NUM, CRASH_NUM
    report_file = "test_%s.txt" % num
    cfile = "test_%s.c" % num

    ret = os.system(ANALYZER_TIMEOUT + GCC_ANALYZER + " -O" + optimization_level +
                    " -c -I " + CSMITH_HEADER + " " + cfile + " > " + report_file + " 2>&1")
    ret >>= 8
    if args.verbose:
        print("gcc static analyzer ret: " + str(ret))

    if ret == 124:
        TIMEOUT_NUM += 1
        print(ANALYZER_TIMEOUT)
        clean_analysis_products(num, args.saveProducts)
        return None
    elif ret == 1:
        # TODO: Is there a problem with the logic there?
        # I have seen a crash case, the return code is 1. But I am not sure what the other return codes (e.g. 2, 3) mean.
        CRASH_NUM += 1
        save_crashing_file(num)
        clean_analysis_products(num, args.saveProducts)
        return None

    return report_file


def analyze_with_clang(num, args):
    '''
    use clang to analyze csmith-generated c program
    '''
    global TIMEOUT_NUM, CRASH_NUM
    report_file = "test_%s.txt" % num
    cfile = "test_%s.c" % num

    ret = os.system(ANALYZER_TIMEOUT + CLANG_ANALYZER + " -c -I " + CSMITH_HEADER + " " + cfile + " > " + report_file + " 2>&1")
    ret >>= 8

    if args.verbose:
        print("clang static analyzer ret: " + str(ret))

    if ret == 124:
        TIMEOUT_NUM += 1
        print(ANALYZER_TIMEOUT)
        clean_analysis_products(num, args.saveProducts)
        return None
    elif ret == 1:
        # TODO: Is there a problem with the logic there?
        # I have seen a crash case, the return code is 1. But I am not sure what the other return codes (e.g. 2, 3) mean.
        save_crashing_file(num)
        clean_analysis_products(num, args.saveProducts)
        CRASH_NUM += 1
        return None
    

    return report_file



def clean_analysis_products(num, save_products_flag):
    if not save_products_flag:
        os.system("rm -f test_%s*" % num)


def save_crashing_file(num):
    '''
    save the cfile crashing analyzer
    '''
    global CRASH_NUM
    os.system("mv test_%s.c crash%s.c " % (num, NPD_NUM))
    os.system("mv test_%s.txt crash%s.txt " % (num, NPD_NUM))
    CRASH_NUM += 1

    
def gcc_test_one(num, args):
    cfile = generate_code(num, CSMITH_USER_OPTIONS, args.max)
    report_file = analyze_with_gcc(num, str(args.optimize), args)
        


def clang_test_one(num, args):
    cfile = generate_code(num, CSMITH_USER_OPTIONS, args.max)
    report_file = analyze_with_clang(num, args)



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
        if args.compiler == "clang":
            f.write("\n\nanalyzer:\n" + CLANG_ANALYZER)
            f.write("\n\nanalyzer info:\n" + get_analyzer_version(CLANG))
        elif args.compiler == "gcc":
            f.write("\n\nanalyzer:\n" + GCC_ANALYZER)
            f.write("\n\nanalyzer info:\n" + get_analyzer_version(GCC))


def handle_args():
    parser = argparse.ArgumentParser(
        description="fuzz static analyzer with csmith-generated c program")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", default= False,action="store_true")
    group.add_argument("-q", "--quiet", default=True, action="store_true")
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
    print("bye bye ~")
    write_fuzzing_result("","interrupted!")
    exit(0)


def main():
    args = handle_args()
    if args.verbose:
        print(args)
    write_script_run_args(args)
    target_analyzer = args.compiler
    num = args.num

    signal.signal(signal.SIGINT, bye)
    signal.signal(signal.SIGTERM, bye)



    if target_analyzer == "gcc":
        for i in range(int(num)):
            gcc_test_one(i, args)
    elif target_analyzer == 'clang':
        for i in range(int(num)):
            clang_test_one(i, args)
    else:
        print("target analyzer: %s is not supported!" % target_analyzer)
        exit(0)



if __name__ == "__main__":
    main()
