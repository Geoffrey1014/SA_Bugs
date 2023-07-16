#!/usr/bin/python3
import subprocess
import shlex,re

CFILE = ""
OPT_LEVEL = ""

CSMITH_HEADER = "/usr/include/csmith"
GCC_ANALYZER = "gcc -fanalyzer -fdiagnostics-plain-output -fdiagnostics-format=text "
TOOLING_EVAL = "/home/working-space/build-llvm-main/bin/tooling-sample"
TOOLING_CFE = "/home/working-space/build-llvm-main/bin/cfe_preprocess"

INSTRUMENT_FILE = "instrument_" + CFILE
INSTRUMENT_P_FILE = "instrument_p_" + CFILE
FILE_NAME = CFILE.split('.').pop(0)
RUN_FILE = "run_" + FILE_NAME
RUN_P_FILE = "run_p_" + FILE_NAME


def get_eval_false_lines(analysis_result:str):
    eval_false_lines = set()
    lines = analysis_result.split('\n')

    for line in lines:
        # print("line %s" %line)
        if re.search("warning: FALSE", line):
            false_info = re.split(":", line)
            eval_false_lines.add(false_info.pop(1))

    print("eval_false_lines: %s" %eval_false_lines)

    return eval_false_lines


def instrument_cfile( eval_falase_lines):
    print("instrument_cfile: %s" % INSTRUMENT_FILE)
    print("instrument_p_cfile: %s" % INSTRUMENT_P_FILE)
    with open(INSTRUMENT_FILE, "r") as f:
        cfile_lines = f.readlines()

        for num in eval_falase_lines:
            c_num = int(num)-1
            print(c_num)
            print(cfile_lines[c_num])
            cfile_lines[c_num] = 'printf("FALSE_FLAG\\n");' + cfile_lines[c_num]
            print(cfile_lines[c_num])

        with open(INSTRUMENT_P_FILE, "w") as f:
            f.writelines(cfile_lines)

    return INSTRUMENT_P_FILE


print("instrument __analyzer_eval to cfile")
instru_ret = subprocess.run("%s %s -- -I %s "%(TOOLING_CFE,CFILE,CSMITH_HEADER),
                               stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, shell=True, check=True)

if instru_ret.returncode != 0:
    exit(instru_ret.returncode)

instru_ret = subprocess.run("%s gcc %s -- -I %s > %s"%(TOOLING_EVAL, CFILE, CSMITH_HEADER, INSTRUMENT_FILE),
                               stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, shell=True , check=True )

if instru_ret.returncode != 0:
    exit(instru_ret.returncode)

# analyzer has to keep warning: FALSE
print("run analyzer")
analyzer_args_split = shlex.split(GCC_ANALYZER)
analyzer_ret = subprocess.run(
    analyzer_args_split + ['-O' + OPT_LEVEL, '-c' ,'-I', CSMITH_HEADER, INSTRUMENT_FILE], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
print(analyzer_ret.stderr)


if analyzer_ret.stderr.count("warning: FALSE") == 0:
    print("warning: FALSE is 0")
    # print("NullDereference disappear")  # cannot comment this line!
    exit(3)

if analyzer_ret.stderr.count("-Wanalyzer-use-of-uninitialized-value") != 0 :
    print("has -Wanalyzer-use-of-uninitialized-value ")
    exit(4)

if analyzer_ret.stderr.count("-Wanalyzer-infinite-recursion") != 0 :
    print("has -Wanalyzer-infinite-recursion ")
    exit(5)
    
if analyzer_ret.stderr.count("undefined reference") != 0 :
    print("has undefined reference ")
    exit(6)
    


# # 从 analyze 的结果中拿到 FALSE 的行号， 然后插桩 printf(“FALSE_FLAG”); 

# eval_false_lines = get_eval_false_lines(analyzer_ret.stderr)
# instrument_cfile(eval_false_lines)


# print("compile: gcc")

# compile_ret = subprocess.run(['gcc', '-O' + OPT_LEVEL, '-I', CSMITH_HEADER, INSTRUMENT_P_FILE, '-o', RUN_FILE],
#                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
# # print(compile_ret.stderr)
# # program cannot have compiler error
# if compile_ret.returncode != 0:
#     print("Compile failed")  # cannot comment this line!
#     exit(compile_ret.returncode)

# print("run")
# run_ret = subprocess.run(['timeout', '5s', './'+RUN_FILE],
#                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
# print(run_ret)


# # check 是否有 flag 
# if run_ret.stdout.count("FALSE_FLAG") == 0:
#     exit(7)

# # 看看是不是 一直 print
# if run_ret.stdout.count("FALSE_FLAG") > 10000:
#     exit(8)

# # if run_ret.returncode == 124:
# #     print("Timeout!")  # cannot comment this line!
# #     exit(run_ret.returncode)
# # elif run_ret.returncode != 0: #TODO： run fail 没有关系其实
# #     print("Run failed!")  # cannot comment this line!
# #     exit(run_ret.returncode)




# # 要保证 main 函数还在，

# # use ccomp to check if there are undefined behaviors
# print("run compcert")
# ccomp_ret = subprocess.run(['ccomp', '-I', CSMITH_HEADER, '-interp', '-fall', 
#                            CFILE], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
# if ccomp_ret.stdout.count("Undefined behavior") != 0:
#     print("Undefined behavior")
#     # print(ccomp_ret)
#     exit(4)
# if ccomp_ret.returncode != 0:
#     print("ccomp_ret returncode: %s" % ccomp_ret.returncode)
#     print("Compcert failed")  # cannot comment this line!
#     # print(ccomp_ret)
#     exit(ccomp_ret.returncode)

# use gcc sanitizer to check undefined behaviors

# print("run gcc sanitizer")
# san_ret = subprocess.run(['gcc', '-fsanitize=undefined', '-I', CSMITH_HEADER, INSTRUMENT_P_FILE,'-o', RUN_P_FILE],stdout=subprocess.PIPE, stderr=subprocess.PIPE,)

# run_return = subprocess.run(['./'+RUN_P_FILE],stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")

# print(run_return)
# if "FALSE_FLAG" not in run_return.stdout:
#     if "runtime error: signed integer overflow" in run_return.stderr or "runtime error: shift exponent" in run_return.stderr:
#         exit(1)

# exit(0)
