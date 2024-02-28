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

# UB
if analyzer_ret.stderr.count("core.BitwiseShift") != 0:
    exit(4)
if analyzer_ret.stderr.count("core.DivideZero") != 0:
    exit(5)
if analyzer_ret.stderr.count("core.NullDereference") != 0:
    exit(6)
if analyzer_ret.stderr.count("core.StackAddressEscape") != 0:
    exit(7)
if analyzer_ret.stderr.count("core.UndefinedBinaryOperatorResult") != 0:
    exit(8)
if analyzer_ret.stderr.count("core.VLASize") != 0:
    exit(9)
if analyzer_ret.stderr.count("core.uninitialized.ArraySubscript") != 0:
    exit(10)
if analyzer_ret.stderr.count("core.uninitialized.Assign") != 0:
    exit(11)
if analyzer_ret.stderr.count("core.uninitialized.Branch") != 0:
    exit(12)
if analyzer_ret.stderr.count("core.uninitialized.CapturedBlockVariable") != 0:
    exit(13)
if analyzer_ret.stderr.count("core.uninitialized.UndefReturn") != 0:
    exit(14)
if analyzer_ret.stderr.count("alpha.core.PointerArithm") != 0:
    exit(15)
if analyzer_ret.stderr.count("alpha.core.PointerSub") != 0:
    exit(16)
if analyzer_ret.stderr.count("alpha.core.StackAddressAsyncEscape") != 0:
    exit(17)
if analyzer_ret.stderr.count("alpha.security.ArrayBoundV2") != 0:
    exit(18)
if analyzer_ret.stderr.count("alpha.unix.cstring.BufferOverlap") != 0:
    exit(19)
if analyzer_ret.stderr.count("alpha.unix.cstring.OutOfBounds") != 0:
    exit(20)
if analyzer_ret.stderr.count("alpha.unix.cstring.UninitializedRead") != 0:
    exit(21)

# use ccomp to check if there are undefined behaviors
print("run compcert")
ccomp_ret = subprocess.run(['ccomp', '-I', CSMITH_HEADER, '-interp', '-fall', '-fstruct-passing',
                           CFILE], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
if ccomp_ret.stdout.count("Undefined behavior") != 0:
    print("Undefined behavior")
    # print(ccomp_ret)
    exit(22)
if ccomp_ret.returncode != 0:
    print("ccomp_ret returncode: %s" % ccomp_ret.returncode)
    print("Compcert failed")  # cannot comment this line!
    # print(ccomp_ret)
    exit(ccomp_ret.returncode)
exit(0)
