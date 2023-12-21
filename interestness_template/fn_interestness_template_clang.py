#!/usr/bin/python3
import os
import subprocess
import shlex
CFILE = " "
OPT_LEVEL = " "

CSMITH_HEADER = "/usr/include/csmith"
CLANG_OPTIONS = "-Xclang -analyzer-config -Xclang widen-loops=true"
CLANG_ANALYZER = "scan-build"

U_FLAG = 0
N_FLAG = 0

subprocess.run(["gcc", "-I", CSMITH_HEADER, "-O0", "-fsanitize=null", CFILE],
               stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")

run_ret = subprocess.run(["timeout", "10s", "./a.out"],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")

if run_ret.stderr.count("runtime error") < 1 and run_ret.stderr.count("null pointer") < 1:
    exit(1)

report_html = "report_html"
if not os.path.exists("report_html"):
    os.system("mkdir report_html")

clang_analyzer_args_split = shlex.split(CLANG_ANALYZER)
clang_args_split = shlex.split(CLANG_OPTIONS)

analyze_ret = subprocess.run(clang_analyzer_args_split + ["-o", report_html, "clang"] + clang_args_split + ["-O0", "-c", "-I", CSMITH_HEADER, CFILE],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")

if analyze_ret.stderr.count("error") != 0:
    exit(2)
if analyze_ret.stderr.count("core.NullDereference") != 0:
    exit(3)
if analyze_ret.stderr.count("uninitialized") != 0:
    exit(4)
if analyze_ret.stderr.count("core.UndefinedBinaryOperatorResult") != 0:
    exit(5)

os.system(
    "ccomp -I {} -interp -fall {} > out_ccomp.txt 2>&1".format(CSMITH_HEADER, CFILE))

with open("out_ccomp.txt", "r") as f:
    for line in f.readlines():
        if "Undefined behavior" in line:
            U_FLAG = 1
        if "*0LL" in line:
            N_FLAG = 1

if U_FLAG == 1 and N_FLAG != 1:
    exit(6)

exit(0)
