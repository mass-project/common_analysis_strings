import unittest
from common_analysis_strings import CommonAnalysisStrings
from tempfile import NamedTemporaryFile
import random
import string

test_chunk_size = 1024

class StringFinderTestCase(unittest.TestCase):

    def test_finds_string_in_textfile(self):
        string_finder = CommonAnalysisStrings(chunk_size=test_chunk_size)
        text_file = NamedTemporaryFile()
        with open(text_file.name, 'w') as f:
            f.write('Hello, World')
        found_strings = string_finder.analyze_file(text_file.name)['found strings']
        text_file.close()
        self.assertIn((0, 'Hello, World'), found_strings)

    def test_finds_strings_in_binary(self):
        string_finder = CommonAnalysisStrings(chunk_size=test_chunk_size)
        binary_file = NamedTemporaryFile()
        with open(binary_file.name, 'wb') as f:
            f.write(b'\x00\xFFHello\xde\xad\xbe\xef')
        found_strings = string_finder.analyze_file(binary_file.name)['found strings']
        binary_file.close()
        self.assertIn((2, 'Hello'), found_strings)

    def test_find_strings_on_file_slice_boundary(self):
        string_finder = CommonAnalysisStrings(chunk_size=test_chunk_size)
        large_binary_file = NamedTemporaryFile()
        with open(large_binary_file.name, 'wb') as f:
            f.write(b'\x01'*(test_chunk_size-1))
            f.write(b'Hello')
            f.write(b'\x01'*100)
        found_strings = string_finder.analyze_file(large_binary_file.name)['found strings']
        large_binary_file.close()
        self.assertIn((test_chunk_size-1,'Hello'), found_strings)
        self.assertNotIn('ello', (f[1] for f in found_strings))

    def test_find_strings_accross_text_file_slice_boundary(self):
        string_finder = CommonAnalysisStrings(chunk_size=test_chunk_size)
        large_binary_file = NamedTemporaryFile()
        with open(large_binary_file.name, 'wb') as f:
            f.write(b'a'*test_chunk_size*2 + b'b'*100)
        found_strings = string_finder.analyze_file(large_binary_file.name)['found strings']
        large_binary_file.close()
        is_there = (0, 'a'*test_chunk_size*2 + 'b'*100) in found_strings
        self.assertEqual(len(found_strings), 1, "There are more found strings than possible.")
        self.assertTrue(is_there, "String not in found_strings.")

    def test_find_strings_with_right_index(self):
        string_finder = CommonAnalysisStrings(chunk_size=test_chunk_size)
        large_binary_file = NamedTemporaryFile()
        with open(large_binary_file.name, 'wb') as f:
            f.write(b'\x00'*test_chunk_size + b'b'*100)
        found_strings = string_finder.analyze_file(large_binary_file.name)['found strings']
        large_binary_file.close()
        self.assertIn((test_chunk_size, 'b'*100), found_strings)

    @unittest.skip('only for performance test')
    def test_find_strings_in_large_test_file(self):
        string_finder = CommonAnalysisStrings(chunk_size=test_chunk_size)
        with NamedTemporaryFile() as tmp:
            with open(tmp.name, 'wb') as f:
                for i in range(1024*1024*10):
                    f.write(random.choice(string.printable).encode('utf-8'))
            found_strings = string_finder.analyze_file(tmp.name)['found strings']
            self.assertEqual(0, found_strings[0][0])
