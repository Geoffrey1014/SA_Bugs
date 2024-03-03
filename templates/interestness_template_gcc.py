#!/usr/bin/python3
import subprocess,shlex,sys
from config import *

CFILE = "instrument_xxx.c"
OPT_LEVEL = "0"
CHECKER = "oob"

if CHECKER == "npd":
    warning_name = GCC_NPD
elif CHECKER == "oob":
    warning_name = GCC_OOB
else:
    print("checker not found!")
    exit(-1)


compile_ret = subprocess.run([GCC, '-O' + OPT_LEVEL, '-I', CSMITH_HEADER, CFILE, "-o", "hwg"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
# print(compile_ret)

# program cannot have compiler error
if compile_ret.returncode != 0:
    print("compile failed!")  # cannot comment this line!
    exit(compile_ret.returncode)

run_ret = subprocess.run(['timeout', RUN_TIMEOUT_NUM, './hwg'],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')

if run_ret.returncode == 124:
    print("timeout!")  # cannot comment this line!
    exit(run_ret.returncode)
elif run_ret.returncode != 0:
    print("run failed!")  # cannot comment this line!
    exit(run_ret.returncode)

count_flag = run_ret.stdout.count("FLAG")
print("count FLAG: %s" % count_flag)
# program run result has to keep output FLAG
if count_flag == 0:
    print(FLAG_DIS_STR)  # cannot comment this line!
    exit(2)

# analyzer has to keep the warning
analyzer_args_split = shlex.split(GCC_ANALYZER)
analyzer_ret = subprocess.run(
    analyzer_args_split + ['-O' + OPT_LEVEL, '-c', '-I', CSMITH_HEADER, CFILE], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
# print(analyzer_ret.stderr)

if analyzer_ret.stderr.count(warning_name) == 0:
    print("%s disappear!" % warning_name)  # cannot comment this line!
    exit(3)

# use ccomp to check if there are undefined behaviors
ccomp_ret = subprocess.run(['ccomp', '-I', CSMITH_HEADER, '-interp', '-fall', '-fstruct-passing',
                           CFILE], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
print(ccomp_ret.stdout)

if ccomp_ret.stdout.count("Undefined behavior") != 0:
    print(UB_STR)  # cannot comment this line!
    exit(4)
if ccomp_ret.returncode != 0:
    print("ccomp_ret returncode: %s" % ccomp_ret.returncode)
    print("compcert failed!")  # cannot comment this line!
    exit(ccomp_ret.returncode)

exit(0)
