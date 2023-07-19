#!/usr/bin/python3
import subprocess
import shlex

CFILE = "oob2.c"
OPT_LEVEL = "0"
CSMITH_HEADER = "/usr/include/csmith"

GCC = "/usr/local/gcc-13-9533/bin/gcc"
GCC_OPTIONS = " -fanalyzer -fanalyzer-call-summaries -fdiagnostics-plain-output -fdiagnostics-format=text "
GCC_ANALYZER = GCC + GCC_OPTIONS

compile_ret = subprocess.run([GCC, '-O' + OPT_LEVEL, '-I', CSMITH_HEADER, CFILE],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
# print(compile_ret.stderr)

# program cannot have compiler error
if compile_ret.returncode != 0:
    print("compile failed!")  # cannot comment this line!
    exit(compile_ret.returncode)

run_ret = subprocess.run(['timeout', '10s', './a.out'],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')

if run_ret.returncode == 124:
    print("timeout!")  # cannot comment this line!
    exit(run_ret.returncode)
elif run_ret.returncode != 0:
    print("run failed!")  # cannot comment this line!
    exit(run_ret.returncode)

# count_npd_flag = run_ret.stdout.count("NPD_FLAG")
# print("count NPD_FLAG: %s" % count_npd_flag)
# # program run result has to keep output NPD_FLAG
# if count_npd_flag == 0:
#     print("NPD FLAG disappear")  # cannot comment this line!
#     exit(2)

# analyzer has to keep npd warning
analyzer_args_split = shlex.split(GCC_ANALYZER)
analyzer_ret = subprocess.run(
    analyzer_args_split + ['-O' + OPT_LEVEL, '-c', '-I', CSMITH_HEADER, CFILE], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
# print(analyzer_ret.stderr)

if analyzer_ret.stderr.count("-Wanalyzer-out-of-bounds") == 0:
    print("-Wanalyzer-out-of-bounds disappear!")  # cannot comment this line!
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
