#!/usr/bin/python3
import subprocess
import shlex

CFILE = ""
OPT_LEVEL = ""

CSMITH_HEADER = "/usr/include/csmith"
CLANG_ANALYZER = "clang --analyze  -Xclang -analyzer-stats  -Xclang  -analyzer-constraints=range -Xclang  -setup-static-analyzer  -Xclang -analyzer-config  -Xclang  eagerly-assume=false   -Xclang  -analyzer-checker=core,alpha.security.taint,debug.ExprInspection,debug.TaintTest  "

INSTRUMENT_FILE = "instrument_" + CFILE

# 这一步的返回值是不是要处理一下？
print("instrument cfile")
subprocess.run("/home/working-space/build-llvm-main/bin/tooling-sample clang %s -- -I %s > %s"%(CFILE, CSMITH_HEADER, INSTRUMENT_FILE),
                               stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, shell=True , check=True )

# analyzer has to keep npd warning
print("run analyzer")
analyzer_args_split = shlex.split(CLANG_ANALYZER)
analyzer_ret = subprocess.run(
    analyzer_args_split + ['-O' + OPT_LEVEL, '-c', '-I', CSMITH_HEADER, INSTRUMENT_FILE], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
print(analyzer_ret.stderr)

subprocess.run(['rm', '-f', 'instrument_eval.o'],  stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8' )

if analyzer_ret.stderr.count("warning: FALSE") == 0:
    print("warning: FALSE is 0")
    # print("NullDereference disappear")  # cannot comment this line!
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
