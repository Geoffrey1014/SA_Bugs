# config.py

# user-configurable stuff
CSMITH_HEADER = "/usr/include/csmith"

# kill csmith after this many seconds
CSMITH_TIMEOUT = 90

# kill compiler after this many seconds
COMPILER_TIMEOUT = 120

# kill compiler's output after this many seconds
PROG_TIMEOUT = 8

CFE = "/home/working-space/build-llvm-main/bin/cfe_preprocess"
INSTRUMENT_TOOL = "/home/working-space/build-llvm-main/bin/tooling-sample"

GCC = "/usr/local/gcc-13-9533/bin/gcc"
GCC_OPTIONS = " -fanalyzer -fanalyzer-call-summaries -fdiagnostics-plain-output -fdiagnostics-format=text "
GCC_ANALYZER = GCC + GCC_OPTIONS

CLANG = "clang"
CLANG_OPTIONS = " --analyze --analyzer-output text -Xclang  -analyzer-constraints=range -Xclang  -setup-static-analyzer  -Xclang -analyzer-config  -Xclang  eagerly-assume=false   -Xclang  -analyzer-checker=core,alpha.security "
CLANG_ANALYZER = CLANG + CLANG_OPTIONS

CSMITH_USER_OPTIONS = "--no-bitfields --no-global-variables --max-pointer-depth 2 "
MIN_PROGRAM_SIZE = 8000 
MAX_PROGRAM_SIZE = 8000

CHECKER_LIST = ["npd", "oob"]
ANALYZER_TIMEOUT = "timeout 60 "
 