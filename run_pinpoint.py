#!/usr/bin/python3
import os,json,sys
from config import *
from config import SEG_CMD, CHECK_CMD, CLANG_CMD, TRANS_CMD

def analyze_with_pinpoint(cfile_path):
    """
    Use PinPoint to analyze Csmith-generated C program
    """
    par_path, cfile_name = os.path.split(cfile_path)
    name, _ = cfile_name.split(".")

    report_file = os.path.join(par_path, name + ".json")
    ibc_file = os.path.join(par_path, name + ".ibc")
    bc_file = os.path.join(par_path, name + ".bc")
    bson_file = os.path.join(par_path, name + ".bson")

    print(f"par_path: {par_path}")

    os.system(f"{CLANG_CMD} {cfile_path} -o {bc_file}")
    os.system(f"{TRANS_CMD} {bc_file} -o {ibc_file}")
    os.system(f"{SEG_CMD} {ibc_file} -o {bson_file}")
    os.system(f"{CHECK_CMD} {ibc_file} -i={bson_file} -report={report_file}")

    if not par_path:
        print("par_path is empty")
    os.system(f"rm -f {par_path}/*.bc {par_path}/*.ibc {par_path}/*.bson")

    return report_file


def checkNpd(path):
    with open(path, "r") as f:
        dataJson = json.load(f)
        if dataJson["TotalBugs"] > 0:
            print("NPD detected!")
            exit(0)
        else:
            print("NO NPD!")
            exit(-1)


def get_cfile(files):
    cfiles = [file for file in files if file.split(".")[-1] == "c"]

    if len(cfiles) > 1:
        print("there are more than one cfile")
        exit(-1)

    return cfiles[0]


def main():
    print(f"number of param: {len(sys.argv)}")
    print(f"param list: {str(sys.argv)}")
    print(f"script name: {sys.argv[0]}")

    for i in range(1, len(sys.argv)):
        print(f"param {i} is: {sys.argv[i]}")

    if len(sys.argv) != 2:
        exit(-1)

    target_c_file = sys.argv[1]
    report_file = analyze_with_pinpoint(target_c_file)
    checkNpd(report_file)


if __name__ == "__main__":
    main()
