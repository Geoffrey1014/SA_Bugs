#!/usr/bin/python3
import os
import subprocess
import shlex
CFILE = " "
OPT_LEVEL = " "

CSMITH_HEADER = "/usr/include/csmith"
GCC_ANALYZER = "gcc -fanalyzer -fdiagnostics-plain-output -fdiagnostics-format=text"

U_FLAG = 0
N_FLAG = 0

subprocess.run(["gcc", "-I", CSMITH_HEADER, "-O0", "-fsanitize=null", CFILE],
               stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")

run_ret = subprocess.run(["timeout", "10s", "./a.out"],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")

if run_ret.stderr.count("runtime error") < 1 and run_ret.stderr.count("null pointer") < 1:
    exit(1)

analyze_args_split = shlex.split(GCC_ANALYZER)
analyze_ret = subprocess.run(
    analyze_args_split + ["-I", CSMITH_HEADER, "-O0", CFILE], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")

if analyze_ret.stderr.count("error") != 0:
    exit(5)
if analyze_ret.stderr.count("data definition has no type or storage class") != 0:
    exit(4)
if analyze_ret.stderr.count("CWE-457") != 0:
    exit(2)
if analyze_ret.stderr.count("CWE-476") != 0:
    exit(3)
if analyze_ret.stderr.count("-Wimplicit-int") != 0:
    exit(6)

os.system(
    "ccomp -I {} -interp -fall {} > out_ccomp.txt 2>&1".format(CSMITH_HEADER, CFILE))

with open("out_ccomp.txt", "r") as f:
    for line in f.readlines():
        if "Undefined behavior" in line:
            U_FLAG = 1
        if "*0LL" in line:
            N_FLAG = 1

if U_FLAG == 1 and N_FLAG != 1:
    exit(7)

exit(0)
