#!/usr/bin/python3
import argparse
import os
import re
import shlex
import subprocess
import time


CSMITH_HEADER = "/usr/include/csmith"

GCC_ANALYZER = "gcc -fanalyzer -fanalyzer-call-summaries -Wno-analyzer-double-fclose -Wno-analyzer-double-free -Wno-analyzer-exposure-through-output-file -Wno-analyzer-file-leak -Wno-analyzer-free-of-non-heap -Wno-analyzer-malloc-leak -Wno-analyzer-mismatching-deallocation -Wno-analyzer-null-argument -Wno-analyzer-possible-null-argument -Wno-analyzer-possible-null-dereference -Wno-analyzer-shift-count-negative -Wno-analyzer-shift-count-overflow -Wno-analyzer-stale-setjmp-buffer -Wno-analyzer-unsafe-call-within-signal-handler -Wno-analyzer-use-after-free -Wno-analyzer-use-of-pointer-in-stale-stack-frame -Wno-analyzer-use-of-uninitialized-value -Wno-analyzer-write-to-const -Wno-analyzer-write-to-string-literal -fdiagnostics-plain-output -fdiagnostics-format=text -msse4.2 "

CLANG_ANALYZER = " "

CLANG_OPTIONS = " "

REACHABLE_DIR = "reachable"
NPD_DISAPPEAR = "NPD_FLAG disappear"
UB_STRING = "Undefined behavior"


def fuzz_fp(args: argparse.Namespace):
    fuzzing_par_dir = args.path
    analyzer = args.analyzer
    opt = args.optimize
    thread_num = args.thread

    print("fuzz thread_num %s" % thread_num)

    iter_times = args.num
    script_path = "/home/working-space/scripts/fuzz_sa_fp.py"
    fuzzing_working_dir = create_fuzzing_place(
        fuzzing_par_dir, script_path, analyzer, str(opt), thread_num)

    os.chdir(fuzzing_working_dir)

    for i in range(0, thread_num):
        os.chdir('fuzz_%s' % i)
        subprocess.Popen(['python3', 'fuzz_sa_fp.py', analyzer, '-o='+str(opt),
                         str(iter_times)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.chdir("..")


def fuzz_fn(args: argparse.Namespace):
    fuzzing_par_dir = args.path
    analyzer = args.analyzer
    opt = args.optimize
    thread_num = args.thread

    print("fuzz thread_num %s" % thread_num)

    iter_times = args.num
    script_path = "/home/working-space/scripts/fuzz_sa_fn.py"
    fuzzing_working_dir = create_fuzzing_place(
        fuzzing_par_dir, script_path, analyzer, str(opt), thread_num)

    os.chdir(fuzzing_working_dir)

    for i in range(0, thread_num):
        os.chdir('fuzz_%s' % i)
        subprocess.Popen(['python3', 'fuzz_sa_fn.py', analyzer, '-o='+str(opt),
                         str(iter_times)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.chdir("..")

def fuzz_eval(args: argparse.Namespace):
    fuzzing_par_dir = args.path
    analyzer = args.analyzer
    opt = args.optimize
    thread_num = args.thread

    print("fuzz thread_num %s" % thread_num)
    iter_times = args.num
    script_path = "/home/working-space/scripts/fuzz_sa_eval.py"
    fuzzing_working_dir = create_fuzzing_place(
        fuzzing_par_dir, script_path, analyzer, str(opt), thread_num)
    
    os.chdir(fuzzing_working_dir)

    for i in range(0, thread_num):
        os.chdir('fuzz_%s' % i)
        subprocess.Popen(['python3', 'fuzz_sa_eval.py', analyzer, '-o='+str(opt),
                         str(iter_times)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.chdir("..")



def create(args: argparse.Namespace):
    # print("creat")

    fuzzing_par_dir = args.path
    num = args.num
    script_path = args.script
    analyzer = args.analyzer

    create_fuzzing_place(fuzzing_par_dir, script_path, analyzer, 'not', num)


def create_fuzzing_place(fuzzing_par_dir, script_path, analyzer, opt_level, dir_num):
    '''
    create $dir_num dirctories in fuzzing_par_dir
    and copy script_path to those dirs
    '''
    abs_par_path = os.path.abspath(fuzzing_par_dir)
    # print(abs_par_path)

    if not os.path.exists(script_path) or not os.path.isfile(script_path):
        print("%s does not exist or is not a file!" % script_path)
        exit(-1)

    abs_script_path = os.path.abspath(script_path)
    # print(abs_script_path)

    time_now = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())
    ret = subprocess.run([analyzer, '-dumpversion'],
                         stderr=subprocess.DEVNULL, stdout=subprocess.PIPE, encoding="utf-8")
    print(analyzer + ": " + ret.stdout.strip())
    abs_working_path = abs_par_path + '/' + analyzer + \
        '_' + ret.stdout.strip() + '_O' + opt_level + '_' + time_now

    if not os.path.exists(abs_working_path):
        os.makedirs(abs_working_path)
        # print("文件夹创建完成..." + abs_working_path)

    for i in range(dir_num):
        fuzz_i = abs_working_path + '/' + "fuzz_%s" % i

        if os.path.exists(fuzz_i):
            subprocess.run(['rm', '-rf', fuzz_i])
        os.mkdir(fuzz_i)

        subprocess.run(['cp', abs_script_path, fuzz_i])
        subprocess.run(['chmod', '+x', fuzz_i + '/' +
                       os.path.basename(abs_script_path)])

    print(abs_working_path)
    return abs_working_path


def get_short_name(full_name: str) -> str:
    '''
    input: abs_path
    return: basename without suffix
    '''
    basename = os.path.basename(full_name)
    name, *_ = basename.split(".")

    return name


def get_analyzer_version(analyzer):
    res = subprocess.run([analyzer, "-v"], stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, encoding="utf-8")

    return res.stdout


def analyze_with_gcc(optimization_level, cfile):
    '''
    use gcc to analyze Csmith-generated c program
    '''
    short_name = get_short_name(cfile)
    report_file = short_name + '.txt'
    object_file = short_name + '.o'

    print("analyze_with_gcc report: " + report_file)

    version = get_analyzer_version("gcc")
    print("gcc: version: \n" + version)
    gcc_analyzer_args_split = shlex.split(GCC_ANALYZER)

    if not os.path.exists(cfile):
        print("File does not exist! : " + cfile)
    else:
        ret = subprocess.run(gcc_analyzer_args_split + ["-O" + optimization_level, "-c", "-I", CSMITH_HEADER,
                             "-o", object_file, cfile], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")

        with open(report_file, "w") as f:
            f.write("gcc: version: " + version)
            f.write(ret.stdout)

        print("analyze_with_gcc return code: " + str(ret.returncode))

    return report_file


def process_gcc_report(report_file, args):
    '''
    check whether the given report contains the target CWE(NPD)
    '''
    # print("process_gcc_report")

    name = get_short_name(report_file)

    if not os.path.exists(report_file):
        print("report does not exist: " + str(report_file))
        clean_analyze_producets(args.saveReport, name)
        return

    with open(report_file, "r") as f:
        ret = subprocess.run(['grep', '\[CWE-476\]'], stdin=f,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
        print(ret)

    clean_analyze_producets(args.saveReport, name)

    if ret.returncode == 0:
        print("npd!")
        return True
    else:
        print("no npd!")
        return False


def clean_analyze_producets(saveFlag, name):
    if not saveFlag:
        ret = subprocess.run(["rm", "-f", name + '.o', name + '.txt'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
        # print("ret")


def check_one(args: argparse.Namespace):
    # print("check npd of one file")

    analyzer = args.analyzer
    record_npd_times = []

    if analyzer == "gcc":
        for i in range(args.num):
            report_file = analyze_with_gcc(str(args.optimize), args.file)
            npd_exist = process_gcc_report(report_file, args)
            if npd_exist:
                record_npd_times.append(i)
    # elif analyzer == "clang":
    #     pass
    # elif analyzer == "pp":
    #     pass

    print("recode_npd_times: ")
    print(record_npd_times)


def check_dir(args: argparse.Namespace):
    print("check npd of one dir: ")
    # TODO: handle args.num

    analyzer = args.analyzer
    target_dir = args.dir
    target_abspath = os.path.abspath(target_dir)
    dir_basename = os.path.basename(target_abspath)
    files = os.listdir(target_abspath)
    res = []

    if analyzer == "gcc":
        for file in files:
            if file.endswith(".c"):
                full_path = os.path.join(target_abspath, file)
                report_file = analyze_with_gcc(str(args.optimize), full_path)
                npd_exist = process_gcc_report(report_file, args)
                if npd_exist:
                    res.append(full_path)

    # elif analyzer == "clang":
    #     pass
    # elif analyzer == "pp":
    #     pass

    res.sort()

    print("\n npd_exist list: ")
    with open(dir_basename + "_npd_list.txt", "w") as f:
        f.write(analyzer + ": version: \n" + get_analyzer_version(analyzer))
        for i in res:
            print(i)
            f.write(i + "\n")


def check_npd(args: argparse.Namespace):
    # print("check npd")

    if args.file and args.dir:
        print('cannot give both "-file" and "-dir" options')
        exit(-1)

    if args.file:
        check_one(args)
    elif args.dir:
        check_dir(args)
    else:
        print("there is no target file/dir !")


def grep_npd(run_out_file):
    grep_ret = subprocess.run(["grep", "NPD_FLAG", run_out_file],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")

    if grep_ret.returncode == 0:
        print("reach NPD!")
        return True
    else:
        print("cannot reach NPD!")
        return False


def get_npd_lines(args: argparse.Namespace, report_abspath):
    npd_lines = []

    if args.analyzer == "gcc":
        with open(report_abspath, "r") as f:
            report_lines = f.readlines()

            for line in report_lines:
                if re.search("CWE-476", line):
                    npd_info = re.split(":", line)
                    # npd_info[1] is the npd report lineß
                    npd_lines.append(npd_info.pop(1))

            print(npd_lines)

    # elif args.analyzer == "clang":
    #     pass
    # else args.analyzer == "pp":
    #     pass

    return npd_lines


def instrument_cfile(cfile_abspath, npd_lines, instrumented_cfile):
    print("instrument_cfile: %s" % cfile_abspath)
    with open(cfile_abspath, "r") as f:
        cfile_lines = f.readlines()

        for num in npd_lines:
            c_num = int(num)-1
            print(c_num)
            print(cfile_lines[c_num])
            cfile_lines[c_num] = 'printf("NPD_FLAG\\n");' + cfile_lines[c_num]
            print(cfile_lines[c_num])

        with open(instrumented_cfile, "w") as f:
            f.writelines(cfile_lines)

    return instrumented_cfile


def compile_and_run_instrument_cfile(args, instrumented_cfile, run_out_file):
    try:
        compile_ret = subprocess.run([args.analyzer, "-O" + str(args.optimize), "-msse4.2", "-I", CSMITH_HEADER,
                                     instrumented_cfile], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, encoding="utf-8", check=True)
    except subprocess.CalledProcessError as e:
        print("compile error!")
        print(e)
        return False

    try:
        run_ret = subprocess.run(["timeout", "5s", "./a.out"], stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, encoding="utf-8", check=True)
    except subprocess.CalledProcessError as e:
        if e.returncode == 124:
            print("run timeout!")
        print(e)
        return False

    try:
        with open(run_out_file, "w") as f:
            f.write(args.analyzer + ": version: \n" +
                    get_analyzer_version(args.analyzer) + "\n")
            f.write(run_ret.stdout)
    except IOError:
        print("cannot write to %s !" % run_out_file)
        return False

    return True


def check_npd_line_reachable(args: argparse.Namespace):
    # print("check_npd_line_reachable")

    if args.cfile:
        print(args.cfile)
        check_cfile_npd_line_reachable(args)
    elif args.dir:
        print(args.dir)
        check_dir_npd_line_reachable(args)
    elif args.logfile:
        print(args.logfile)
        # TODO
        return
    elif args.file_list:
        print(args.file_list)
        # TODO
        return
    else:
        print("There is no such file/dir !")


def check_cfile_npd_line_reachable(args: argparse.Namespace):
    print("check whether cfile npd line reachable according to the corresponding analysis report")

    version = get_analyzer_version(args.analyzer)
    print(args.analyzer + ": version: \n" + version)

    # handle file path
    cfile_abspath = os.path.abspath(args.cfile)
    # print("cfile: " + cfile_abspath)
    par_dir, cfile = os.path.split(cfile_abspath)
    short_name = get_short_name(cfile)
    report_file = short_name + ".txt"
    report_abspath = os.path.join(par_dir, report_file)
    # print("report: " + report_abspath)
    instrumented_cfile = "instrument_" + short_name + ".c"
    run_out_file = "instrument_" + short_name + ".out"

    if not os.path.exists(report_abspath):
        print("report file does not exist!")
    else:
        print("report file exist!")
        npd_lines = get_npd_lines(args, report_abspath)
        instrumented_cfile = instrument_cfile(
            cfile_abspath, npd_lines, instrumented_cfile)
        res = compile_and_run_instrument_cfile(
            args, instrumented_cfile, run_out_file)
        npd_exist = False

        if res:
            npd_exist = grep_npd(run_out_file)
        else:
            print("compile_and_run_instrument_cfile fail!")

        clean_npd_check_input(args, cfile_abspath, report_abspath, npd_exist)
        clean_npd_check_output(args, instrumented_cfile,
                               run_out_file, npd_exist)


def clean_npd_check_input(args, cfile_abspath, report_abspath, npd_exist):
    if (not npd_exist and args.rmNonReachable) or args.rmAllReachable:
        ret = subprocess.run(['rm', "-f", cfile_abspath, report_abspath],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
        # print(ret)


def clean_npd_check_output(args, instrumented_cfile, run_out_file, npd_exist):
    if args.saveOutput or npd_exist:
        return

    subprocess.Popen(["rm", "-f", instrumented_cfile, run_out_file],
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")


def check_dir_npd_line_reachable(args: argparse.Namespace):
    # print("check_dir_npd_line_reachable")

    version = get_analyzer_version(args.analyzer)
    print(args.analyzer + ": version: \n" + version)

    # handle dir pathes
    target_dir_abspath = os.path.abspath(args.dir)
    # print(target_dir_abspath)
    os.chdir(target_dir_abspath)

    # create the reachable dir
    if not os.path.exists(REACHABLE_DIR):
        os.mkdir(REACHABLE_DIR)
    os.chdir(REACHABLE_DIR)

    files = os.listdir(target_dir_abspath)
    print("file nums: " + str(len(files)))

    res_reachable = []
    res_not_reachable = []
    res_report_not_exist = []
    res_compile_or_run_fail = []

    for file in files:
        if file.endswith(".c") and file.count("npd") != 0:
            # handle file pathes
            cfile = file
            cfile_abspath = os.path.join(target_dir_abspath, file)
            # print("cfile" + cfile_abspath)
            short_name = get_short_name(cfile)
            report_file = short_name + ".txt"
            report_abspath = os.path.join(target_dir_abspath, report_file)
            print("report: " + report_abspath)
            instrumented_cfile = "instrument_" + short_name + ".c"
            run_out_file = "instrument_" + short_name + ".out"

            if not os.path.exists(report_abspath):
                print("report file does not exist!")
                res_report_not_exist.append(cfile_abspath)
            else:
                print("report file exist!")
                npd_lines = get_npd_lines(args, report_abspath)
                instrumented_cfile = instrument_cfile(
                    cfile_abspath, npd_lines, instrumented_cfile)
                res = compile_and_run_instrument_cfile(
                    args, instrumented_cfile, run_out_file)
                npd_exist = False

                if res:
                    npd_exist = grep_npd(run_out_file)
                    if npd_exist:
                        res_reachable.append(cfile_abspath)
                    else:
                        res_not_reachable.append(cfile_abspath)
                else:
                    res_compile_or_run_fail.append(cfile_abspath)

                clean_npd_check_input(args, cfile_abspath,
                                      report_abspath, npd_exist)
                clean_npd_check_output(
                    args, instrumented_cfile, run_out_file, npd_exist)

    # write result to file
    res_reachable.sort()
    res_not_reachable.sort()
    res_report_not_exist.sort()
    res_compile_or_run_fail.sort()

    reachable_report = "npd_reachable_report_" + \
        str(time.strftime("%Y-%m-%d-%H-%M", time.localtime())) + ".txt"

    with open(reachable_report, "w") as f:
        f.write("%s: version: \n %s\n" %
                (args.analyzer, get_analyzer_version(args.analyzer)))

        f.write("\nnpd_reachable:\n")
        print("\nnpd_reachable:\n")

        for i in res_reachable:
            print(i)
            f.write(i + "\n")

        f.write("\nnpd_not_reachable:\n")
        print("\nnpd_not_reachable:\n")

        for i in res_not_reachable:
            print(i)
            f.write(i + "\n")

        f.write("\nres_report_not_exist:\n")
        print("\nres_report_not_exist:\n")

        for i in res_report_not_exist:
            print(i)
            f.write(i + "\n")

        f.write("\nres_compile_or_run_fail:\n")
        print("\nres_compile_or_run_fail:\n")

        for i in res_compile_or_run_fail:
            print(i)
            f.write(i + "\n")


def gen_reduce_script(template_abspath: str, cfile_name: str, opt_level: str, args: argparse.Namespace):
    # print("gen_reduce_script")

    with open(template_abspath, "r") as f:
        cfile_lines = f.readlines()

        # TODO: change the hard coding
        cfile_lines[4] = 'CFILE = "%s.c"\n' % cfile_name
        print(cfile_lines[4])
        
        cfile_lines[5] = 'OPT_LEVEL = "%s"\n' % opt_level
        print(cfile_lines[5])

        if args.script_path and args.cfile:
            script_abspath = os.path.abspath(args.script_path)
            if os.path.dirname(script_abspath):
                reduce_script = script_abspath
            else:
                print("path does not exist: " + args.script_path)
                return
        else:
            reduce_script = 'reduce_%s.py' % cfile_name

        with open(reduce_script, "w") as f:
            f.writelines(cfile_lines)

        print(reduce_script)
        subprocess.run(['chmod', '+x', reduce_script])
        return reduce_script


def gen_reduce(args: argparse.Namespace):
    # print("gen_reduce script")

    template_abspath = os.path.abspath(args.template)
    if not os.path.exists(template_abspath):
        print("template_abspath does not exist: " + template_abspath)
        exit(-1)

    analyzer = args.analyzer
    opt_level = str(args.optimize)

    if args.cfile:
        cfile_abspath = os.path.abspath(args.cfile)
        if not os.path.exists(cfile_abspath):
            print("cfile_path does not exist: " + cfile_abspath)
            exit(-1)

        cfile_name = get_short_name(cfile_abspath)
        gen_reduce_script(template_abspath, cfile_name, opt_level, args)

    elif args.dir:
        target_dir_abspath = os.path.abspath(args.dir)
        if not os.path.exists(target_dir_abspath):
            print("dir_path does not exist: " + target_dir_abspath)
            exit(-1)

        # handle dir path
        print(target_dir_abspath)
        os.chdir(target_dir_abspath)

        files = os.listdir(target_dir_abspath)
        print("file nums: " + str(len(files)))

        for file in files:
            if file.endswith(".c") and not file.startswith("instrument"):
                cfile_name = get_short_name(file)
                gen_reduce_script(
                    template_abspath, cfile_name, opt_level, args)
    else:
        target_dir_abspath = os.getcwd()
        files = os.listdir(target_dir_abspath)
        print("file nums: " + str(len(files)))

        for file in files:
            if file.endswith(".c"):
                cfile_name = get_short_name(file)
                gen_reduce_script(
                    template_abspath, cfile_name, opt_level, args)


def get_instrument_npd_serial_num(name):
    '''
    get serial num of given name
    example: input instrument_npd123.c ; retuen 123 ;
    '''
    res = re.search(r'instrument_npd(\w+)\..*', name)
    print(res)
    if res:
        return res.group(1)
    else:
        return None


def run_reduce_eval(args: argparse.Namespace):
    print("run reduce eval")
    thread_num = str(args.thread)
    analyzer = args.analyzer
    opt = str(args.opt)

    if args.file:
        file = args.file
        if file.startswith("reduce_eval"):
            print(file)
            serial_num = re.search(r'reduce_eval_(\w+)\..*', file).group(1)
            ret = subprocess.run(["./"+file, "eval_%s.c" % serial_num,
                                    "--n", thread_num], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            print(ret)
        return 


    if args.dir:
        targer_dir_abspath = os.path.abspath(args.dir)
        if not os.path.exists(targer_dir_abspath):
            print("dir_abspath does not exist: " + targer_dir_abspath)
            exit(-1)

        # handle dir pathes
        print(targer_dir_abspath)
        os.chdir(targer_dir_abspath)

        # result list
        reduced_list = []
        not_reduced_list = {}

        if not os.path.exists("reduce"):
            subprocess.run(["mkdir", "reduce"],
                           stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

        # handle every reducing script
        files = os.listdir(targer_dir_abspath)
        print("file num: " + str(len(files)))

        for file in files:
            if file.startswith("reduce_eval"):
                print(file)
                rfile = file
                serial_num = re.search(r'reduce_eval_(\w+)\..*', file).group(1)
                # print(serial_num)
                cfile = "eval_%s.c" % serial_num

                # if the reduce script does not return 0, then this cfile is useless
                ret = subprocess.run(["./"+rfile, cfile,
                                    "--n", thread_num], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                print("reduce script return code: %s" %ret.returncode)
                if ret.returncode != 0:
                    print(ret)
                    not_reduced_list[os.path.abspath(rfile)] = ret.returncode
                    ret = subprocess.run("rm instrument_eval_%s.c instrument_p_eval_%s.c instrument_eval_%s.log eval_%s.c reduce_eval_%s.py" % (
                                            serial_num, serial_num, serial_num, serial_num, serial_num), shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                    continue
                
                # reduce the cfile
                ret = subprocess.run(["creduce", rfile, "eval_%s.c" % serial_num,
                                     "--n", thread_num], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                reduced_list.append(os.path.abspath(cfile))
                print(ret)
                
                # move the reduced file and it's static analysis result to reduce/ dir
                ret = subprocess.run("/home/working-space/build-llvm-main/bin/tooling-sample %s eval_%s.c -- -I /usr/include/csmith/ > instrument_eval_%s.c"%(analyzer, serial_num,serial_num), 
                    shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                print(ret)

                if analyzer == "gcc":
                    ret = subprocess.run("gcc -fanalyzer -O%s -I /usr/include/csmith/ instrument_eval_%s.c &> instrument_eval_%s.log"%(opt, serial_num, serial_num), 
                    shell=True)
                    print(ret)

                elif analyzer == "clang":
                    pass


                ret = subprocess.run("mv instrument_eval_%s.c instrument_eval_%s.log eval_%s.c reduce/" % (
                    serial_num, serial_num, serial_num), shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                print(ret)

                print("finish!")
                subprocess.run("rm -rf instrument_eval_%s.o" % serial_num,
                               shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                subprocess.run("rm -rf /tmp/instrument_eval_%s*" % serial_num,
                               shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                subprocess.run("rm -rf /tmp/compcert*",
                               shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)


    os.chdir("reduce")
    reduced_list.sort()

    with open("reduce_result-%s.txt" % str(time.strftime("%Y-%m-%d-%H-%M", time.localtime())), "w") as f:
        
        f.write("\nReduced files:\n")
        for i in reduced_list:
            f.write(i + "\n")

        f.write("\n\nNot Reduced files:\n")
        for i in not_reduced_list:
            f.write(i + ": " + str(not_reduced_list[i]) + "\n")



def run_reduce(args: argparse.Namespace):
    '''
    run every reduce script in the given dir
    if the intended reduce file has Undefine behavior, then delete it
    else reduce it
    '''
    print("run reduce")
    thread_num = str(args.thread)

    if args.dir:
        targer_dir_abspath = os.path.abspath(args.dir)
        if not os.path.exists(targer_dir_abspath):
            print("dir_abspath does not exist: " + targer_dir_abspath)
            exit(-1)

        # handle dir pathes
        print(targer_dir_abspath)
        os.chdir(targer_dir_abspath)

        # result list
        ub_list = []
        npd_disappear_list = []
        reduce_list = []

        if not os.path.exists("reduce"):
            subprocess.run(["mkdir", "reduce"],
                           stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

        # handle every reducing script
        files = os.listdir(targer_dir_abspath)
        print("file num: " + str(len(files)))

        for file in files:
            if file.endswith(".py"):
                print(file)
                serial_num = get_instrument_npd_serial_num(file)
                print(serial_num)
                res = subprocess.run(
                    ["./" + file], stderr=subprocess.DEVNULL, stdout=subprocess.PIPE, encoding="utf-8")

                # if the intended reduce file has Undefine behavior, then delete it
                if res.stdout.count(UB_STRING) != 0:
                    print(UB_STRING)
                    ub_list.append(os.path.abspath(file))
                    ret = subprocess.run("rm -f *instrument_npd%s*" % serial_num,
                                         shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                    # print(ret)
                    continue

                elif res.stdout.count(NPD_DISAPPEAR) != 0:
                    print(NPD_DISAPPEAR)
                    npd_disappear_list.append(os.path.abspath(file))
                    ret = subprocess.run("mv *instrument_npd%s reduce/" % serial_num,
                                         shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                    continue

                ret = subprocess.run(["creduce", file, "instrument_npd%s.c" % serial_num,
                                     "--n", thread_num], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                reduce_list.append(os.path.abspath(file))
                print(ret)
                ret = subprocess.run("mv instrument_npd%s.c* instrument_npd%s.out reduce_instrument_npd%s.py reduce/" % (
                    serial_num, serial_num, serial_num), shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                print(ret)

                print("finish!")
                subprocess.run("rm -rf /tmp/instrument_npd%s*" % serial_num,
                               shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                subprocess.run("rm -rf /tmp/compcert*",
                               shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

    os.chdir("reduce")
    ub_list.sort()
    reduce_list.sort()

    with open("reduce_result-%s.txt" % str(time.strftime("%Y-%m-%d-%H-%M", time.localtime())), "w") as f:
        f.write("Undefined behavior:\n")
        for i in ub_list:
            f.write(i + "\n")
        f.write("\nReduced files:\n")
        for i in reduce_list:
            f.write(i + "\n")



def do_preprocess(abs_file_path, analyzer):
    subprocess.run("/home/working-space/build-llvm-main/bin/cfe_preprocess %s -- -I /usr/include/csmith "%abs_file_path,
                               stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, shell=True, check=True)

    new_lines = []
    with open(abs_file_path, "r") as f:
        lines = f.readlines()
        if analyzer == "gcc":
            new_lines.append("#include <stdbool.h>\n")
            new_lines.append("void __analyzer_eval(int a){}\n")
        elif analyzer == "clang":
            new_lines.append("#include <stdbool.h>\n")
            new_lines.append("void clang_analyzer_eval(int a){}\n")

        for line in lines:
            new_lines.append(line)
    with open(abs_file_path, "w") as f:
        f.writelines(new_lines)   

    short_name = get_short_name(abs_file_path)
    pat_path, _ = os.path.split(abs_file_path)

    if analyzer == "gcc":
        subprocess.run("/home/working-space/build-llvm-main/bin/tooling-sample --analyzer=gcc %s -- -I /usr/include/csmith > %s"%(abs_file_path,pat_path+ "/instru_" + short_name + ".c"),
                               stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, shell=True , check=True )
    elif analyzer == "clang":
        subprocess.run("/home/working-space/build-llvm-main/bin/tooling-sample --analyzer=clang %s -- -I /usr/include/csmith > %s"%(abs_file_path,pat_path+ "/instru_" + short_name + ".c"),
                               stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, shell=True , check=True )



def preprocess(args: argparse.Namespace):
    '''
    add include head to csmith-generated program
    '''
    if args.file:
        print(args.file)
        abs_file_path = os.path.abspath(args.file)
        do_preprocess(abs_file_path, args.analyzer)
        
    elif args.dir:
        print(args.dir)



def handle_args():
    parser = argparse.ArgumentParser(
        description="tools for testing static analyzer")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true")
    group.add_argument("-q", "--quiet", action="store_true")

    subparsers = parser.add_subparsers(help='sub-command help')

    # add subcommand preprocess
    parser_preprocess = subparsers.add_parser(
        "preprocess", help="preprocess a program")
    parser_preprocess.add_argument("analyzer", type=str, choices={
        'gcc', 'clang'}, help="give a analyzer")
    group_preprocess = parser_preprocess.add_mutually_exclusive_group()
    group_preprocess.add_argument("-f", "--file", type=str, help="target file")
    group_preprocess.add_argument(
        "-d", "--dir", type=str, help="give a directory")

    parser_preprocess.set_defaults(func=preprocess)



    # add subcommand gen-reduce
    parser_gen_reduce = subparsers.add_parser(
        "gen-reduce", help="generate reduce script")
    parser_gen_reduce.add_argument(
        "template", type=str, help="specify reduce template")
    parser_gen_reduce.add_argument("analyzer", type=str, choices={
        'gcc', 'clang'}, help="give a analyzer")
    parser_gen_reduce.add_argument("optimize", type=int, choices={
                                   0, 1, 2, 3}, help="optimization level")
    parser_gen_reduce.add_argument(
        "-t", "--script_path", type=str, help="specify script path")

    group_parser_gen_reduce = parser_gen_reduce.add_mutually_exclusive_group()
    group_parser_gen_reduce.add_argument(
        "-f", "--cfile", type=str, help="specify cfile")
    group_parser_gen_reduce.add_argument(
        "-d", "--dir", type=str, help="give a directory")

    parser_gen_reduce.set_defaults(func=gen_reduce)

    # add subcommand run-reduce
    parser_run_reduce = subparsers.add_parser(
        "run-reduce", help="run reduce script")
    parser_run_reduce.add_argument("dir", type=str, help="give a directory")
    parser_run_reduce.add_argument(
        "thread", type=int, default=0, help="specify the thread num for reducing")

    parser_run_reduce.set_defaults(func=run_reduce)


    # add subcommand run-reduce-eval
    parser_run_reduce_eval = subparsers.add_parser(
        "run-reduce-eval", help="run reduce-eval script")
    parser_run_reduce_eval.add_argument("-d","--dir", type=str, help="give a directory")
    parser_run_reduce_eval.add_argument("-f","--file", type=str, help="give a file")
    parser_run_reduce_eval.add_argument(
        "thread", type=int, default=0, help="specify the thread num for reducing")
    parser_run_reduce_eval.add_argument("analyzer", type=str, choices={
        'gcc', 'clang'}, help="give a analyzer")
    parser_run_reduce_eval.add_argument("opt", type=int, choices={
                                   0, 1, 2, 3}, help="optimization level")

    parser_run_reduce_eval.set_defaults(func=run_reduce_eval)

    # add subcommand fuzz-fp
    parser_fuzz = subparsers.add_parser(
        "fuzz-fp", help="fuzzing static analyzer in a given dir")
    parser_fuzz.add_argument(
        "path", help="given a parent dir of fuzzing working dir")
    parser_fuzz.add_argument("analyzer", type=str, choices={
        'gcc', 'clang'}, help="give a analyzer")
    parser_fuzz.add_argument("optimize", type=int, choices={
        0, 1, 2, 3}, default=0, help="optimization level")
    parser_fuzz.add_argument(
        "thread", type=int, default=1, help="specify the thread num for fuzzing")
    parser_fuzz.add_argument(
        "num", type=int, default=1, help="the iteration times of fuzzing")

    parser_fuzz.set_defaults(func=fuzz_fp)

    # add subcommand fuzz-fn
    parser_fuzz = subparsers.add_parser(
        "fuzz-fn", help="fuzzing static analyzer in a given dir")
    parser_fuzz.add_argument(
        "path", help="given a parent dir of fuzzing working dir")
    parser_fuzz.add_argument("analyzer", type=str, choices={
        'gcc', 'clang'}, help="give a analyzer")
    parser_fuzz.add_argument("optimize", type=int, choices={
        0, 1, 2, 3}, default=0, help="optimization level")
    parser_fuzz.add_argument(
        "thread", type=int, default=1, help="specify the thread num for fuzzing")
    parser_fuzz.add_argument(
        "num", type=int, default=1, help="the iteration times of fuzzing")

    parser_fuzz.set_defaults(func=fuzz_fn)

     # add subcommand fuzz-eval
    parser_fuzz = subparsers.add_parser(
        "fuzz-eval", help="fuzzing static analyzer in a given dir")
    parser_fuzz.add_argument(
        "path", help="given a parent dir of fuzzing working dir")
    parser_fuzz.add_argument("analyzer", type=str, choices={
        'gcc', 'clang'}, help="give a analyzer")
    parser_fuzz.add_argument("optimize", type=int, choices={
        0, 1, 2, 3}, default=0, help="optimization level")
    parser_fuzz.add_argument(
        "thread", type=int, default=1, help="specify the thread num for fuzzing")
    parser_fuzz.add_argument(
        "num", type=int, default=1, help="the iteration times of fuzzing")

    parser_fuzz.set_defaults(func=fuzz_eval)


    # add subcommand create fuzzing working dir
    parser_create = subparsers.add_parser(
        "create", help="create fuzzing working dir")
    parser_create.add_argument("script", help="give a fuzzing script")
    parser_create.add_argument(
        "path", help="give a parent dir of fuzzing working dir")
    parser_create.add_argument("analyzer", type=str, choices={
                               'gcc', 'clang'}, help="give a analyzer")
    parser_create.add_argument(
        "-n", "--num", type=int, required=True, help="the number of fuzzing")

    parser_create.set_defaults(func=create)

    # add subcommand find


    # add subcommand checknpd
    parser_checknpd = subparsers.add_parser(
        "check-npd", help="check whether the given analyzer complain npd of the given c program (discarded)")
    parser_checknpd.add_argument("analyzer", type=str, choices={
                                 'gcc', 'clang'}, help="give a analyzer")
    parser_checknpd.add_argument("-o", "--optimize", type=int,
                                 choices={0, 1, 2, 3}, default=0, help="optimization level")
    parser_checknpd.add_argument(
        "-n", "--num", type=int, default=1, help="the times of checked for each file")
    parser_checknpd.add_argument("-s", "--saveReport", action="store_true",
                                 help="do not delete generated files in analyzing process")

    group_checknpd = parser_checknpd.add_mutually_exclusive_group()
    group_checknpd.add_argument("-f", "--file", type=str, help="give a c file")
    group_checknpd.add_argument(
        "-d", "--dir", type=str, help="give a directory")

    parser_checknpd.set_defaults(func=check_npd)

    # add subcommand reach-npd
    parser_reach_npd_lines = subparsers.add_parser(
        "reach-npd", help="check whether the npd line complained by the given analyzer is reahable （discarded）")
    parser_reach_npd_lines.add_argument("analyzer", type=str, choices={
                                        'gcc', 'clang'}, help="give a analyzer")
    parser_reach_npd_lines.add_argument(
        "-o", "--optimize", type=int, choices={0, 1, 2, 3}, default=0, help="optimization level")
    parser_reach_npd_lines.add_argument(
        "-s", "--saveOutput", action="store_true", help="do not delete generated files in checking process")

    group_rm_reach_npd_lines = parser_reach_npd_lines.add_mutually_exclusive_group()
    group_rm_reach_npd_lines.add_argument(
        "-mn", "--rmNonReachable", action="store_true", help="remove non-npd-line-reachable test c files")
    group_rm_reach_npd_lines.add_argument(
        "-ma", "--rmAllReachable", action="store_true", help="remove all-npd-line-reachable test c files")

    group_reach_npd_lines = parser_reach_npd_lines.add_mutually_exclusive_group()
    group_reach_npd_lines.add_argument(
        "-cf", "--cfile", type=str, help="give a cfile")
    group_reach_npd_lines.add_argument(
        "-d", "--dir", type=str, help="give a directory")
    group_reach_npd_lines.add_argument(
        "-lf", "--file_list", type=str, help="give a cfile list")
    group_reach_npd_lines.add_argument(
        "-gf", "--logfile", type=str, help="give a log file of analyzing c programs")

    parser_reach_npd_lines.set_defaults(func=check_npd_line_reachable)

    args = parser.parse_args()
    # print(args)
    return args


def main():
    args = handle_args()
    args.func(args)


if __name__ == "__main__":
    main()
