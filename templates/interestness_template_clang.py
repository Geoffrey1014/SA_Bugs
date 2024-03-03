#!/usr/bin/python3
import subprocess,shlex,sys
from config import *

CFILE = " "
OPT_LEVEL = " "
CHECKER = "dz"

if CHECKER == "npd":
    warning_name = CLANG_NPD
elif CHECKER == "oob":
    warning_name = CLANG_OOB
elif CHECKER == "dz":   
    warning_name = CLANG_DZ
else:
    print("checker not found!")
    exit(-1)

compile_ret = subprocess.run(['clang', '-I', CSMITH_HEADER, CFILE, "-o", "hwg"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')

if compile_ret.returncode != 0:
    print("compile failed!")
    exit(compile_ret.returncode)

run_ret = subprocess.run(['timeout', '10s', './hwg'],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')

if run_ret.returncode == 124:
    print("timeout!")
    exit(run_ret.returncode)
elif run_ret.returncode != 0:
    print("run failed!")
    exit(run_ret.returncode)

count_flag = run_ret.stdout.count("FLAG")
print("count FLAG: %s" % count_flag)

if count_flag == 0:
    print(FLAG_DIS_STR)  # cannot comment this line!
    exit(2)

analyzer_args_split = shlex.split(CLANG_ANALYZER)

analyzer_ret = subprocess.run(
    analyzer_args_split + ['-O' + OPT_LEVEL, '-c', '-I', CSMITH_HEADER, CFILE], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
print(analyzer_ret.stderr)

if analyzer_ret.stderr.count(warning_name) == 0:
    print("%s disappear!" % warning_name)  # cannot comment this line!
    exit(3)

# use ccomp to check if there are undefined behaviors
ccomp_ret = subprocess.run(['ccomp', '-I', CSMITH_HEADER, '-interp', '-fall', '-fstruct-passing',
                           CFILE], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")

if ccomp_ret.stdout.count("Undefined behavior") != 0:
    print("undefined behavior!")
    exit(4)
if ccomp_ret.returncode != 0:
    print("ccomp_ret returncode: %s" % ccomp_ret.returncode)
    print("compcert failed!")  # cannot comment this line!
    exit(ccomp_ret.returncode)

exit(0)
