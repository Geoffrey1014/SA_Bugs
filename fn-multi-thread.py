#!/usr/bin/python3

import argparse
import os
import subprocess
import time


def handle_args():
    """
    handle command line args
    """
    parser = argparse.ArgumentParser(
        description="fuzz static analyzers for false negative related null ptr dereference")
    parser.add_argument(
        "num_t", type=int, help="choose number of threads of fuzzing")
    parser.add_argument(
        "num_c", type=int, help="choose number of cases under each thread")

    args = parser.parse_args()
    return args


def create_fuzz_place(fuzz_par_dir, script_path, thread_num):
    """
    create $thread_num dir in fuzz_par_dir and
    copy script_path to those dirs
    """
    abs_par_path = os.path.abspath(fuzz_par_dir)
    abs_script_path = os.path.abspath(script_path)
    abs_working_path = abs_par_path + "/" + \
        time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())

    os.makedirs(abs_working_path)

    for i in range(thread_num):
        fuzz_i = abs_working_path + "/" + "fuzz_{}".format(i)
        os.makedirs(fuzz_i)

        subprocess.run(["mkdir", fuzz_i + "/" + "fn_csa"])
        subprocess.run(["mkdir", fuzz_i + "/" + "fn_gsa"])
        subprocess.run(["mkdir", fuzz_i + "/" + "fail_csa"])
        subprocess.run(["mkdir", fuzz_i + "/" + "fail_gsa"])

        subprocess.run(["cp", abs_script_path, fuzz_i])
        subprocess.run(["chmod", "+x", fuzz_i + "/" +
                       os.path.basename(abs_script_path)])

    return abs_working_path


def main():
    args = handle_args()
    num_t = args.num_t
    num_c = args.num_c

    fuzz_place = create_fuzz_place(".", "fuzz_sa_fn.py", num_t)
    os.chdir(fuzz_place)

    for i in range(num_t):
        os.chdir("fuzz_{}".format(i))
        subprocess.Popen(["python3", "fuzz_sa_fn.py", str(num_t), str(num_c)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.chdir("..")


if __name__ == "__main__":
    main()
