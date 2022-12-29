import subprocess
import fuzz_sa_fn
import sys
import unittest

sys.path.append('../')


class Test1(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        print("execute setUpClass")

    @classmethod
    def tearDownClass(self):
        print("execute tearDownClass")

    def setUp(self):
        print("execute setUp")

    def tearDown(self):
        subprocess.run(['rm', '-f', 'a.out'])
        print("execute tearDown")

    def test_run_npd(self):
        print('execute test_run_npd')
        self.assertTrue(fuzz_sa_fn.run_npd("segmentation_fault.c", "0"))


if __name__ == '__main__':
    unittest.main()
