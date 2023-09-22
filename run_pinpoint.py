from config import *

def analyze_with_pinpoint(cfile_path):
    '''
    use pinpoint to analyze Csmith-generated c program
    '''
    par_path, cfile_name = os.path.split(cfile_path)
    print("par_path: %s"%(par_path) )
    name, _ = cfile_name.split('.')
    report_file =  os.path.join(par_path, name+".json")
    bc_file =  os.path.join(par_path, name+".bc")
    ibc_file = os.path.join(par_path, name+".ibc")
    bson_file = os.path.join(par_path, name+".bson")

    os.system(CLANG_CMD + cfile_path + " -o " + bc_file)
    os.system(TRANS_CMD + bc_file + " -o " + ibc_file)
    os.system(SEG_CMD + ibc_file + " -o " + bson_file)
    os.system(CHECK_CMD + ibc_file + " -i=" +bson_file + " -report="+ report_file)
    # os.system("rm -f %s/*\.bc %s/*\.ibc %s/*\.bson %s/*\.c"%(par_path,par_path,par_path,par_path))
    if par_path == "":
        print("par_path is empty!")
    os.system("rm -f %s/*\.bc %s/*\.ibc %s/*\.bson"%(par_path,par_path,par_path))


    return report_file

def checkNpd(path):
    with open(path, 'r') as f:
        dataJson = json.load(f)
        if dataJson["TotalBugs"] > 0:
            print("NPD Detected!")
            exit(0)
        else:
            print("No NPD!")
            exit(-1)

def get_cfile(files):
    cfiles = []
    for file in files:
        a, b = file.split('.')
        if b == 'c':
            cfiles.append(file)
    if len(cfiles)> 1:
        print("There are more than ONE C-file!")
        exit(-1)
    return cfiles[0]


def main():
    print('参数个数为:', len(sys.argv), '个参数。')
    print('参数列表:', str(sys.argv))
    print('脚本名为：', sys.argv[0])
    for i in range(1, len(sys.argv)):
        print('参数 %s 为：%s' % (i, sys.argv[i]))

    if len(sys.argv) != 2:
        exit(-1)

    target_c_file = sys.argv[1]
    # cur_path = os.getcwd()
    # files = os.listdir(cur_path)
    # cfile = get_cfile(files)

    # target_c_file = os.path.join(cur_path, cfile)
    report_file = analyze_with_pinpoint(target_c_file)
    checkNpd(report_file)

    
    


if __name__ == "__main__":
    # print("run pp-check and return the npd-checking result")
    main()