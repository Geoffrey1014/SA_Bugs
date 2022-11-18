#!/usr/bin/python3

import argparse
import os


def handle_args():
    """
    handle command line args
    """
    parser = argparse.ArgumentParser(
        description="creduce case where false negative related null ptr dereference exists")
    parser.add_argument(
        "sa", type=str, help="choose a static analyzer [clang, gcc]")
    parser.add_argument(
        "start", type=int, help="choose number of cases to be reduced")
    parser.add_argument(
        "end", type=int, help="choose number of cases to be reduced")

    args = parser.parse_args()
    return args


def main():
    args = handle_args()
    for i in range(args.start, args.end):
        rfile = "reduce_case_{}.py".format(i)
        tfile = "interestness_template_{}.py".format(args.sa)
        cfile = "case_{}.c".format(i)

        os.system("cp {} {}".format(tfile, rfile))
        os.system("chmod +x {}".format(rfile))

        with open(rfile, "r") as f:
            lines = ""
            for line in f.readlines():
                if "example.c" in line:
                    line = line.replace("example.c", cfile)
                lines += line

            with open(rfile, "w") as f:
                f.writelines(lines)

        os.system(
            "nohup creduce {} {} > out_case_{}.txt 2>&1 &".format(rfile, cfile, i))


if __name__ == "__main__":
    main()
