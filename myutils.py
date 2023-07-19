import os,subprocess,re
from config import *

def get_short_name(full_name: str) -> str:
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
        os.system("rm -f %s" % cfile)

    while True:
        cmd = "csmith %s --output %s" % (csmith_options, cfile)
        os.system(cmd)
        file_size = os.stat(cfile).st_size

        if ctrl_max:
            if file_size < MAX_PROGRAM_SIZE:
                if verbose:
                    print("succ generated a file whose size is no more than %s: " % (MAX_PROGRAM_SIZE))
                break
        else:
            if file_size > MIN_PROGRAM_SIZE:
                if verbose:
                    print("succ generated a file whose size is no less than %s: " % (MIN_PROGRAM_SIZE))
                break
    if verbose:
        seed = read_value_from_file(cfile, 'Seed:\s+(\d+)')
        print("generated a c file %s, Seed: %s" %(cfile, seed))
    return cfile

