import os,subprocess,re, shutil,time
from config import *

def get_short_name(full_name:str) -> str:
    '''
    input: abs_path
    return: basename without suffix
    '''
    basename = os.path.basename(full_name)
    name, *_ = basename.split(".")

    return name

def get_analyzer_version(analyzer) -> str:
    res = subprocess.run([analyzer, "-v"], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, encoding='utf-8')

    return res.stderr

def read_value_from_file(file, match):
    '''
    extra the group(1) of searched pattern
    '''
    with open(file, 'r') as f:
        pattern = re.compile(r''+match)
        for line in f.readlines():
            seed = pattern.search(line)
            if seed:
                return seed.group(1)

    return ""


def generate_code(num, csmith_options, ctrl_max=False, verbose=False):
    '''
    generate wanted-size code with csmith \\
    generated test cases are saved in "test_%s.c" % num
    '''
    cfile = f"test_{num}.c"
    if os.path.exists(cfile):
        os.remove(cfile)

    while True:
        cmd = f"csmith {csmith_options} --output {cfile}"
        os.system(cmd)
        file_size = os.stat(cfile).st_size

        if ctrl_max:
            if file_size < MAX_PROGRAM_SIZE:
                if verbose:
                    print(f"Successfully generated a file whose size is no more than {MAX_PROGRAM_SIZE}: {cfile}")
                break
        else:
            if file_size > MIN_PROGRAM_SIZE:
                if verbose:
                    print(f"Successfully generated a file whose size is no less than {MIN_PROGRAM_SIZE}: {cfile}")
                break

    if verbose:
        seed = read_value_from_file(cfile, r"Seed:\s+(\d+)")
        print(f"Generated a C file {cfile}, Seed: {seed}")

    return cfile

def cleanup_files(*files):
    '''
    Remove the specified files.
    '''
    for file in files:
        if os.path.exists(file):
            os.remove(file)

def cleanup_directory(directory):
    '''
    Remove all files in the specified directory.
    '''
    if os.path.exists(directory):
        shutil.rmtree(directory)
        os.mkdir(directory)


def get_warning_line_from_file(report_file, warning):
    '''
    get warning line number from report file
    report_file needs to be guaranteed to exist
    '''
    warning_lines = []
    with open(report_file, "r") as f:
        report_lines = f.readlines()

        for line in report_lines:
            if re.search(warning, line):
                warning_info = re.split(":", line)
                # warning_info[1] is the warning line number
                warning_lines.append(warning_info.pop(1))
    return warning_lines

def get_warning_lines(analyzer, checker, report_abspath):
    '''
    Given an analyzer, checker, and report file path, returns a list of warning lines.

    Args:
    - analyzer (str): The name of the analyzer to use ("gcc" or "clang").
    - checker (str): The name of the checker to use ("npd" or "oob").
    - report_abspath (str): The absolute path to the report file.

    Returns:
    - warning_lines (list): A list of warning lines.
    '''
    if analyzer == "gcc":
        if checker == "npd":
            warning_name = "-Wanalyzer-null-dereference"
        elif checker == "oob":
            warning_name = "-Wanalyzer-out-of-bounds"
        else:
            print("please make sure the checker is npd or oob!")
            exit(-1)
        warning_lines = get_warning_line_from_file(report_abspath, warning_name)
        
    elif analyzer == "clang":
        if checker == "npd":
            warning_name = "core.NullDereference"
        elif checker == "oob":
            warning_name = "alpha.security.ArrayBound"
        else:
            print("please make sure the checker is npd or oob!")
            exit(-1)
        warning_lines = get_warning_line_from_file(report_abspath, warning_name)
    else:
        print("please make sure the analyzer is gcc or clang!")
        exit(-1)
    return warning_lines


def instrument_cfile(cfile_abspath, warning_lines, instrumented_cfile):
    '''
    input: cfile_abspath, warning_lines, instrumented_cfile
    output: whether generating instrumented c file successfully
    '''
    try:
        with open(cfile_abspath, "r") as f:
            cfile_lines = f.readlines()

            for num in warning_lines:
                c_num = int(num)-1
                cfile_lines[c_num] = 'printf("FLAG\\n");' + cfile_lines[c_num]

            try:
                with open(instrumented_cfile, "w") as f:
                    f.writelines(cfile_lines)
            except OSError:
                print("Error writing to instrumented file: %s" % instrumented_cfile)
                return False
    except OSError:
        print("Error reading from file: %s" % cfile_abspath)
        return False
    return True


def compile_and_run_instrument_cfile(cc, optimize, instrumented_cfile, run_out_file):
    '''
    Compiles and runs an instrumented C file using the specified compiler and optimization level.
    The output of the program is written to a file.

    Args:
    cc (str): The path to the C compiler to use.
    optimize (int): The optimization level to use.
    instrumented_cfile (str): The path to the instrumented C file to compile and run.
    run_out_file (str): The path to the file to write the program output to.

    Returns:
    bool: True if the program was compiled and run successfully, False otherwise.
    '''
    try:
        subprocess.run([cc, "-O" + str(optimize), "-I", CSMITH_HEADER,
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
    # os.remove("a.out")

    try:
        with open(run_out_file, "w") as f:
            f.write(cc + ": version: \n" +
                    get_analyzer_version(cc) + "\n")
            f.write(run_ret.stdout)
    except IOError:
        print("cannot write to %s !" % run_out_file)
        return False

    return True

def get_compiler(analyzer):
    '''
    Returns the path to the C compiler based on the specified analyzer.

    Args:
    analyzer (str): The name of the analyzer to use. Must be "gcc" or "clang".

    Returns:
    str: The path to the C compiler.
    '''
    if analyzer == "gcc":
        return GCC
    elif analyzer == "clang":
        return CLANG
    else:
        print("please make sure the analyzer is gcc or clang!")
        exit(-1)


def grep_flag(run_out_file):
    '''
    Searches for the string "FLAG" in the specified file using the grep command.

    Args:
    run_out_file (str): The path to the file to search.

    Returns:
    bool: True if the string "FLAG" is found in the file, False otherwise.
    '''
    try:
        subprocess.run(["grep", "FLAG", run_out_file],
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"grep_flag: Failed to grep FLAG. Error: {e}")
        return False

def write_result_to_file(res_reachable, res_not_reachable, res_report_not_exist, res_compile_or_run_fail, analyzer):
    '''
    Writes the results of the analysis to a file.

    Args:
    res_reachable (list): A list of reachable paths.
    res_not_reachable (list): A list of non-reachable paths.
    res_report_not_exist (list): A list of paths for which the report does not exist.
    res_compile_or_run_fail (list): A list of paths for which the compilation or execution failed.
    analyzer (str): The name of the analyzer used.

    Returns:
    bool: True if the results were written to the file successfully, False otherwise.
    '''
    res_reachable.sort()
    res_not_reachable.sort()
    res_report_not_exist.sort()
    res_compile_or_run_fail.sort()
    reachable_report = "npd_reachable_report_" + \
        str(time.strftime("%Y-%m-%d-%H-%M", time.localtime())) + ".txt"
    try:
        with open(reachable_report, "w") as f:
            f.write("%s: version: \n %s\n" %
                    (analyzer, get_analyzer_version(analyzer)))
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
            return True
    except IOError:
        print("cannot write to %s !" % reachable_report)
        return False

def clean_check_reach_input(rmNonReachable, rmAllReachable, cfile_abspath, report_abspath, warning_exist):
    """
    Removes the cfile and report files if either rmNonReachable is True and there are no warnings, or if rmAllReachable is True.
    
    Args:
    rmNonReachable (bool): If True, remove the cfile and report files if there are no warnings.
    rmAllReachable (bool): If True, remove the cfile and report files regardless of warnings.
    cfile_abspath (str): Absolute path to the cfile.
    report_abspath (str): Absolute path to the report file.
    warning_exist (bool): If True, there are warnings in the report file.
    """
    if (not warning_exist and rmNonReachable) or rmAllReachable:
        os.remove(cfile_abspath)
        os.remove(report_abspath)

def clean_check_reach_output(saveOutput, instrumented_cfile, run_out_file, warning_exist):
    if saveOutput or warning_exist:
        return
    os.remove(instrumented_cfile)
    os.remove(run_out_file)
