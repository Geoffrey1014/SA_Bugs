#!/usr/bin/python3

from __future__ import print_function

import argparse
import json
import os
import random
import re
import subprocess
import sys

from pycparser import parse_file, c_ast
from pycparser.plyparser import Coord

sys.path.extend([".", ".."])

CSMITH_HEADER = "/usr/include/csmith"
CSMITH_USER_OPTIONS = "--no-const-pointers --no-global-variables --no-safe-math"

CLANG_ANALYZER = "clang --analyze -Xanalyzer -analyzer-checker=core.NullDereference -Xanalyzer -analyzer-checker=alpha.security.ArrayBoundV2 -Xclang -analyzer-config -Xclang widen-loops=true --analyzer-output text"
GCC_ANALYZER = "gcc -fanalyzer -Wanalyzer-null-dereference -Wanalyzer-out-of-bounds -Wno-incompatible-pointer-types -Wno-overflow"

# -fdiagnostics-plain-output -fdiagnostics-format=text

ANALYZER_TIMEOUT = "timeout 5s"

RE_CHILD_ARRAY = re.compile(r'(.*)\[(.*)\]')
RE_INTERNAL_ATTR = re.compile('__.*__')

CFILE = ""
CFILE_TMP = ""
SAN_FILE = ""
REPORT_FILE_CSA = ""
REPORT_FILE_GSA = ""

NPD_LINE_SAN = []
OOB_LINE_SAN = []
NPD_LINE_CSA = []
NPD_LINE_GSA = []
OOB_LINE_CSA = []
OOB_LINE_GSA = []

FN_NPD_CSA_NUM = 0
FN_NPD_GSA_NUM = 0
FN_OOB_CSA_NUM = 0
FN_OOB_GSA_NUM = 0

PTRQQ_SCOPE_LIST = []

TARGET_NAME_LIST = []
TARGET_LINE_LIST = []


def memodict(fn):
    """
    fast memoization decorator for function with a single argument
    """

    class memodict(dict):
        def __missing__(self, key):
            ret = self[key] = fn(key)
            return ret

    return memodict().__getitem__


@memodict
def child_attrs_of(klass):
    """
    given a node class, retrieve a collection of child attributes that
    have been memoized to prevent excessive repetition of string manipulation
    """
    non_child_attrs = set(klass.attr_names)
    all_attrs = set(
        [i for i in klass.__slots__ if not RE_INTERNAL_ATTR.match(i)])

    return all_attrs - non_child_attrs


def to_dict(node):
    """
    recursively convert an AST into a dictionary representation
    """
    klass = node.__class__
    result = {}
    result["_nodetype"] = klass.__name__

    for attr in klass.attr_names:
        result[attr] = getattr(node, attr)

    if node.coord:
        result["coord"] = str(node.coord)
    else:
        result["coord"] = None

    for child_name, child in node.children():
        match = RE_CHILD_ARRAY.match(child_name)

        if match:
            array_name, array_index = match.groups()
            array_index = int(array_index)
            result[array_name] = result.get(array_name, [])
            result[array_name].append(to_dict(child))
        else:
            result[child_name] = to_dict(child)

    for child_attr in child_attrs_of(klass):
        if child_attr not in result:
            result[child_attr] = None

    return result


def to_json(node, **kwargs):
    """
    convert AST node to JSON string
    """
    return json.dumps(to_dict(node), **kwargs)


def file_to_dict(filename):
    """
    load a C file into a dictionary representation of the AST
    """
    ast = parse_file(filename, use_cpp=True,
                     cpp_path="gcc",
                     cpp_args=["-E", r"-I/usr/include/csmith", r"-I/usr/include/pycparser/utils/fake_libc_include"])

    return to_dict(ast)


def file_to_json(filename, **kwargs):
    """
    load a C file into a JSON string representation of the AST
    """
    ast = parse_file(filename, use_cpp=True,
                     cpp_path="gcc",
                     cpp_args=["-E", r"-I/usr/include/csmith", r"-I/usr/include/pycparser/utils/fake_libc_include"])

    return to_json(ast, **kwargs)


def _parse_coord(coord_str):
    """
    parse coord string `(file:line[:column])` into a coord object
    """
    if coord_str is None:
        return None

    vals = coord_str.split(":")
    vals.extend([None] * 3)
    filename, line, column = vals[:3]

    return Coord(filename, line, column)


def _convert_to_obj(value):
    """
    convert an object in dictionary representation into an object
    note: mutually recursive with `from_dict`
    """
    value_type = type(value)

    if value_type == dict:
        return from_dict(value)
    elif value_type == list:
        return [_convert_to_obj(item) for item in value]
    else:
        return value


def from_dict(node_dict):
    """
    recursively construct an AST from a dictionary representation
    """
    objs = {}
    class_name = node_dict.pop('_nodetype')
    klass = getattr(c_ast, class_name)

    for key, value in node_dict.items():
        if key == "coord":
            objs[key] = _parse_coord(value)
        else:
            objs[key] = _convert_to_obj(value)

    return klass(**objs)


def from_json(ast_json):
    """
    construct an AST from a JSON string representation
    """
    return from_dict(json.loads(ast_json))


def fuzz_case_with_csmith():
    """
    utilize Csmith to generate test cases
    """
    global CSMITH_USER_OPTIONS, CFILE

    os.system("csmith {} --output {}".format(CSMITH_USER_OPTIONS, CFILE))


def find_path(ast, target_key, target_value):
    """
    find the path based on the specified key-value and 
    return a list of the keys that are passed
    """

    def iter_node(node_data, road_step):
        if isinstance(node_data, dict):
            key_value_iter = (x for x in node_data.items())
        elif isinstance(node_data, list):
            key_value_iter = (x for x in enumerate(node_data))

        for key, value in key_value_iter:
            current_path = road_step.copy()
            current_path.append(key)

            if key == target_key and value == target_value:
                yield current_path

            if isinstance(value, (dict, list)):
                yield from iter_node(value, current_path)

    path_list = []

    for item in iter_node(json.loads(ast), []):
        path_list.append(item)

    return path_list


def fetch_value(ast, path_list, tmp_list, ret_list, x):
    """
    fetch a value from a JSON object using a specified path
    """
    index = 1
    path_sublist = json.loads(ast)[path_list[x][0]]

    tmp_list.clear()
    ret_list.clear()

    for y in range(len(path_list[x]) - 1):
        item = ("tmp_{}".format(y))
        tmp_list.append(item)

    for _ in tmp_list:
        item = path_sublist[path_list[x][index]]
        index = index + 1
        path_sublist = item
        ret_list.append(item)

    return ret_list


def scope_analysis_helper(var_name, item):
    """
    scope analysis of ptr (branch nesting)
    """
    global PTRQQ_SCOPE_LIST

    if item.__contains__("stmt") and item["stmt"] is not None and \
       item["stmt"].__contains__("block_items") and item["stmt"]["block_items"] is not None:

        for index in range(len(item["stmt"]["block_items"])):
            if item["stmt"]["block_items"][index].__contains__("_nodetype") and item["stmt"]["block_items"][index]["_nodetype"] is not None and \
                ((item["stmt"]["block_items"][index]["_nodetype"] == "If") or
                 (item["stmt"]["block_items"][index]["_nodetype"] == "For")):
                # TODO: ...
                print(
                    "if / for stmt: {}\n".format(item["stmt"]["block_items"][index]["cond"]["coord"])[-2])


def scope_analysis(var_name, ret_list):
    """
    scope analysis of ptr
    """
    global PTRQQ_SCOPE_LIST

    if ret_list.__contains__("_nodetype") and ret_list["_nodetype"] is not None and \
            ((ret_list["_nodetype"] == "For") or
             (ret_list["_nodetype"] == "If") or
             (ret_list["_nodetype"] == "FuncDef")):

        if ret_list.__contains__("stmt") and ret_list["stmt"].__contains__("block_items") and \
           ret_list["stmt"]["block_items"] is not None:

            branch_list = []
            branch_dict = {}

            for item in ret_list["stmt"]["block_items"]:
                if item.__contains__("_nodetype") and item["_nodetype"] is not None and \
                        ((item["_nodetype"] == "For") or (item["_nodetype"] == "If")):

                    branch_line = re.split(":", item["cond"]["coord"])[-2]

                    if branch_line not in branch_list:
                        branch_list.append(branch_line)

            if branch_list is not None:
                branch_dict[var_name] = branch_list

            if branch_dict not in PTRQQ_SCOPE_LIST:
                PTRQQ_SCOPE_LIST.append(branch_dict)


def filter_ptr_helper(ast, ret_list):
    """
    filter out global pointers, pointers to arrays, pointers to unions, and pointers to structures
    """
    global TARGET_NAME_LIST, TARGET_LINE_LIST

    new_tmp_list = []
    new_ret_list = []

    new_path_list = find_path(ast, "name", ret_list[-2]["type"]["declname"])

    for x in range(len(new_path_list)):
        new_ret_list = fetch_value(
            ast, new_path_list, new_tmp_list, new_ret_list, x)

        if new_ret_list[-2].__contains__("type") and new_ret_list[-2]["type"] is not None and \
                new_ret_list[-2]["type"].__contains__("_nodetype") and new_ret_list[-2]["type"][
            "_nodetype"] is not None and \
                new_ret_list[-2]["type"]["_nodetype"] != "ArrayDecl":

            if ret_list[-2]["type"]["declname"] not in TARGET_NAME_LIST and \
                    re.split(":", ret_list[-2]["coord"])[-2] not in TARGET_LINE_LIST:

                TARGET_NAME_LIST.append(
                    ret_list[-2]["type"]["declname"])
                TARGET_LINE_LIST.append(
                    re.split(":", ret_list[-2]["coord"])[-2])

                scope_analysis(ret_list[-2]["type"]["declname"], ret_list[-6])


def filter_ptr(ast, path_list):
    """
    filter out global pointers, pointers to array, pointers to union, and pointers to structure
    """
    global CFILE

    tmp_list = []
    ret_list = []

    for x in range(len(path_list)):
        ret_list = fetch_value(ast, path_list, tmp_list, ret_list, x)

        if ret_list[-2].__contains__("coord") and ret_list[-2]["coord"] is not None and \
                re.split(":", ret_list[-2]["coord"])[0] == CFILE and \
                ret_list[-2].__contains__("type") and ret_list[-2]["type"] is not None and \
                ret_list[-2]["type"].__contains__("declname") and ret_list[-2]["type"]["declname"] is not None and \
                ret_list[-2]["type"].__contains__("type") and ret_list[-2]["type"]["type"] is not None and \
                ret_list[-2]["type"]["type"].__contains__("_nodetype") and ret_list[-2]["type"]["type"][
            "_nodetype"] is not None and \
                ret_list[-2]["type"]["type"]["_nodetype"] != "Union" and \
                ret_list[-2]["type"]["type"]["_nodetype"] != "Struct":

            if not re.match(r"g_*", ret_list[-2]["type"]["declname"]) and not re.match(r"p_*", ret_list[-2]["type"][
                "declname"]) and \
                    not re.match(r"func*", ret_list[-2]["type"]["declname"]) and \
                    not re.match(r"argv", ret_list[-2]["type"]["declname"]):

                filter_ptr_helper(ast, ret_list)


def instrument_nullptr_then_defer():
    """
    insert `ptr = NULL` after the specified line;
    insert `*ptr = 123456` in the specified scope
    """
    global CFILE, TARGET_NAME_LIST, TARGET_LINE_LIST, PTRQQ_SCOPE_LIST

    if len(TARGET_LINE_LIST) - 1 > 7:
        index_list = []

        try:
            while len(index_list) < 3:
                index = random.randint(0, len(TARGET_LINE_LIST) - 1)
                if index not in index_list:
                    index_list.append(index)
        except Exception as e:
            write_exception("{}\n".format(str(e)))

        with open(CFILE, "r") as f1:
            cfile_lines = f1.readlines()

            for index in index_list:
                target_name = TARGET_NAME_LIST[index]
                target_line = TARGET_LINE_LIST[index]

                ptr_stmt = cfile_lines[int(target_line) - 1]
                cfile_lines[int(target_line) - 1] = ""
                cfile_lines[int(
                    target_line) - 1] = "{}{} = (void*)0;".format(ptr_stmt, target_name)

                for item in PTRQQ_SCOPE_LIST:
                    if item.get(target_name) is not None:
                        for scope_line in item.get(target_name):
                            branch_stmt = cfile_lines[int(scope_line)]
                            cfile_lines[int(scope_line)] = ""
                            cfile_lines[int(
                                scope_line)] = "{}*{} = 123456;".format(branch_stmt, target_name)

            with open(CFILE, "w") as f2:
                f2.writelines(cfile_lines)


def instrument_out_of_bound_index(ast):
    """
    such as: arr[1][2][3] -> arr[9][9][9]
    """
    global CFILE

    TMP_FLAG = 42

    with open(CFILE, "r") as f1:
        cfile_lines = f1.readlines()

    tmp_list = []
    ret_list = []
    target_lines = []
    target_comns = []

    path_list = find_path(ast, "_nodetype", "ArrayRef")

    for x in range(len(path_list)):
        ret_list = fetch_value(ast, path_list, tmp_list, ret_list, x)

        if ret_list[-2].__contains__("coord") and ret_list[-2]["coord"] is not None:
            target_line = int(re.split(":", ret_list[-2]["coord"])[-2])
            target_comn = int(re.split(":", ret_list[-2]["coord"])[-1])

            if ((target_line not in target_lines) and (target_comn not in target_comns)):
                target_lines.append(target_line)
                target_comns.append(target_comn)

                pattern = re.compile(r'\[(\d+)\]')
                matches = pattern.finditer(
                    str(cfile_lines[target_line - 1]), target_comn)

                if str(cfile_lines[target_line - 1]).find("=") == -1:
                    for match in matches:
                        target_comn = match.end()

                        # match_index.append(int(match.group(1)))

                        tmp_x = str(
                            cfile_lines[target_line - 1])[:int(str(cfile_lines[target_line - 1]).find("["))]
                        tmp_y = str(cfile_lines[target_line - 1])[
                            int(str(cfile_lines[target_line - 1]).find("[")):]

                        tmp_y = tmp_y.replace(str(cfile_lines[target_line - 1])[target_comn - 2],
                                              str(len(str(cfile_lines[target_line - 1])[target_comn - 2]) * 9))

                        cfile_lines[target_line - 1] = tmp_x + tmp_y

                        TMP_FLAG += 1

                        if TMP_FLAG == 70:
                            break

                        if str(cfile_lines[target_line - 1])[target_comn:].startswith("["):
                            continue
                        else:
                            break
            else:
                continue

        if TMP_FLAG == 70:
            break

    with open(CFILE, "w") as f2:
        f2.writelines(cfile_lines)


def compile_and_run_cfile():
    """
    compile and run instrumented test cases
    """
    global CSMITH_HEADER, CFILE, SAN_FILE, NPD_LINE_SAN, OOB_LINE_SAN

    compile_ret = subprocess.run(["gcc", "-I", CSMITH_HEADER, "-fsanitize=null", "-fsanitize=bounds", CFILE],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")

    if compile_ret.returncode == 0:
        run_ret = subprocess.run(["timeout", "0.001s", "./a.out"],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")

        if run_ret.stderr.count("runtime error") >= 1 and \
                ((run_ret.stderr.count("null pointer") >= 1) or (run_ret.stderr.count("out of bounds") >= 1)):

            with open(SAN_FILE, "w") as f:
                f.writelines(run_ret.stderr)

            with open(SAN_FILE, "r") as f:
                for line in f.readlines():
                    if (("runtime error" in line) and ("null pointer" in line)) and \
                       (int(re.split(":", line)[-4]) not in NPD_LINE_SAN):
                        NPD_LINE_SAN.append(int(re.split(":", line)[-4]))
                    if (("runtime error" in line) and ("out of bounds" in line)) and \
                       (int(re.split(":", line)[-4]) not in OOB_LINE_SAN):
                        OOB_LINE_SAN.append(int(re.split(":", line)[-4]))

            return True
        else:
            return None

    else:
        write_exception("{}\n".format(compile_ret.stderr))


def analyze_with_csa():
    """
    analyze the test case with CSA
    """
    global CSMITH_HEADER, CLANG_ANALYZER, CFILE, REPORT_FILE_CSA, ANALYZER_TIMEOUT, \
        FN_NPD_CSA_NUM, NPD_LINE_SAN, OOB_LINE_SAN, NPD_LINE_CSA, OOB_LINE_CSA

    ret = os.system(
        "{} {} {} > {} 2>&1".format(ANALYZER_TIMEOUT, CLANG_ANALYZER, CFILE, REPORT_FILE_CSA))
    ret >>= 8

    if ret == 0:
        with open(REPORT_FILE_CSA, "r") as f:
            for line in f.readlines():
                if ("core.NullDereference" in line) and (int(re.split(":", line)[-4]) not in NPD_LINE_CSA):
                    NPD_LINE_CSA.append(int(re.split(":", line)[-4]))
                if (("alpha.security.ArrayBoundV2" in line) or ("array-bounds" in line)) and (int(re.split(":", line)[-4]) not in OOB_LINE_CSA):
                    OOB_LINE_CSA.append(int(re.split(":", line)[-4]))

        if len(NPD_LINE_CSA) < len(NPD_LINE_SAN):
            os.system("cp {} fn_csa/{}".format(CFILE, CFILE))
        else:
            for item in NPD_LINE_SAN:
                if item not in NPD_LINE_CSA:
                    os.system("cp {} fn_csa/{}".format(CFILE, CFILE))

        if len(OOB_LINE_CSA) < len(OOB_LINE_SAN):
            os.system("cp {} fn_csa/{}".format(CFILE, CFILE))
        else:
            for item in NPD_LINE_SAN:
                if item not in OOB_LINE_CSA:
                    os.system("cp {} fn_csa/{}".format(CFILE, CFILE))

    else:
        if ret == 124:
            os.system("cp {} \"?_csa\"/timeout_{}".format(CFILE, CFILE))
        else:
            os.system("cp {} \"?_csa\"/case_{}.c".format(CFILE, CFILE))


def analyze_with_gsa():
    """
    analyze the test case with GSA
    """
    global CSMITH_HEADER, GCC_ANALYZER, CFILE, REPORT_FILE_GSA, ANALYZER_TIMEOUT, \
        FN_NPD_GSA_NUM, NPD_LINE_SAN, OOB_LINE_SAN, NPD_LINE_GSA, OOB_LINE_GSA

    ret = os.system(
        "{} {} {} > {} 2>&1".format(ANALYZER_TIMEOUT, GCC_ANALYZER, CFILE, REPORT_FILE_GSA))
    ret >>= 8

    if ret == 0:
        with open(REPORT_FILE_CSA, "r") as f:
            for line in f.readlines():
                if ("core.NullDereference" in line) and (int(re.split(":", line)[-4]) not in NPD_LINE_CSA):
                    NPD_LINE_CSA.append(int(re.split(":", line)[-4]))
                if (("alpha.security.ArrayBoundV2" in line) or ("array-bounds" in line)) and (int(re.split(":", line)[-4]) not in OOB_LINE_CSA):
                    OOB_LINE_CSA.append(int(re.split(":", line)[-4]))

        if len(NPD_LINE_CSA) < len(NPD_LINE_SAN):
            os.system("cp {} fn_csa/{}".format(CFILE, CFILE))
        else:
            for item in NPD_LINE_SAN:
                if item not in NPD_LINE_CSA:
                    os.system("cp {} fn_csa/{}".format(CFILE, CFILE))

        if len(OOB_LINE_CSA) < len(OOB_LINE_SAN):
            os.system("cp {} fn_csa/{}".format(CFILE, CFILE))
        else:
            for item in NPD_LINE_SAN:
                if item not in OOB_LINE_CSA:
                    os.system("cp {} fn_csa/{}".format(CFILE, CFILE))

    else:
        if ret == 124:
            os.system("cp {} \"?_csa\"/timeout_{}".format(CFILE, CFILE))
        else:
            os.system("cp {} \"?_csa\"/case_{}.c".format(CFILE, CFILE))


def write_exception(exception):
    """
    write down the exception
    """
    global CFILE, CFILE_TMP

    if CFILE_TMP != CFILE:
        CFILE_TMP = CFILE

        with open("exception.md", "a+") as f:
            f.write("## {}\n\n".format(CFILE))

    with open("exception.md", "a+") as f:
        f.write("{}\n\n".format(exception))


def write_fuzzing_result():
    """
    write down the result of fuzzing
    """
    global FN_NPD_CSA_NUM, FN_NPD_GSA_NUM, FN_OOB_CSA_NUM, FN_OOB_GSA_NUM

    with open("fuzzing_result.txt", "w") as f:
        f.write("FN_NPD_CSA_NUM: {} _ FN_NPD_GSA_NUM: {}\n".format(
            FN_NPD_CSA_NUM, FN_NPD_GSA_NUM))
        f.write("FN_OOB_CSA_NUM: {} _ FN_OOB_GSA_NUM: {}\n".format(
            FN_OOB_CSA_NUM, FN_OOB_GSA_NUM))


def handle_args():
    """
    handle the command line args
    """
    parser = argparse.ArgumentParser(
        description="fuzz static analyzer for FN related NPD & OOB")
    parser.add_argument(
        "num_t", type=int, help="choose number of threads of fuzzing")
    parser.add_argument(
        "num_c", type=int, help="choose number of cases under each thread")

    return parser.parse_args()


def main():
    global CFILE, SAN_FILE, REPORT_FILE_CSA, REPORT_FILE_GSA, TARGET_NAME_LIST, TARGET_LINE_LIST

    args = handle_args()

    for i in range(args.num_c):
        CFILE = "case_{}.c".format(i)
        REPORT_FILE_CSA = "case_{}_csa.txt".format(i)
        REPORT_FILE_GSA = "case_{}_gsa.txt".format(i)
        SAN_FILE = "case_{}_san.txt".format(i)

        TARGET_NAME_LIST.clear()
        TARGET_LINE_LIST.clear()

        NPD_LINE_SAN.clear()
        OOB_LINE_SAN.clear()
        NPD_LINE_CSA.clear()
        OOB_LINE_CSA.clear()
        NPD_LINE_GSA.clear()
        OOB_LINE_GSA.clear()

        try:
            fuzz_case_with_csmith()
        except Exception as e:
            write_exception("fuzz_case_with_csmith: {}\n".format(str(e)))
            continue

        try:
            ast = to_json(from_dict(file_to_dict(CFILE)),
                          sort_keys=True, indent=4)
        except Exception as e:
            write_exception("ast_to_json: {}\n".format(str(e)))
            continue

        try:
            filter_ptr(ast, find_path(ast, "_nodetype", "PtrDecl"))
        except Exception as e:
            write_exception("filter_ptr: {}\n".format(str(e)))
            continue

        try:
            instrument_nullptr_then_defer()
        except Exception as e:
            write_exception(
                "instrument_nullptr_then_defer: {}\n".format(str(e)))
            continue

        try:
            instrument_out_of_bound_index(ast)
        except Exception as e:
            write_exception(
                "instrument_out_of_bound_index: {}\n".format(str(e)))
            continue

        try:
            cr_flag = compile_and_run_cfile()
        except Exception as e:
            write_exception("compile_and_run_cfile: {}\n".format(str(e)))
            continue

        try:
            if cr_flag:
                analyze_with_csa()
                analyze_with_gsa()
        except Exception as e:
            write_exception("analyze_with_(csa/gsa): {}\n".format(str(e)))
            continue


if __name__ == "__main__":
    main()
