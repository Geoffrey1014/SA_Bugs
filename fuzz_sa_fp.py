#!/usr/bin/python3
import argparse
import os,json
import signal
import time,shlex, subprocess
from myutils import get_analyzer_version, generate_code, get_warning_line_from_report
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
    cfile = "test_%s.c" % num
    
    analyzer_args_split = shlex.split(GCC_ANALYZER)

    analyzer_ret = subprocess.run( [ANALYZER_TIMEOUT] + analyzer_args_split + ['-O' + optimization_level, '-c', '-I', CSMITH_HEADER, cfile], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')

    if args.verbose:
        print("gcc static analyzer ret: " + str(analyzer_ret.stderr))

    if analyzer_ret.returncode == 124:
        TIMEOUT_NUM += 1
        print(ANALYZER_TIMEOUT)
        clean_analysis_products(num, args.saveProducts)
        return None
    elif analyzer_ret.returncode == 1:
        # TODO: Is there a problem with the logic there?
        # I have seen a crash case, the return code is 1. But I am not sure what the other return codes (e.g. 2, 3) mean.
        CRASH_NUM += 1
        save_crashing_file(num)
        clean_analysis_products(num, args.saveProducts)
        return None

    return analyzer_ret.stderr


def analyze_with_clang(num, args):
    '''
    use clang to analyze csmith-generated c program
    '''
    global TIMEOUT_NUM, CRASH_NUM
    cfile = "test_%s.c" % num

    analyzer_args_split = shlex.split(ANALYZER_TIMEOUT) + shlex.split(CLANG_ANALYZER)

    analyzer_ret = subprocess.run(  analyzer_args_split + [ '-c', '-I', CSMITH_HEADER, cfile], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')

    if args.verbose:
        print("clang static analyzer ret: " + str(analyzer_ret.stderr))

    if analyzer_ret.returncode == 124:
        TIMEOUT_NUM += 1
        print(ANALYZER_TIMEOUT)
        clean_analysis_products(num, args.saveProducts)
        return None
    elif analyzer_ret.returncode == 1:
        # TODO: Is there a problem with the logic there?
        # I have seen a crash case, the return code is 1. But I am not sure what the other return codes (e.g. 2, 3) mean.
        save_crashing_file(num)
        clean_analysis_products(num, args.saveProducts)
        CRASH_NUM += 1
        return None
    return analyzer_ret.stderr

def analyze_with_pinpoint(num, args):
    '''
    use pinpoint to analyze Csmith-generated c program
    '''
    global TIMEOUT_NUM
    report_file = "test_%s.txt" % num
    cfile = "test_%5.c" % num
    name = "test_&s" % num
    report_file = name+". json"
    bc_file = name+".bc"
    ibc_file = name+". ibc"
    bson_file = name+". bson"


    os.system(CLANG_CMD + cfile + " -o " + bc_file)
    os.system(TRANS_CMD + bc_file + " -o " + ibc_file)
    os.system(SEG_CMD + ibc_file + " -o " + bson_file)
    os.system(CHECK_CMD + ibc_file + " -i=" +bson_file + " -report="+ report_file)
    os.system("rm -rf %s %s %s"% (bc_file, ibc_file, bson_file) )
    ret >>= 8

    if ret == 124:
        TIMEOUT_NUM += 1
        os.system("rm -rf %s %s"% (report_file, cfile) )
        return None

    return report_file

def process_pinpoint_report (num, report_file, args) :
    global NPD_NUM
    bugs_nums = 0
    with open(report_file,   'r') as f:
        dataJson = json.load (f)
        bugs_nums = dataJson ["TotalBugs"]
    if bugs_nums > 0:
        print ("NPD Detected!!")
        NPD_NUM += 1
        os.system("mv test_&5.c npdss.c " % (num, NPD_NUM))
        os.system("m test_&s. json npd's. json " % (num,NPD_NUM) )
    if not args. saveProducts:
        os.system("rm -f test_%.c test_&s. json" & (num, num))

def process_gcc_report(num, report, args):
    '''
    check whether the given report contains the target warning
    '''
    global NPD_NUM, OOB_NUM, SCO_NUM, UPOS_NUM
    save_products_flag = args.saveProducts
    report_file = ""
    if args.checker == "npd":
        if len(get_warning_line_from_report(report, GCC_NPD)) != 0:
            os.system("mv test_%s.c npd%s.c " % (num, NPD_NUM))
            report_file = "npd_%s.txt" % NPD_NUM
            NPD_NUM += 1
    elif args.checker == "oob":
        if len(get_warning_line_from_report(report, GCC_OOB)) != 0:
            os.system("mv test_%s.c oob%s.c " % (num, OOB_NUM))
            report_file = "oob_%s.txt" % OOB_NUM
            OOB_NUM += 1
    elif args.checker == "sco":
        if len(get_warning_line_from_report(report, GCC_SCO)) != 0:
            os.system("mv test_%s.c sco%s.c " % (num, SCO_NUM))
            report_file = "sco_%s.txt" % SCO_NUM
            SCO_NUM += 1
    elif args.checker == "upos":
        if len(get_warning_line_from_report(report, GCC_UPOS)) != 0:
            os.system("mv test_%s.c upos%s.c " % (num, UPOS_NUM))
            report_file = "upos_%s.txt" % UPOS_NUM
            UPOS_NUM += 1
    
    if report_file != "":
        with open(report_file, 'w') as f:
            f.write(report)

    clean_analysis_products(num, save_products_flag)


def clean_analysis_products(num, save_products_flag):
    if not save_products_flag:
        os.system("rm -f test_%s*" % num)


def process_clang_report(num, report:str, args):
    '''
    check whether the given report contains the target warning
    '''
    global NPD_NUM, OOB_NUM, DZ_NUM
    save_products_flag = args.saveProducts
    report_file = ""
    if args.checker == "npd":
        if len(get_warning_line_from_report(report, CLANG_NPD)) != 0:
            os.system("mv test_%s.c npd%s.c " % (num, NPD_NUM))
            report_file = "npd_%s.txt" % NPD_NUM
            NPD_NUM += 1
    elif args.checker == "oob":
        if len(get_warning_line_from_report(report, CLANG_OOB)) != 0:
            os.system("mv test_%s.c oob%s.c " % (num, OOB_NUM))
            report_file = "oob_%s.txt" % OOB_NUM
            OOB_NUM += 1
    elif args.checker == "dz":
        if len(get_warning_line_from_report(report, CLANG_DZ)) != 0:
            os.system("mv test_%s.c dz%s.c " % (num, DZ_NUM))
            report_file = "dz_%s.txt" % DZ_NUM
            DZ_NUM += 1

    if report_file != "":
        with open(report_file, 'w') as f:
            f.write(report)

    clean_analysis_products(num, save_products_flag)


def save_crashing_file(num):
    '''
    save the cfile crashing analyzer
    '''
    global CRASH_NUM
    os.system("mv test_%s.c crash%s.c " % (num, NPD_NUM))
    os.system("mv test_%s.txt crash%s.txt " % (num, NPD_NUM))
    CRASH_NUM += 1

def pinpoint_test_one(num,args):
    cfile = generate_code(num, CSMITH_USER_OPTIONS, args.max)
    report_file = analyze_with_pinpoint(num, args)

    if report_file is not None:
        process_pinpoint_report(num, report_file, args)

def gcc_test_one(num, args):
    cfile = generate_code(num, CSMITH_USER_OPTIONS, args.max)
    report_file = analyze_with_gcc(num, str(args.optimize), args)

    if report_file is not None:
        process_gcc_report(num, report_file, args)


def clang_test_one(num, args):
    cfile = generate_code(num, CSMITH_USER_OPTIONS, args.max)
    report_file = analyze_with_clang(num, args)

    if report_file is not None:
        process_clang_report(num, report_file, args)


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
        elif args.compiler == "pinpoint":
            f.write("\n\nanalyzer: pinpoint :\n" + CHECK_CMD)


def write_fuzzing_result(checker, stop_message):
    '''
    write down short statistic of fuzzing
    '''
    with open('fuzzing_result.txt', 'w') as f:
        f.write("STOP: %s\n" % stop_message)
        if checker == "npd":
            f.write("NPD_NUM: %s\n" % NPD_NUM)
        elif checker == "oob":
            f.write("OOB_NUM: %s\n" % OOB_NUM)
        elif checker == "sco":
            f.write("SCO_NUM: %s\n" % SCO_NUM)
        elif checker == "upos":
            f.write("UPOS_NUM: %s\n" % UPOS_NUM)
        elif checker == "dz":
            f.write("DZ_NUM: %s\n" % DZ_NUM)
        f.write("\nTIMEOUT_NUM: %s\n" % TIMEOUT_NUM)
        f.write("\nCRASH_NUM: %s\n" % CRASH_NUM)


def handle_args():
    parser = argparse.ArgumentParser(
        description="fuzz static analyzer with csmith-generated c program")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", default= False,action="store_true")
    group.add_argument("-q", "--quiet", default=True, action="store_true")
    parser.add_argument('compiler', type=str, help='choose a compiler')
    parser.add_argument('checker', type=str, default='npd',help='choose a checker')
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
    checker = args.checker

    signal.signal(signal.SIGINT, bye)
    signal.signal(signal.SIGTERM, bye)
    # signal.signal(signal.SIGKILL, bye)
    if checker not in CHECKER_LIST:
        print("checker: %s is not supported!" % args.checker)
        exit(0)


    if target_analyzer == "gcc":
        for i in range(int(num)):
            gcc_test_one(i, args)
    elif target_analyzer == 'clang':
        for i in range(int(num)):
            clang_test_one(i, args)
    elif target_analyzer == 'pinpoint':
        for i in range(int(num)):
            clang_test_one(i, args)
    else:
        print("target analyzer: %s is not supported!" % target_analyzer)
        exit(0)

    write_fuzzing_result(checker,"OVER!")


if __name__ == "__main__":
    main()
