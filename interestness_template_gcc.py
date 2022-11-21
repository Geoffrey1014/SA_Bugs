#!/usr/bin/python3
import subprocess
import shlex

CFILE = " "
OPT_LEVEL = " "

CSMITH_HEADER = "/usr/include/csmith"
GCC_ANALYZER = "gcc -fanalyzer -fanalyzer-call-summaries -Wno-analyzer-double-fclose -Wno-analyzer-double-free -Wno-analyzer-exposure-through-output-file -Wno-analyzer-file-leak -Wno-analyzer-free-of-non-heap -Wno-analyzer-malloc-leak -Wno-analyzer-mismatching-deallocation -Wno-analyzer-null-argument -Wno-analyzer-possible-null-argument -Wno-analyzer-possible-null-dereference -Wno-analyzer-shift-count-negative -Wno-analyzer-shift-count-overflow -Wno-analyzer-stale-setjmp-buffer -Wno-analyzer-unsafe-call-within-signal-handler -Wno-analyzer-use-after-free -Wno-analyzer-use-of-pointer-in-stale-stack-frame -Wno-analyzer-use-of-uninitialized-value -Wno-analyzer-write-to-const -Wno-analyzer-write-to-string-literal -fdiagnostics-plain-output -fdiagnostics-format=text "

print("compile: gcc")

compile_ret = subprocess.run(['gcc', '-O' + OPT_LEVEL, '-I', CSMITH_HEADER, CFILE],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
print(compile_ret.stderr)
# program cannot have compiler error
if compile_ret.returncode != 0:
    print("Compile failed")  # cannot comment this line!
    exit(compile_ret.returncode)

print("run")
run_ret = subprocess.run(['timeout', '5s', './a.out'],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
print(run_ret)

if run_ret.returncode == 124:
    print("Timeout!")  # cannot comment this line!
    exit(run_ret.returncode)
elif run_ret.returncode != 0:
    print("Run failed!")  # cannot comment this line!
    exit(run_ret.returncode)

count_npd_flag = run_ret.stdout.count("NPD_FLAG")
print("count NPD_FLAG: %s" % count_npd_flag)
# program run result has to keep output NPD_FLAG
if count_npd_flag == 0:
    print("NPD FLAG disappear")  # cannot comment this line!
    exit(2)

# analyzer has to keep npd warning
print("run analyzer")
analyzer_args_split = shlex.split(GCC_ANALYZER)
analyzer_ret = subprocess.run(
    analyzer_args_split + ['-O' + OPT_LEVEL, '-c', '-I', CSMITH_HEADER, CFILE], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
print(analyzer_ret.stderr)

if analyzer_ret.stderr.count("CWE-476") == 0:
    print("CWE-476 disappear")
    print("NullDereference disappear")  # cannot comment this line!
    exit(3)

# use ccomp to check if there are undefined behaviors
print("run compcert")
ccomp_ret = subprocess.run(['ccomp', '-I', CSMITH_HEADER, '-interp', '-fall', '-fstruct-passing',
                           CFILE], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
if ccomp_ret.stdout.count("Undefined behavior") != 0:
    print("Undefined behavior")
    # print(ccomp_ret)
    exit(4)
if ccomp_ret.returncode != 0:
    print("ccomp_ret returncode: %s" % ccomp_ret.returncode)
    print("Compcert failed")  # cannot comment this line!
    # print(ccomp_ret)
    exit(ccomp_ret.returncode)
exit(0)
