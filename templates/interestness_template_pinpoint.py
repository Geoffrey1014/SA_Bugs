#!/usr/bin/python3
import os,subprocess,shlex,sys,json
from config import *

CFILE = " "
OPT_LEVEL = "0"



compile_ret = subprocess.run([GCC, '-I', CSMITH_HEADER, CFILE],
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
name, _ = CFILE.split('.')
report_file =   name+".json"
bc_file =   name+".bc"
ibc_file = name+".ibc"
bson_file = name+".bson"

os.system(CLANG_CMD + CFILE + " -o " + bc_file)
os.system(TRANS_CMD + bc_file + " -o " + ibc_file)
os.system(SEG_CMD + ibc_file + " -o " + bson_file)
ret = os.system(CHECK_CMD + ibc_file + " -i=" +bson_file + " -report="+ report_file)
os.system("rm -rf %s %s %s"% (bc_file, ibc_file, bson_file) )

bugs_nums = 0
with open (report_file, 'r') as f:
    dataJson = json.load(f)
    bugs_nums = dataJson ("TotalBugs")

if bugs_nums == 0: 
    print ("NullDereference disappear") # cannot comment this line!
    exit (3)

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
