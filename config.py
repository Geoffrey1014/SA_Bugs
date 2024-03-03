# config.py
__all__ = ["CHECK_CMD","SEG_CMD", "TRANS_CMD", "CLANG_CMD","CSMITH_HEADER", "CSMITH_TIMEOUT", "COMPILER_TIMEOUT", "PROG_TIMEOUT", "CFE", "INSTRUMENT_TOOL", "GCC", "GCC_OPTIONS", "GCC_ANALYZER", "CLANG", "CLANG_OPTIONS", "CLANG_ANALYZER", "CSMITH_USER_OPTIONS", "MIN_PROGRAM_SIZE", "MAX_PROGRAM_SIZE", "CHECKER_LIST", "ANALYZER_TIMEOUT", "GCC_NPD", "GCC_OOB", "GCC_SCO", "GCC_UPOS", "RUN_TIMEOUT_NUM", "FLAG_DIS_STR", "UB_STR", "CLANG_DZ", "CLANG_OOB", "CLANG_NPD"]
# user-configurable stuff
CSMITH_HEADER = "/usr/include/csmith"

# kill csmith after this many seconds
CSMITH_TIMEOUT = "90"

# kill compiler after this many seconds
COMPILER_TIMEOUT = "120"

# kill compiler's output after this many seconds
PROG_TIMEOUT = "8"

CFE = "/home/build-clang-16/bin/cfe_preprocess"
INSTRUMENT_TOOL = "/home/build-clang-16/bin/tooling-sample"

GCC = "/usr/local/gcc-13-cov/bin/gcc"
GCC_OPTIONS = " -fanalyzer -fanalyzer-call-summaries -fdiagnostics-plain-output -fdiagnostics-format=text "
GCC_ANALYZER = GCC + GCC_OPTIONS

<<<<<<< HEAD
CLANG = "/usr/local/clang-16-gcov/bin/clang"
CLANG_OPTIONS = " --analyze --analyzer-output text -Xclang  -analyzer-constraints=range -Xclang  -setup-static-analyzer  -Xclang -analyzer-config  -Xclang  eagerly-assume=false   -Xclang  -analyzer-checker=core,alpha.security "
CLANG_DEBUG_OPTIONS = " --analyze --analyzer-output text -Xclang  -analyzer-constraints=range -Xclang  -setup-static-analyzer  -Xclang -analyzer-config  -Xclang  eagerly-assume=false   -Xclang  -analyzer-checker=debug.ExprInspection "
=======
CLANG = "clang"
CLANG_OPTIONS = " --analyze --analyzer-output text -Xclang -analyzer-constraints=range -Xclang -setup-static-analyzer -Xclang -analyzer-config -Xclang eagerly-assume=false -Xclang -analyzer-checker=core,alpha.security "
>>>>>>> fe3dea2 (small fix)
CLANG_ANALYZER = CLANG + CLANG_OPTIONS

# CSMITH_USER_OPTIONS = "--no-argc --no-bitfields --no-global-variables --max-pointer-depth 2 "
CSMITH_USER_OPTIONS = " --no-bitfields --no-global-variables --max-pointer-depth 2 "
MIN_PROGRAM_SIZE = "8000" 
MAX_PROGRAM_SIZE = "8000"

CHECKER_LIST = ["npd", "oob", "dz", "sco", "upos"]
ANALYZER_TIMEOUT = "timeout 60 "

GCC_NPD = "-Wanalyzer-null-dereference"
GCC_OOB = "-Wanalyzer-out-of-bounds"
GCC_SCO = "-Wanalyzer-shift-count-overflow"
GCC_UPOS = "-Wanalyzer-use-of-pointer-in-stale-stack-frame"

CLANG_NPD = "core.NullDereference"
CLANG_OOB = "alpha.security.ArrayBoundV2"
CLANG_DZ = "core.DivideZero"
 
RUN_TIMEOUT_NUM = "10s"
FLAG_DIS_STR="FLAG disappear"
UB_STR = "Undefined behavior"

CLANG_CMD="/opt/working-place/pinpoint/third-party/bin/clang-3.6 -g -c -emit-llvm -I /usr/include/csmith "
TRANS_CMD="/opt/working-place/pinpoint/bin/pp-transform "
SEG_CMD="/opt/working-place/pinpoint/bin/pp-build  -execution-mode normal -falcon-cg "

# CHECK_CMD="/opt/working-place/pinpoint/bin/pp-check -debug -debug-psa-trace -nworkers=1 -hide-progress-bar -ps-npd  -execution-mode normal  -enable-core-legacy -system-timeout=1800 -load-licence=/root/.pinpoint/sbrella.lic  "
CHECK_CMD="/opt/working-place/pinpoint/bin/pp-check  -nworkers=1 -hide-progress-bar -ps-npd -execution-mode normal  -enable-core-legacy -system-timeout=1800 -load-licence=/root/.pinpoint/sbrella.lic  "
# CHECK_CMD="/opt/working-place/pinpoint/bin/pp-check  -nworkers=1 -hide-progress-bar -ps-npd  -ps-npd-enable-null-analysis -ps-cnd -ps-drm-npd -execution-mode normal  -enable-core-legacy -system-timeout=1800  -iminfo-dir=/root/MY_CODES/random_code/iminfo  -report-inter-trace=/root/MY_CODES/random_code/iminfo/test.ibc.im.json -load-licence=/root/.pinpoint/sbrella.lic -load-external-spec=/root/pinpoint/resource/new-spec.json -load-external-spec=/root/pinpoint/resource/taint-common-spec.json -load-external-spec=/root/pinpoint/resource/taint-demangle-spec.json -load-external-spec=/root/pinpoint/resource/taint-regex-spec.json -load-external-spec=/root/pinpoint/resource/struts2-hiberate-mybatis-spec.json "
