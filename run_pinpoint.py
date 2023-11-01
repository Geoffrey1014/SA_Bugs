from config import *

def analyze_with_pinpoint(cfile_path):
    """
    use PinPoint to analyze Csmith-generated C program
    """
    par_path, cfile_name = os.path.split(cfile_path)
    name, _ = cfile_name.split(".")
    report_file =  os.path.join(par_path, name+".json")
    ibc_file = os.path.join(par_path, name+".ibc")
    bc_file =  os.path.join(par_path, name+".bc")
    bson_file = os.path.join(par_path, name+".bson")

    print("par_path: %s"%(par_path))
    
    os.system(CLANG_CMD + cfile_path + " -o " + bc_file)
    os.system(TRANS_CMD + bc_file + " -o " + ibc_file)
    os.system(SEG_CMD + ibc_file + " -o " + bson_file)
    os.system(CHECK_CMD + ibc_file + " -i=" +bson_file + " -report="+ report_file)
    
    if par_path == "":
        print("par_path is empty!")
    os.system("rm -f %s/*\.bc %s/*\.ibc %s/*\.bson"%(par_path,par_path,par_path))
    
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
    cfiles = []
    for file in files:
        a, b = file.split('.')
        if b == 'c':
            cfiles.append(file)
    if len(cfiles)> 1:
        print("There are more than one cfile!")
        exit(-1)
    return cfiles[0]


def main():
    print("number of param:", len(sys.argv))
    print("param list:", str(sys.argv))
    print("script name:", sys.argv[0])
    for i in range(1, len(sys.argv)):
        print("param %s is: %s" % (i, sys.argv[i]))
    if len(sys.argv) != 2:
        exit(-1)
    target_c_file = sys.argv[1]
    report_file = analyze_with_pinpoint(target_c_file)
    checkNpd(report_file)


if __name__ == "__main__":
    main()