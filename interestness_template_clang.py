#!/usr/bin/python3
import os
import subprocess
import shlex

CFILE = " "
OPT_LEVEL = " "

CSMITH_HEADER = "/usr/include/csmith"

CLANG_ANALYZER = "scan-build -disable-checker core.CallAndMessage -disable-checker core.DivideZero -disable-checker core.NonNullParamChecker -disable-checker core.StackAddressEscape -disable-checker core.UndefinedBinaryOperatorResult -disable-checker core.VLASize -disable-checker core.uninitialized.ArraySubscript -disable-checker core.uninitialized.Assign -disable-checker core.uninitialized.Branch -disable-checker core.uninitialized.CapturedBlockVariable -disable-checker core.uninitialized.UndefReturn -disable-checker cplusplus.InnerPointer -disable-checker cplusplus.Move -disable-checker cplusplus.NewDelete -disable-checker cplusplus.NewDeleteLeaks -disable-checker cplusplus.PlacementNew -disable-checker cplusplus.PureVirtualCall -disable-checker deadcode.DeadStores -disable-checker nullability.NullPassedToNonnull -disable-checker nullability.NullReturnedFromNonnull -disable-checker security.insecureAPI.gets -disable-checker security.insecureAPI.mkstemp -disable-checker security.insecureAPI.mktemp -disable-checker security.insecureAPI.vfork -disable-checker unix.API -disable-checker unix.Malloc -disable-checker unix.MallocSizeof -disable-checker unix.MismatchedDeallocator -disable-checker unix.Vfork -disable-checker unix.cstring.BadSizeArg -disable-checker unix.cstring.NullArg "
CLANG_OPTIONS = "-Wno-literal-conversion -Wno-bool-operation -Wno-pointer-sign -Wno-tautological-compare -Wno-incompatible-pointer-types -Wno-tautological-constant-out-of-range-compare -Wno-compare-distinct-pointer-types -Wno-implicit-const-int-float-conversion -Wno-constant-logical-operand -Wno-parentheses-equality -Wno-constant-conversion -Wno-unused-value -Xclang -analyzer-config -Xclang widen-loops=true "

compile_ret = subprocess.run(['clang', '-I', CSMITH_HEADER, CFILE],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')

if compile_ret.returncode != 0:
    print("compile failed!")
    exit(compile_ret.returncode)

run_ret = subprocess.run(['timeout', '10s', './a.out'],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')

if run_ret.returncode == 124:
    print("timeout!")
    exit(run_ret.returncode)
elif run_ret.returncode != 0:
    print("run failed!")
    exit(run_ret.returncode)

count_npd_flag = run_ret.stdout.count("NPD_FLAG")
print("count NPD_FLAG: %s" % count_npd_flag)

if count_npd_flag == 0:
    print("NPD_FLAG disappear!")
    exit(2)

if not os.path.exists("report_html"):
    ret = os.system("mkdir report_html")
    if ret != 0:
        print("fail to mkdir report_html")
        exit(ret >> 8)

report_html = "report_html"

clang_args_split = shlex.split(CLANG_OPTIONS)
clang_analyzer_args_split = shlex.split(CLANG_ANALYZER)

analyze_ret = subprocess.run(clang_analyzer_args_split + ['-o', report_html, 'clang'] + clang_args_split + ['-c', '-I', CSMITH_HEADER, CFILE],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
print(analyze_ret.stderr)

if analyze_ret.stderr.count("[core.NullDereference]") == 0:
    print("NullDereference disappear!")
    exit(3)

# use ccomp to check if there are undefined behaviors
ccomp_ret = subprocess.run(['ccomp', '-I', CSMITH_HEADER, '-interp', '-fall', '-fstruct-passing',
                           CFILE], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")

if ccomp_ret.stdout.count("Undefined behavior") != 0:
    print("undefined behavior!")
    # print(ccomp_ret)
    exit(4)
    
if ccomp_ret.returncode != 0:
    print("ccomp_ret returncode: %s" % ccomp_ret.returncode)
    print("compcert failed!")  # cannot comment this line!
    # print(ccomp_ret)
    exit(ccomp_ret.returncode)

exit(0)
