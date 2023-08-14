import os,subprocess,re, shutil,time, re
from config import *

__all__ = [ "get_short_name", "get_analyzer_version", "read_value_from_file", 
           "generate_code", "cleanup_files", "cleanup_directory", "get_warning_line_from_file","get_warning_lines",
           "instrument_cfile", "get_compiler", "compile_and_run_instrument_cfile", "grep_flag",
           "write_result_to_file", "clean_check_reach_input", "clean_check_reach_output", "gen_reduce_script",
           "get_serial_num", "wirte_reduce_result"
           ]

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
            if file_size < int(MAX_PROGRAM_SIZE):
                if verbose:
                    print(f"Successfully generated a file whose size is no more than {MAX_PROGRAM_SIZE}: {cfile}")
                break
        else:
            if file_size > int(MIN_PROGRAM_SIZE):
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
            raise ValueError("please make sure the checker is npd or oob!")
        warning_lines = get_warning_line_from_file(report_abspath, warning_name)
        
    elif analyzer == "clang":
        if checker == "npd":
            warning_name = "core.NullDereference"
        elif checker == "oob":
            warning_name = "alpha.security.ArrayBound"
        else:
            raise ValueError("please make sure the checker is npd or oob!")
        warning_lines = get_warning_line_from_file(report_abspath, warning_name)
    else:
        raise ValueError("Invalid analyzer specified: {}".format(analyzer))
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
        print(e)
        return False

    try:
        run_ret = subprocess.run(["timeout", RUN_TIMEOUT_NUM, "./a.out"], stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, encoding="utf-8", check=True)
    except subprocess.CalledProcessError as e:
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
        raise ValueError("Invalid analyzer specified: {}".format(analyzer))



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

def write_result_to_file(res_reachable, res_not_reachable, res_report_not_exist, res_compile_or_run_fail, analyzer,checker):
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
    reachable_report = checker + "_reachable_report_" + \
        str(time.strftime("%Y-%m-%d-%H-%M", time.localtime())) + ".txt"
    try:
        with open(reachable_report, "w") as f:
            f.write("%s: version: \n %s\n" %
                    (analyzer, get_analyzer_version(analyzer)))
            f.write("\nreachable:\n")
            print("\nreachable:\n")

            for i in res_reachable:
                print(i)
                f.write(i + "\n")

            f.write("\nnot_reachable:\n")
            print("\nnot_reachable:\n")

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
        if os.path.exists(cfile_abspath):
            os.remove(cfile_abspath)
        if os.path.exists(report_abspath):  
            os.remove(report_abspath)

def clean_check_reach_output(saveOutput, instrumented_cfile, run_out_file, warning_exist):
    if saveOutput or warning_exist:
        return
    if os.path.exists(instrumented_cfile):
        os.remove(instrumented_cfile)
    if os.path.exists(run_out_file):
        os.remove(run_out_file)


def gen_reduce_script(template_abspath: str, cfile_name: str, opt_level: str, checker: str) -> str:
    """
    Generates a reduce script from the specified template file.

    Args:
    template_abspath (str): Absolute path to the template file.
    cfile_name (str): Name of the C file.
    opt_level (str): Optimization level.
    checker (str): Checker to use.

    Returns:
    reduce_script (str): Name of the generated reduce script.
    """
    reduce_script = 'reduce_%s.py' % cfile_name
    try:
        with open(template_abspath, "r") as f:
            cfile_lines = f.readlines()

            config_values = ""
            config_names = ""
            g_vars = globals()
            import config 
            config_names = ','.join(config.__all__) + '='
            config_values = '"'+'", "'.join(str(g_vars[i]) for i in config.__all__) + '"\n'
            
                        
            cfile_lines[2] = config_names + config_values 
            cfile_lines[4] = 'CFILE = "%s.c"\n' % cfile_name            
            cfile_lines[5] = 'OPT_LEVEL = "%s"\n' % opt_level
            cfile_lines[6] = 'CHECKER = "%s"\n' % checker
            
            with open(reduce_script, "w") as f:
                f.writelines(cfile_lines)

            subprocess.run(['chmod', '+x', reduce_script])
    except Exception as e:
        print(e)
        print("gen_reduce_script fail!")
        return None
    return reduce_script

def get_serial_num(name):
    '''
    Returns the serial number of a given name.

    Args:
    name (str): The name to extract the serial number from.

    Returns:
    serial_num (str): The extracted serial number from the name.

    Example:
    input: instrument_npd123.c
    output: 123
    '''
    res = re.search(r'[a-zA-Z_]+(\d+)\..*', name)
    print(res)

    if res:
        return res.group(1)
    else:
        return None

def wirte_reduce_result(reduce_list, ub_list, flag_disappear_list, other_error_list):
    try:
        with open("reduce_result-%s.txt" % str(time.strftime("%Y-%m-%d-%H-%M", time.localtime())), "w") as f:
            f.write("\nReduced files:\n")
            for i in reduce_list:
                f.write(i + "\n")

            f.write("Undefined behavior:\n")
            for i in ub_list:
                f.write(i + "\n")
            
            f.write("\nFlag disappear:\n")
            for i in flag_disappear_list:   
                f.write(i + "\n")

            f.write("\nOther error:\n")
            for i in other_error_list:
                f.write(i + "\n")
    except IOError:
        print("cannot write to reduce_result.txt !")
        return False
    return True