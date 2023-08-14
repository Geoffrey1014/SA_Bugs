#!/usr/bin/python3
import subprocess,shlex,sys
CSMITH_HEADER,CSMITH_TIMEOUT,COMPILER_TIMEOUT,PROG_TIMEOUT,CFE,INSTRUMENT_TOOL,GCC,GCC_OPTIONS,GCC_ANALYZER,CLANG,CLANG_OPTIONS,CLANG_ANALYZER,CSMITH_USER_OPTIONS,MIN_PROGRAM_SIZE,MAX_PROGRAM_SIZE,CHECKER_LIST,ANALYZER_TIMEOUT,GCC_NPD,GCC_OOB,RUN_TIMEOUT_NUM,FLAG_DIS_STR,UB_STR="/usr/include/csmith", "90", "120", "8", "/home/working-space/build-llvm-main/bin/cfe_preprocess", "/home/working-space/build-llvm-main/bin/tooling-sample", "/usr/local/gcc-13-9533/bin/gcc", " -fanalyzer -fanalyzer-call-summaries -fdiagnostics-plain-output -fdiagnostics-format=text ", "/usr/local/gcc-13-9533/bin/gcc -fanalyzer -fanalyzer-call-summaries -fdiagnostics-plain-output -fdiagnostics-format=text ", "clang", " --analyze --analyzer-output text -Xclang  -analyzer-constraints=range -Xclang  -setup-static-analyzer  -Xclang -analyzer-config  -Xclang  eagerly-assume=false   -Xclang  -analyzer-checker=core,alpha.security ", "clang --analyze --analyzer-output text -Xclang  -analyzer-constraints=range -Xclang  -setup-static-analyzer  -Xclang -analyzer-config  -Xclang  eagerly-assume=false   -Xclang  -analyzer-checker=core,alpha.security ", "--no-bitfields --no-global-variables --max-pointer-depth 2 ", "8000", "8000", "['npd', 'oob']", "timeout 60 ", "-Wanalyzer-null-dereference", "-Wanalyzer-out-of-bounds", "10s", "FLAG disappear", "Undefined behavior"

CFILE = "oob_0.c"
OPT_LEVEL = "2"
CHECKER = "oob"

if CHECKER == "npd":
    warning_name = GCC_NPD
elif CHECKER == "oob":
    warning_name = GCC_OOB
else:
    print("checker not found!")
    exit(-1)


compile_ret = subprocess.run([GCC, '-O' + OPT_LEVEL, '-I', CSMITH_HEADER, CFILE],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
# print(compile_ret)

# program cannot have compiler error
if compile_ret.returncode != 0:
    print("compile failed!")  # cannot comment this line!
    exit(compile_ret.returncode)

run_ret = subprocess.run(['timeout', RUN_TIMEOUT_NUM, './a.out'],
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
