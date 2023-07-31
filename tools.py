#!/usr/bin/python3
import argparse
import os
import re
import shlex
import subprocess
import time
from myutils import *
from config import *

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = ROOT_DIR + "/config.py"
MYUTILS_FILE = ROOT_DIR + "/myutils.py"

REACHABLE_DIR = "reachable"

def fuzz_fp(args: argparse.Namespace):
    script_path = ROOT_DIR + "/fuzz_sa_fp.py"

    fuzzing_par_dir = args.path
    opt = args.optimize
    thread_num = args.thread
    analyzer = args.analyzer
    iter_times = args.num
    print("fuzz-fp thread_num %s" % thread_num)
    
    fuzzing_working_dir = create_fuzzing_place(
        fuzzing_par_dir, script_path, analyzer, str(opt), thread_num)

    os.chdir(fuzzing_working_dir)

    for i in range(0, thread_num):
        os.chdir('fuzz_%s' % i)
        subprocess.Popen(['python3', 'fuzz_sa_fp.py', analyzer, args.checker,
                         str(iter_times),'-o='+str(opt)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.chdir("..")

def fuzz_fn(args: argparse.Namespace):
    script_path = ROOT_DIR + "/fuzz_sa_fn.py"

    fuzzing_par_dir = args.path
    analyzer = args.analyzer
    opt = args.optimize
    thread_num = args.thread
    iter_times = args.num
    print("fuzz-fn thread_num %s" % thread_num)
    
    fuzzing_working_dir = create_fuzzing_place(
        fuzzing_par_dir, script_path, analyzer, str(opt), thread_num)

    os.chdir(fuzzing_working_dir)

    for i in range(0, thread_num):
        os.chdir('fuzz_%s' % i)
        subprocess.Popen(['python3', 'fuzz_sa_fn.py', analyzer, '-o='+str(opt),
                         str(iter_times)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.chdir("..")

def fuzz_eval(args: argparse.Namespace):
    script_path = ROOT_DIR + "/fuzz_sa_eval.py"

    fuzzing_par_dir = args.path
    analyzer = args.analyzer
    opt = args.optimize
    thread_num = args.thread
    iter_times = args.num
    print("fuzz-eval thread_num %s" % thread_num)
    
    fuzzing_working_dir = create_fuzzing_place(
        fuzzing_par_dir, script_path, analyzer, str(opt), thread_num)
    
    os.chdir(fuzzing_working_dir)

    for i in range(0, thread_num):
        os.chdir('fuzz_%s' % i)
        subprocess.Popen(['python3', 'fuzz_sa_eval.py', analyzer, '-o='+str(opt),
                         str(iter_times)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.chdir("..")

def create(args: argparse.Namespace):
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
    print("create_fuzzing_place")
    abs_par_path = os.path.abspath(fuzzing_par_dir)

    if not os.path.exists(script_path) or not os.path.isfile(script_path):
        print("%s does not exist or is not a file!" % script_path)
        exit(-1)

    abs_script_path = os.path.abspath(script_path)

    time_now = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())

    if analyzer == "gcc":
        cc = GCC
    elif analyzer == "clang":
        cc = CLANG
    try:
        ret = subprocess.run([cc, '-dumpversion'],
                             stderr=subprocess.DEVNULL, stdout=subprocess.PIPE, encoding="utf-8", check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        exit(1)
    
    abs_working_path = abs_par_path + '/' + analyzer + \
        '_' + ret.stdout.strip() + '_O' + opt_level + '_' + time_now

    if not os.path.exists(abs_working_path):
        os.makedirs(abs_working_path)

    for i in range(dir_num):
        fuzz_i = abs_working_path + '/' + "fuzz_%s" % i

        if os.path.exists(fuzz_i):
            subprocess.run(['rm', '-rf', fuzz_i])
        os.mkdir(fuzz_i)

        subprocess.run(['cp', abs_script_path,CONFIG_FILE,MYUTILS_FILE, fuzz_i])
        subprocess.run(['chmod', '+x', fuzz_i + '/' + os.path.basename(abs_script_path)])

    print(abs_working_path)
    return abs_working_path



def analyze_with_gcc(optimization_level, cfile):
    '''
    use gcc to analyze csmith-generated c program
    '''
    short_name = get_short_name(cfile)
    report_file = short_name + '.txt'
    object_file = short_name + '.o'

    print("analyze_with_gcc report: " + report_file)

    version = get_analyzer_version("gcc")
    print("gcc: version: \n" + version)
    gcc_analyzer_args_split = shlex.split(GCC_ANALYZER)

    if not os.path.exists(cfile):
        print("file does not exist! : " + cfile)
    else:
        ret = subprocess.run(gcc_analyzer_args_split + ["-O" + optimization_level, "-c", "-I", CSMITH_HEADER,
                             "-o", object_file, cfile], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
        print(ret)

        with open(report_file, "w") as f:
            f.write("gcc: version: " + version)
            f.write(ret.stdout)

        print("analyze_with_gcc return code: " + str(ret.returncode))

    return report_file


def analyze_with_clang(cfile):
    '''
    use clang to analyze csmith-generated c program
    '''
    short_name = get_short_name(cfile)
    report_file = short_name + '.txt'
    object_file = short_name + '.o'

    print("analyze_with_clang report: " + report_file)

    version = get_analyzer_version("clang")
    print("clang: version: \n" + version)
    clang_analyzer_args_split = shlex.split(CLANG_ANALYZER)

    if not os.path.exists("report_html"):
        ret = os.system("mkdir report_html")
        if ret != 0:
            print("fail to mkdir report_html")
            exit(ret >> 8)

    report_html = "report_html"

    if not os.path.exists(cfile):
        print("file does not exist! : " + cfile)
    else:
        ret = subprocess.run(clang_analyzer_args_split + ["-o", report_html, "clang", CLANG_OPTIONS, "-c", "-I", CSMITH_HEADER, "-o", object_file,
                             cfile], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
        # print(ret)

        with open(report_file, "w") as f:
            f.write("clang: version: " + version)
            f.write(ret.stdout)

        print("analyze_with_clang return code: " + str(ret.returncode))

    return report_file


def process_gcc_report(report_file, args):
    '''
    check whether the given report contains the target CWE(NPD)
    '''
    name = get_short_name(report_file)

    if not os.path.exists(report_file):
        print("report does not exist: " + str(report_file))
        clean_analyze_producets(args.saveReport, name)
        return None

    with open(report_file, "r") as f:
        ret = subprocess.run(['grep', '\[CWE\-476\]'], stdin=f,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
        print(ret)

    clean_analyze_producets(args.saveReport, name)

    if ret.returncode == 0:
        print("npd!")
        return True
    else:
        print("no npd!")
        return False


def process_clang_report(report_file, args):
    '''
    check whether the given report contains the target CWE(NPD)
    '''
    name = get_short_name(report_file)

    if not os.path.exists(report_file):
        print("report does not exist: " + str(report_file))
        clean_analyze_producets(args.saveReport, name)
        return None

    with open(report_file, "r") as f:
        ret = subprocess.run(['grep', '\[core\.NullDereference\]'], stdin=f,
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


def check_one(args: argparse.Namespace):
    analyzer = args.analyzer
    record_npd_times = []

    if analyzer == "gcc":
        for i in range(args.num):
            report_file = analyze_with_gcc(str(args.optimize), args.file)
            npd_exist = process_gcc_report(report_file, args)
            if npd_exist:
                record_npd_times.append(i)

    elif analyzer == "clang":
        for i in range(args.num):
            report_file = analyze_with_clang(args.file)
            npd_exist = process_clang_report(report_file, args)
            if npd_exist:
                record_npd_times.append(i)

    elif analyzer == "pp":
        pass

    print("recode_npd_times: ")
    print(record_npd_times)


def check_dir(args: argparse.Namespace):
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

    elif analyzer == "clang":
        for file in files:
            if file.endswith(".c"):
                full_path = os.path.join(target_abspath, file)
                report_file = analyze_with_clang(full_path)
                npd_exist = process_clang_report(report_file, args)
                if npd_exist:
                    res.append(full_path)

    elif analyzer == "pp":
        pass

    res.sort()

    print("\n npd_exist list: ")
    with open(dir_basename + "_npd_list.txt", "w") as f:
        f.write(analyzer + ": version: \n" + get_analyzer_version(analyzer))
        for i in res:
            print(i)
            f.write(i + "\n")


def check_fp(args: argparse.Namespace):
    if args.file:
        check_one(args)
    elif args.dir:
        check_dir(args)
    else:
        print("there is no target file/dir !")
        exit(-1)


def check_reachable(args: argparse.Namespace):
    if args.cfile and os.path.exists(args.cfile):
        print(args.cfile)
        if check_cfile_warning_line_reachable(args):
            print("warning line reachable!")
        else:
            print("warning line not reachable!")
    elif args.dir and os.path.exists(args.dir):
        print(args.dir)
        check_dir_warning_line_reachable(args)
    else:
        print("please make sure the given file/dir exist!")
        exit(-1)


def check_cfile_warning_line_reachable(args: argparse.Namespace):
    print("check whether the warning line reachable")
    cc = get_compiler(args.analyzer)
    if args.verbose:
        version = get_analyzer_version(cc)
        print(args.analyzer + ": version: \n" + version)

    # handle cfile path
    cfile_abspath = os.path.abspath(args.cfile)
    par_dir, cfile = os.path.split(cfile_abspath)

    os.chdir(par_dir)

    # handle report_file path
    short_name = get_short_name(cfile)
    report_file = short_name + ".txt"
    report_abspath = os.path.join(par_dir, report_file)

    instrumented_cfile = "instrument_" + short_name + ".c"
    run_out_file = "instrument_" + short_name + ".out"
    warning_exist = False

    if not os.path.exists(report_abspath):
        #TODO: analyze the cfile and get the report
        print("report file does not exist!")
        exit(-1)
    else:
        warning_lines = get_warning_lines(args.analyzer,args.checker, report_abspath)
        if len(warning_lines) != 0:
            if instrument_cfile(cfile_abspath, warning_lines, instrumented_cfile):
                if compile_and_run_instrument_cfile(cc, str(args.optimize),instrumented_cfile, run_out_file):
                    warning_exist = grep_flag(run_out_file)
                else:
                    print("compile_and_run_instrument_cfile fail!")
                clean_check_reach_output(args.saveOutput, instrumented_cfile, run_out_file, warning_exist)
        clean_check_reach_input(args.rmNonReachable, args.rmAllReachable, cfile_abspath, report_abspath, warning_exist)
        return warning_exist



def check_dir_warning_line_reachable(args: argparse.Namespace):
    cc = get_compiler(args.analyzer)
    warning_type = args.checker
    if args.verbose:
        version = get_analyzer_version(args.analyzer)
        print(args.analyzer + ": version: \n" + version)

    # handle dir pathes
    target_dir_abspath = os.path.abspath(args.dir)
    os.chdir(target_dir_abspath)

    files = os.listdir(target_dir_abspath)
    print("file nums: " + str(len(files)))

    # create the reachable dir
    if not os.path.exists(REACHABLE_DIR):
        os.mkdir(REACHABLE_DIR)
    os.chdir(REACHABLE_DIR)


    res_reachable = []
    res_not_reachable = []
    res_report_not_exist = []
    res_compile_or_run_fail = []

    for file in files:
        if file.endswith(".c") and file.startswith(warning_type):
            # handle file pathes
            if args.verbose:
                print("handling file: " + file)
            cfile = file
            cfile_abspath = os.path.join(target_dir_abspath, file)
            short_name = get_short_name(cfile)
            report_file = short_name + ".txt"
            report_abspath = os.path.join(target_dir_abspath, report_file)
            instrumented_cfile = "instrument_" + short_name + ".c"
            run_out_file = "instrument_" + short_name + ".out"
            warning_exist = False

            if not os.path.exists(report_abspath):
                if args.verbose:
                    print("report file does not exist!")
                res_report_not_exist.append(cfile_abspath)
            else:
                warning_lines = get_warning_lines(args.analyzer,args.checker, report_abspath)
                if len(warning_lines) != 0:
                    if instrument_cfile(cfile_abspath, warning_lines, instrumented_cfile):
                        if compile_and_run_instrument_cfile(cc, str(args.optimize),instrumented_cfile, run_out_file):
                            warning_exist = grep_flag(run_out_file)
                            if warning_exist:
                                res_reachable.append(cfile_abspath)
                            else:
                                res_not_reachable.append(cfile_abspath)
                        else:
                            res_compile_or_run_fail.append(cfile_abspath)
                        clean_check_reach_output(args.saveOutput, instrumented_cfile, run_out_file, warning_exist)
            clean_check_reach_input(args.rmNonReachable, args.rmAllReachable, cfile_abspath, report_abspath, warning_exist)

    write_result_to_file(res_reachable, res_not_reachable, res_report_not_exist, res_compile_or_run_fail, args.analyzer, warning_type)
    


def gen_reduce(args: argparse.Namespace):
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
        par_dir, _ = os.path.split(cfile_abspath)
        os.chdir(par_dir)
        shutil.copy(CONFIG_FILE, "config.py")

        reduce_script = gen_reduce_script(template_abspath, get_short_name(cfile_abspath), opt_level, args.checker)
        if not reduce_script:
            print("gen_reduce_script fail!")
            exit(-1)

    elif args.dir:
        target_dir_abspath = os.path.abspath(args.dir)
        if not os.path.exists(target_dir_abspath):
            print("dir_path does not exist: " + target_dir_abspath)
            exit(-1)

        # handle dir path
        print(target_dir_abspath)
        os.chdir(target_dir_abspath)
        shutil.copy(CONFIG_FILE, "config.py")

        files = os.listdir(target_dir_abspath)
        print("file nums: " + str(len(files)))

        for file in files:
            if file.endswith(".c") and file.startswith("instrument"):
                reduce_script = gen_reduce_script(
                    template_abspath, get_short_name(file), opt_level, args.checker)
                if not reduce_script:
                    print("gen_reduce_script fail!")
        print("gen reduce script done!")
    else:
        print("Please give a cfile of a dir !")
        exit(-1)



# 需要重写
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
    if the intended reduce file has undefine behavior
    then delete it, else reduce it
    '''
    thread_num = str(args.thread)
    targer_dir_abspath = os.path.abspath(args.dir)
    if not os.path.exists(targer_dir_abspath):
        print("dir_abspath does not exist: " + targer_dir_abspath)
        exit(-1)

    # handle dir pathe
    print(targer_dir_abspath)
    os.chdir(targer_dir_abspath)

    # result list
    ub_list = []
    flag_disappear_list = []
    other_error_list = []
    reduce_list = []

    if not os.path.exists("reduce"):
        os.mkdir("reduce")
        
    # handle every reducing script
    files = os.listdir(targer_dir_abspath)
    print("file num: " + str(len(files)))

    for cfile in files:
        if cfile.endswith(".c") and cfile.startswith("instrument"):
            print(cfile)
            short_name = get_short_name(cfile)
            reduce_script = 'reduce_%s.py' % short_name

            # if the reduce script does not return 0, then this cfile is useless
            res = subprocess.run(
                ["./" + reduce_script], stderr=subprocess.DEVNULL, stdout=subprocess.PIPE, encoding="utf-8")

            # if the intended reduce file has undefine behavior, then delete it
            if res.stdout.count(UB_STR) != 0:
                print(UB_STR)
                ub_list.append(os.path.abspath(reduce_script))
                os.system("rm -rf %s %s %s.o" % (cfile, reduce_script, short_name))
                continue
            elif res.stdout.count(FLAG_DIS_STR) != 0:
                print(FLAG_DIS_STR)
                flag_disappear_list.append(os.path.abspath(reduce_script))
                os.system("rm -rf %s %s %s.o" % (cfile, reduce_script, short_name))
                continue
            elif res.returncode != 0:
                print(res.stdout)
                other_error_list.append(os.path.abspath(reduce_script))
                os.system("rm -rf %s %s %s.o" % (cfile, reduce_script, short_name))
                continue

            ret = subprocess.run(["creduce", cfile, reduce_script,
                                    "--n", thread_num], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

            if ret.returncode == 0:
                reduce_list.append(os.path.abspath(cfile))
                os.system("mv %s %s %s.out reduce/" % (cfile, reduce_script, short_name))
                os.remove(short_name+".o")

            subprocess.run("rm -rf /tmp/%s*" % short_name,
                            shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            subprocess.run("rm -rf /tmp/compcert*",
                            shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

    os.chdir("reduce")
    ub_list.sort()
    reduce_list.sort()
    wirte_reduce_result(reduce_list, ub_list, flag_disappear_list, other_error_list)    




def do_preprocess(abs_file_path, analyzer):
    subprocess.run("%s %s -- -I %s "% (CFE, abs_file_path, CSMITH_HEADER),
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
        subprocess.run("%s --analyzer=gcc %s -- -I %s > %s"%(INSTRUMENT_TOOL, abs_file_path, CSMITH_HEADER,pat_path+ "/instru_" + short_name + ".c"),
                               stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, shell=True , check=True )
    elif analyzer == "clang":
        subprocess.run("%s --analyzer=clang %s -- -I %s > %s"%(INSTRUMENT_TOOL, abs_file_path, CSMITH_HEADER ,pat_path+ "/instru_" + short_name + ".c"),
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
        description="some tools for testing static analyzer")
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
    parser_gen_reduce.add_argument("checker", type=str, choices=CHECKER_LIST, help="give a checker")
    parser_gen_reduce.add_argument("optimize", type=int, choices={
                                   0, 1, 2, 3}, help="optimization level")
    # parser_gen_reduce.add_argument(
        # "-t", "--script_path", type=str, help="specify script path")
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
    parser_fuzz_fp = subparsers.add_parser(
        "fuzz-fp", help="fuzzing static analyzer in a given dir")
    parser_fuzz_fp.add_argument(
        "path", help="given a parent dir of fuzzing working dir")
    parser_fuzz_fp.add_argument("analyzer", type=str, choices={
        'gcc', 'clang'}, help="give a analyzer")
    parser_fuzz_fp.add_argument("checker", type=str, choices=CHECKER_LIST, help="give a checker")
    parser_fuzz_fp.add_argument("optimize", type=int, choices={
        0, 1, 2, 3}, default=0, help="optimization level ( if clang, ...")
    parser_fuzz_fp.add_argument(
        "thread", type=int, default=1, help="specify the thread num for fuzzing")
    parser_fuzz_fp.add_argument(
        "num", type=int, default=1, help="the iteration times of fuzzing")

    parser_fuzz_fp.set_defaults(func=fuzz_fp)

    # add subcommand fuzz-fn
    parser_fuzz_fn = subparsers.add_parser(
        "fuzz-fn", help="fuzzing static analyzer in a given dir")
    parser_fuzz_fn.add_argument(
        "path", help="given a parent dir of fuzzing working dir")
    parser_fuzz_fn.add_argument("analyzer", type=str, choices={
        'gcc', 'clang'}, help="give a analyzer")
    parser_fuzz_fn.add_argument("optimize", type=int, choices={
        0, 1, 2, 3}, default=0, help="optimization level ( if clang, ...")
    parser_fuzz_fn.add_argument(
        "thread", type=int, default=1, help="specify the thread num for fuzzing")
    parser_fuzz_fn.add_argument(
        "num", type=int, default=1, help="the iteration times of fuzzing")

    parser_fuzz_fn.set_defaults(func=fuzz_fn)

     # add subcommand fuzz-eval
    parser_fuzz_eval = subparsers.add_parser(
        "fuzz-eval", help="fuzzing static analyzer in a given dir")
    parser_fuzz_eval.add_argument(
        "path", help="given a parent dir of fuzzing working dir")
    parser_fuzz_eval.add_argument("analyzer", type=str, choices={
        'gcc', 'clang'}, help="give a analyzer")
    parser_fuzz_eval.add_argument("optimize", type=int, choices={
        0, 1, 2, 3}, default=0, help="optimization level")
    parser_fuzz_eval.add_argument(
        "thread", type=int, default=1, help="specify the thread num for fuzzing")
    parser_fuzz_eval.add_argument(
        "num", type=int, default=1, help="the iteration times of fuzzing")

    parser_fuzz_eval.set_defaults(func=fuzz_eval)


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


    # add subcommand check-fp
    parser_checkfp = subparsers.add_parser(
        "check-fp", help="check whether the given analyzer complain the given warning for the given c program ")
    parser_checkfp.add_argument("analyzer", type=str, choices={
                                 'gcc', 'clang'}, help="give a analyzer")
    parser_checkfp.add_argument("checker", type=str, choices=CHECKER_LIST, help="give a checker")
    parser_checkfp.add_argument("-o", "--optimize", type=int,
                                 choices={0, 1, 2, 3}, default=0, help="optimization level")
    parser_checkfp.add_argument(
        "-n", "--num", type=int, default=1, help="the times of checked for each file")
    parser_checkfp.add_argument("-s", "--saveReport", action="store_true",
                                 help="do not delete generated files in analyzing process")

    group_checkfp = parser_checkfp.add_mutually_exclusive_group()
    group_checkfp.add_argument("-f", "--file", type=str, help="give a c file")
    group_checkfp.add_argument("-d", "--dir", type=str, help="give a directory")

    parser_checkfp.set_defaults(func=check_fp)

    # add subcommand check-reach
    parser_reach_warning_lines = subparsers.add_parser(
        "check-reach", help="check whether the warning line complained by the given analyzer is reachable")
    parser_reach_warning_lines.add_argument("analyzer", type=str, choices={
                                        'gcc', 'clang'}, help="give a analyzer")
    parser_reach_warning_lines.add_argument("checker", type=str, choices=CHECKER_LIST, help="give a checker")
    parser_reach_warning_lines.add_argument("optimize", type=int, choices={0, 1, 2, 3}, default=0, help="optimization level")
    parser_reach_warning_lines.add_argument(
        "-s", "--saveOutput", action="store_true", help="do not delete generated files in checking process")

    group_rm_reach_warning_lines = parser_reach_warning_lines.add_mutually_exclusive_group()
    group_rm_reach_warning_lines.add_argument(
        "-mn", "--rmNonReachable", action="store_true", help="remove non-warning-line-reachable test c files")
    group_rm_reach_warning_lines.add_argument(
        "-ma", "--rmAllReachable", action="store_true", help="remove all-warning-line-reachable test c files")

    group_reach_warning_lines = parser_reach_warning_lines.add_mutually_exclusive_group()
    group_reach_warning_lines.add_argument(
        "-cf", "--cfile", type=str, help="give a cfile")
    group_reach_warning_lines.add_argument(
        "-d", "--dir", type=str, help="give a directory")

    parser_reach_warning_lines.set_defaults(func=check_reachable)

    args = parser.parse_args()
    return args


def main():
    args = handle_args()
    if args.verbose:
        print(args)
    args.func(args)


if __name__ == "__main__":
    main()
