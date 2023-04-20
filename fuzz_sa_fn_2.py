from __future__ import print_function
from pycparser.plyparser import Coord
from pycparser import parse_file, c_ast

import argparse
import os
import re
import random
import subprocess
import sys
import json
import time

# this is not required if you've installed pycparser into
# your site-packages/ with setup.py
sys.path.extend(['.', '..'])

CSMITH_HEADER = "/usr/include/csmith"
CSMITH_USER_OPTIONS = "--ccomp"

GCC_ANALYZER = "gcc -fanalyzer -fanalyzer-call-summaries -Wno-analyzer-double-fclose -Wno-analyzer-double-free -Wno-analyzer-exposure-through-output-file -Wno-analyzer-file-leak -Wno-analyzer-free-of-non-heap -Wno-analyzer-malloc-leak -Wno-analyzer-mismatching-deallocation -Wno-analyzer-null-argument -Wno-analyzer-possible-null-argument -Wno-analyzer-possible-null-dereference -Wno-analyzer-shift-count-negative -Wno-analyzer-shift-count-overflow -Wno-analyzer-stale-setjmp-buffer -Wno-analyzer-unsafe-call-within-signal-handler -Wno-analyzer-use-after-free -Wno-analyzer-use-of-pointer-in-stale-stack-frame -Wno-analyzer-use-of-uninitialized-value -Wno-analyzer-write-to-const -Wno-analyzer-write-to-string-literal -fdiagnostics-plain-output -fdiagnostics-format=text"
CLANG_ANALYZER = "scan-build -disable-checker core.CallAndMessage -disable-checker core.DivideZero -disable-checker core.NonNullParamChecker -disable-checker core.StackAddressEscape -disable-checker core.UndefinedBinaryOperatorResult -disable-checker core.VLASize -disable-checker core.uninitialized.ArraySubscript -disable-checker core.uninitialized.Assign -disable-checker core.uninitialized.Branch -disable-checker core.uninitialized.CapturedBlockVariable -disable-checker core.uninitialized.UndefReturn -disable-checker cplusplus.InnerPointer -disable-checker cplusplus.Move -disable-checker cplusplus.NewDelete -disable-checker cplusplus.NewDeleteLeaks -disable-checker cplusplus.PlacementNew -disable-checker cplusplus.PureVirtualCall -disable-checker deadcode.DeadStores -disable-checker nullability.NullPassedToNonnull -disable-checker nullability.NullReturnedFromNonnull -disable-checker security.insecureAPI.gets -disable-checker security.insecureAPI.mkstemp -disable-checker security.insecureAPI.mktemp -disable-checker security.insecureAPI.vfork -disable-checker unix.API -disable-checker unix.Malloc -disable-checker unix.MallocSizeof -disable-checker unix.MismatchedDeallocator -disable-checker unix.Vfork -disable-checker unix.cstring.BadSizeArg -disable-checker unix.cstring.NullArg"
CLANG_OPTIONS = "-Wno-literal-conversion -Wno-bool-operation -Wno-pointer-sign -Wno-tautological-compare -Wno-incompatible-pointer-types -Wno-tautological-constant-out-of-range-compare -Wno-compare-distinct-pointer-types -Wno-implicit-const-int-float-conversion -Wno-constant-logical-operand -Wno-parentheses-equality -Wno-constant-conversion -Wno-unused-value -Xclang -analyzer-config -Xclang widen-loops=true"

ANALYZER_TIMEOUT = "timeout 180"

RE_CHILD_ARRAY = re.compile(r'(.*)\[(.*)\]')
RE_INTERNAL_ATTR = re.compile('__.*__')

CFILE = ""
AST_FILE = ""
OUT_FILE = ""
REPORT_FILE_GSA = ""
REPORT_FILE_CSA = ""
INFO_FILE = ""

MIS_NPD_NUM = 0


def memodict(fn):
    """
    fast memoization decorator for function taking single argument
    """
    class memodict(dict):
        def __missing__(self, key):
            ret = self[key] = fn(key)
            return ret

    return memodict().__getitem__


@memodict
def child_attrs_of(klass):
    """
    given a node class, get a set of child attrs
    memoized to avoid highly repetitive string manipulation
    """
    non_child_attrs = set(klass.attr_names)
    all_attrs = set(
        [i for i in klass.__slots__ if not RE_INTERNAL_ATTR.match(i)])

    return all_attrs - non_child_attrs


def to_dict(node):
    """
    recursively convert ast into dict representation
    """
    klass = node.__class__
    result = {}
    # metadata
    result["_nodetype"] = klass.__name__

    # local node attributes
    for attr in klass.attr_names:
        result[attr] = getattr(node, attr)

    # coord object
    if node.coord:
        result["coord"] = str(node.coord)
    else:
        result["coord"] = None

    # child attributes
    for child_name, child in node.children():
        # child strings are either simple (e.g. "value") or arrays (e.g. "block_items[1]")
        match = RE_CHILD_ARRAY.match(child_name)

        if match:
            array_name, array_index = match.groups()
            array_index = int(array_index)
            # arrays come in order, so we verify and append
            result[array_name] = result.get(array_name, [])
            result[array_name].append(to_dict(child))
        else:
            result[child_name] = to_dict(child)

    # any child attributes that were missing need "none" values in the json
    for child_attr in child_attrs_of(klass):
        if child_attr not in result:
            result[child_attr] = None

    return result


def to_json(node, **kwargs):
    """
    convert ast node to json string
    """
    return json.dumps(to_dict(node), **kwargs)


def file_to_dict(filename):
    """
    load C file into dict representation of ast
    """
    ast = parse_file(filename, use_cpp=True,
                     cpp_path='gcc',
                     # solve the problem that the introduction of standard libraries
                     # and external libraries causes the parsing failed
                     cpp_args=['-E', r'-Icsmith', r'-Ipycparser/utils/fake_libc_include'])

    return to_dict(ast)


def file_to_json(filename, **kwargs):
    """
    load C file into json string representation of ast
    """
    ast = parse_file(filename, use_cpp=True,
                     cpp_path='gcc',
                     # solve the problem that the introduction of standard libraries
                     # and external libraries causes the parsing failed
                     cpp_args=['-E', r'-Icsmith', r'-Ipycparser/utils/fake_libc_include'])

    return to_json(ast, **kwargs)


def _parse_coord(coord_str):
    """
    parse coord string (file:line[:column]) into coord object
    """
    if coord_str is None:
        return None

    vals = coord_str.split(":")
    vals.extend([None] * 3)
    filename, line, column = vals[:3]

    return Coord(filename, line, column)


def _convert_to_obj(value):
    """
    convert object in the dict representation into object
    note: mutually recursive with from_dict
    """
    value_type = type(value)

    if value_type == dict:
        return from_dict(value)
    elif value_type == list:
        return [_convert_to_obj(item) for item in value]
    else:
        # string
        return value


def from_dict(node_dict):
    """
    recursively build ast from dict representation
    """
    class_name = node_dict.pop('_nodetype')
    klass = getattr(c_ast, class_name)

    # create a new dict containing the key-value pairs which
    # we can pass to node constructors
    objs = {}
    for key, value in node_dict.items():
        if key == "coord":
            objs[key] = _parse_coord(value)
        else:
            objs[key] = _convert_to_obj(value)

    # use keyword parameters, which works thanks to
    # beautifully consistent ast node initializers
    return klass(**objs)


def from_json(ast_json):
    """
    build ast from json string representation
    """
    return from_dict(json.loads(ast_json))


def find_path_by_kv(ast):
    """
    find path based on specified key-value pair
    and return list of the keys passed
    """
    def iter_node(node_data, road_step):
        if isinstance(node_data, dict):
            key_value_iter = (x for x in node_data.items())
        elif isinstance(node_data, list):
            key_value_iter = (x for x in enumerate(node_data))

        for key, value in key_value_iter:
            current_path = road_step.copy()
            current_path.append(key)

            if key == "_nodetype" and value == "PtrDecl":
                yield current_path
            if isinstance(value, (dict, list)):
                yield from iter_node(value, current_path)

    """
    there are **hundreds of** pointer types in a CFILE,
    so it returns a two-dimensional list, which has
    **hundreds of** one-dimensional lists in this list!
    """

    path_list = []
    # for each key-value pair, there is a corresponding list
    for item in iter_node(json.loads(ast), []):
        path_list.append(item)

    return path_list


def read_value_from_file(match):
    """
    extra the group(1) of searched pattern
    """
    global CFILE

    with open(CFILE, "r") as f:
        pattern = re.compile(r""+match)

        for line in f.readlines():
            seed = pattern.search(line)
            if seed:
                return seed.group(1)

    return ""


def generate_code():
    """
    use csmith to generate test cases
    """
    global CSMITH_USER_OPTIONS, CFILE

    os.system("csmith {} --output {}".format(CSMITH_USER_OPTIONS, CFILE))
    seed = read_value_from_file('Seed:\s+(\d+)')

    if len(seed) <= 0:
        print("random program {} has no seed information\n".format(CFILE))
        return None
    else:
        return True


def instrument_cfile(ast, path_list):
    """
    insert C statement (pointer = NULL) after specified line
    """
    global CFILE

    res_list = []
    tmp_list = []
    target_name_list = []
    target_line_list = []

    for x in range(len(path_list)):
        index = 1
        path_sublist = json.loads(ast)[path_list[x][0]]
        res_list.clear()
        tmp_list.clear()

        """
        [["key1", "key2", "key3"], ["key4", "key5", "key6", "key7"]]
        x = 0: ["key1", "key2", "key3"]
        x = 1: ["key4", "key5", "key6", "key7"]
        """

        for y in range(len(path_list[x])-1):
            item = ("t{}".format(y))
            tmp_list.append(item)

            """
            x = 0: y in range (3) -> tmp_list[t0, t1, t2]
            x = 1: y in range (4) -> tmp_list[t0, t1, t2, t3]
            """

        for item in tmp_list:
            item = path_sublist[path_list[x][index]]
            index = index + 1
            path_sublist = item
            res_list.append(item)

            # following this logic, the dict where
            # the key-value pair are located is approached continuously

            """
            t0 = t0[list[1]]
            t1 = t0[list[2]]
            t2 = t1[list[3]]
            """

        """
        {
            "_nodetype": "PtrDecl",
            "coord": "case_0.c:37:26",
            "quals": [ "const" ],
            "type": {
                "_nodetype": "TypeDecl",
                "align": null,
                "coord": "case_0.c:37:34",
                "declname": "g_54",
                "quals": [ "volatile" ],
                "type": {
                    "_nodetype": "Union",
                    "coord": "case_0.c:37:23",
                    "decls": null,
                    "name": "U1"
                }
            }
        }
        """

        # if res_list[-2]["type"].__contains__("type") and res_list[-2]["type"]["type"] is not None \
        #         and res_list[-2]["type"]["type"]["_nodetype"] == "Union":

        if res_list[-2]["type"] is not None and \
                res_list[-2]["coord"] is not None and re.split(":", res_list[-2]["coord"])[0] == CFILE and \
                res_list[-2]["type"].__contains__("declname") and res_list[-2]["type"]["declname"] is not None:

            if not re.match(r"func*", res_list[-2]["type"]["declname"]) \
                    and not re.match(r"argv", res_list[-2]["type"]["declname"]):

                target_name_list.append(
                    res_list[-2]["type"]["declname"])
                target_line_list.append(
                    re.split(":", res_list[-2]["coord"])[-2])

    if len(target_line_list)-1 > 0:
        index = random.randint(0, len(target_line_list)-1)
        target_line = target_line_list[index]
        target_name = target_name_list[index]

        # test: target_name and target_line
        print("{}: {}\n".format(target_name, target_line))

        f = open(CFILE, "r")
        cfile_lines = f.readlines()
        cfile_lines[int(target_line)-1] = cfile_lines[int(target_line)-1] + \
            "{} = (void*)0;\n".format(target_name)
        f.close()

        with open(CFILE, "w") as f:
            f.writelines(cfile_lines)
            f.close()

        return True

    else:
        return None


def compile_and_run_cfile():
    """
    compile and run instrumented CFILE
    """
    global CSMITH_HEADER, CFILE

    compile_ret = subprocess.run(["gcc", "-I", CSMITH_HEADER, "-fsanitize=null", CFILE],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")

    if compile_ret.returncode == 0:
        run_ret = subprocess.run(["timeout", "3s", "./a.out"],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")

        if run_ret.stderr.count("runtime error") >= 1 and run_ret.stderr.count("null pointer") >= 1 and run_ret.stderr.count("the monitored command dumped core") >= 1:
            return not run_ret
        else:
            # test: run_ret.stderr
            with open("run_ret.error", "w") as f:
                f.writelines(run_ret.stderr)

    else:
        print("compile failed\n")


def check_from_report(sa):
    """
    check NPD from report of analyzer
    """
    global REPORT_FILE_GSA, REPORT_FILE_CSA, MIS_NPD_NUM

    if sa == "gsa":
        check_cmd = 'grep "\[CWE\-476\]"'
        ret = os.system(check_cmd + " < " + REPORT_FILE_GSA)

    elif sa == "csa":
        check_cmd = 'grep "\[core\.NullDereference\]"'
        ret = os.system(check_cmd + " < " + REPORT_FILE_CSA)

    ret >>= 8

    if ret != 0:
        MIS_NPD_NUM += 1
        os.system("mv {} {}_mis_{}".format(CFILE, sa, CFILE))
    else:
        os.system("rm -rf {}".format(CFILE))


def analyze_with_gsa():
    """
    analyze test cases with gcc static analyzer
    """
    global CSMITH_HEADER, GCC_ANALYZER, CFILE, REPORT_FILE_GSA, ANALYZER_TIMEOUT

    ret = os.system(ANALYZER_TIMEOUT + " " + GCC_ANALYZER + " -msse4.2 -c " +
                    "-I" + " " + CSMITH_HEADER + " " + CFILE + " > " + REPORT_FILE_GSA + " 2>&1")
    ret >>= 8

    if ret == 0:
        check_from_report("gsa")
    else:
        print("analyze_with_gsa ret: {}\n".format(ret))


def analyze_with_csa():
    """
    analyze test cases with clang static analyzer
    """
    global CSMITH_HEADER, CLANG_ANALYZER, CLANG_OPTIONS, CFILE, REPORT_FILE_CSA, ANALYZER_TIMEOUT

    ret = os.system(ANALYZER_TIMEOUT + " " + CLANG_ANALYZER + " -o " + "report_html" + " clang " +
                    CLANG_OPTIONS + " -c " + "-I" + " " + CSMITH_HEADER + " " + CFILE + " > " + REPORT_FILE_CSA + " 2>&1")
    ret >>= 8

    if ret == 0:
        check_from_report("csa")
    else:
        print("analyze_with_csa ret: {}\n".format(ret))


def ast_to_file(ast):
    """
    write ast to json file
    """
    global AST_FILE

    with open(AST_FILE, "w") as f:
        f.writelines(ast)
        f.close()


def write_script_run_args():
    '''
    write down script running args
    '''
    global CSMITH_USER_OPTIONS, GCC_ANALYZER, CLANG_ANALYZER, CLANG_OPTIONS

    with open("script_run_args.info", "w") as f:

        f.write("time: {}\n\n".format((time.strftime(
            "%Y-%m-%d %H:%M:%S %a", time.localtime()))))
        f.write("csmith options: {}\n\n".format(CSMITH_USER_OPTIONS))
        f.write("gcc analyzer: {}\n\n".format(GCC_ANALYZER))
        f.write("clang analyzer: {}\n\n".format(CLANG_ANALYZER))
        f.write("clang options: {}\n\n".format(CLANG_OPTIONS))

        f.close()


def handle_args():
    '''
    handle command line args
    '''
    parser = argparse.ArgumentParser(
        description="fuzz static analyzers for false negative related null pointer dereference")
    parser.add_argument(
        "num_t", type=int, help="choose number of threads of fuzzing")
    parser.add_argument(
        "num_c", type=int, help="choose number of cases under each thread")

    args = parser.parse_args()
    return args


def main():
    global CFILE, AST_FILE, OUT_FILE, REPORT_FILE_GSA, REPORT_FILE_CSA

    args = handle_args()
    write_script_run_args()

    for i in range(args.num_c):
        CFILE = "case_{}.c".format(i)
        AST_FILE = "case_{}_ast.json".format(i)
        OUT_FILE = "case_{}.o".format(i)
        REPORT_FILE_GSA = "case_{}_gsa.txt".format(i)
        REPORT_FILE_CSA = "case_{}_csa.txt".format(i)

        if generate_code():
            ast = to_json(from_dict(file_to_dict(CFILE)),
                          sort_keys=True, indent=4)

            if instrument_cfile(ast, find_path_by_kv(ast)) and compile_and_run_cfile():
                analyze_with_gsa()
                analyze_with_csa()
            else:
                # test: func ast_to_file
                ast_to_file(ast)

                # test: func analyze_with_gsa/csa
                # analyze_with_gsa()
                # analyze_with_csa()


if __name__ == "__main__":
    main()
