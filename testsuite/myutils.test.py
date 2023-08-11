import os, sys
import unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from myutils import *
from config import *


class TestUtils(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.root_dir = os.path.dirname(self.test_dir)  
        self.test_data_dir = os.path.join(self.root_dir, "test_data")

        self.test_file = os.path.join(self.test_data_dir, "test.txt")   
        with open(self.test_file, "w") as f:
            f.write("Seed: 1234\n")
            f.write("hello world\n")
            f.write("this is a test\n")
            f.write("goodbye\n")
            f.write("test.c:5:1: warning: stack-based buffer overflow [CWE-121] [-Wanalyzer-out-of-bounds]\n")

    def tearDown(self):
        os.remove(self.test_file)

    def test_get_short_name(self):
        self.assertEqual(get_short_name("file.txt"), "file")
        self.assertEqual(get_short_name("/path/to/another/file.py"), "file")

    def test_read_value_from_file(self):
        self.assertEqual(read_value_from_file(self.test_file, 'Seed:\s+(\d+)'), "1234")

    # def test_generate_code(self):
    #     cfile = generate_code(1, "")
    #     self.assertTrue(os.path.exists(cfile))
    #     os.remove(cfile)

    def test_get_analyzer_version(self):
        version = get_analyzer_version("clang")
        self.assertIn("clang version", version)
    
    def test_get_warning_line(self):
        warning_lines = get_warning_line_from_file(os.path.join(self.root_dir, "test_data/oob_0.txt"), "-Wanalyzer-out-of-bounds")
        # print(warning_lines)
        self.assertIn("107", warning_lines)

    def test_get_warning_line_2(self):            
        warning_lines = get_warning_line_from_file(self.test_file, "-Wanalyzer-out-of-bounds")
        # print(warning_lines)
        self.assertEqual(warning_lines, ["5"])
    
    def test_instrument_cfile(self):
        # Test case 1: Valid input
        cfile_abspath = os.path.join(self.root_dir,"test_data/oob_0.c")
        warning_lines = ['107', '107', '208', '214', '384', '460', '530', '545', '559', '560', '574', '621', '946', '985']
        instrumented_cfile = os.path.join(self.root_dir,"test_data/oob_0_instrumented.c")
        assert instrument_cfile(cfile_abspath, warning_lines, instrumented_cfile) == True
        os.remove(instrumented_cfile)

        # Test case 2: Invalid cfile_abspath
        cfile_abspath = "nonexistent.c"
        warning_lines = ["10", "20", "30"]
        instrumented_cfile = "test2_instrumented.c"
        assert instrument_cfile(cfile_abspath, warning_lines, instrumented_cfile) == False

        # Test case 3: Invalid warning_lines
        cfile_abspath = "test.c"
        warning_lines = ["100", "200", "300"]
        instrumented_cfile = "test3_instrumented.c"
        assert instrument_cfile(cfile_abspath, warning_lines, instrumented_cfile) == False

        # Test case 4: Invalid instrumented_cfile
        cfile_abspath = "test.c"
        warning_lines = ["10", "20", "30"]
        instrumented_cfile = "nonexistent_instrumented.c"
        assert instrument_cfile(cfile_abspath, warning_lines, instrumented_cfile) == False
    
    def test_get_compiler_gcc(self):
        self.assertEqual(get_compiler("gcc"), GCC)
        
    def test_get_compiler_clang(self):
        self.assertEqual(get_compiler("clang"), CLANG)
        
    def test_get_compiler_invalid(self):
        with self.assertRaises(SystemExit):
            get_compiler("invalid")
    
    def test_grep_flag(self):
        # Test case 1: FLAG is present in the file
        with open("test_file.txt", "w") as f:
            f.write("This is a test file with FLAG in it.")
        assert grep_flag("test_file.txt") == True
        
        # Test case 2: FLAG is not present in the file
        with open("test_file.txt", "w") as f:
            f.write("This is a test file without Flag.")
        assert grep_flag("test_file.txt") == False
        
        # Test case 3: File does not exist
        assert grep_flag("nonexistent_file.txt") == False
        os.remove("test_file.txt")

    def test_get_warning_lines(self):
        warning_lines = get_warning_lines("gcc", "oob", self.test_file)
        self.assertEqual(warning_lines, ['5'])
    
    def test_gen_reduce_script(self):
        template_abspath = self.root_dir + '/interestness_template_gcc.py'
        cfile = self.test_data_dir + '/oob_0.c'

        cfile_name = get_short_name(cfile)
        opt_level = '2'
        checker = 'oob'
        os.chdir(self.test_data_dir)

        # Generate the reduce script
        reduce_script = gen_reduce_script(template_abspath, cfile_name, opt_level, checker)

        # Check that the reduce script was generated successfully
        assert reduce_script is not None
        assert os.path.exists(reduce_script)

        # Check that the contents of the reduce script are correct
        with open(reduce_script, 'r') as f:
            lines = f.readlines()
            assert lines[4] == 'CFILE = "%s.c"\n' % cfile_name
            assert lines[5] == 'OPT_LEVEL = "%s"\n' % opt_level
            assert lines[6] == 'CHECKER = "%s"\n' % checker

        # Clean up the reduce script
        # os.remove(reduce_script)
        os.chdir(self.test_dir)
    
    def test_get_serial_num(self):
        self.assertEqual(get_serial_num("instrument_npd123.c"), "123")
        self.assertEqual(get_serial_num("file_abc456.c"), "456")
        self.assertEqual(get_serial_num("test_789.c"), "789")
        self.assertEqual(get_serial_num("no_serial_num.c"), None)

if __name__ == '__main__':
    unittest.main()