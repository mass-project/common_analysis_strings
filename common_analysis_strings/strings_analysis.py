from common_analysis_base import AnalysisPluginFile
from common_helper_files import get_directory_for_filename, get_version_string_from_git, read_in_chunks

import re
import string
from collections import namedtuple

system_version = get_version_string_from_git(get_directory_for_filename(__file__))

class StringMatch:
    def __init__(self, start=0, string=''):
        self.start = start
        self.string = string

    def __add__(self, other):
        if len(self.string) == 0:
            return StringMatch(other.start, other.string)
        if len(other.string) == 0:
            return StringMatch(self.start, self.string)

        if self.start <= other.start:
            return StringMatch(self.start, self.string + other.string)
        else:
            return StringMatch(other.start, other.string + self.string)

    def __len__(self):
        return len(self.string)

    def get_plain_tuple(self):
        return (self.start, self.string)

    def shift_start_by(self,offset):
        self.start += offset

def _check_match(match):
    if match:
        return StringMatch(match.start(), match.group().decode('utf-8'))
    else:
        return StringMatch(0,'')

default_chunk_size = 64 * 1024 * 1024

class CommonAnalysisStrings(AnalysisPluginFile):
    def __init__(self, min_length=4, printable=string.printable, chunk_size=default_chunk_size):
        super(CommonAnalysisStrings, self).__init__(system_version)
        self.min_length = min_length
        self.printable = printable
        pattern_templ = '[{}]{{{},}}'
        self.pattern_templ = pattern_templ
        printable_pattern = pattern_templ.format(self.printable, self.min_length)
        self.string_re = re.compile(printable_pattern.encode('utf-8'))
        self.chunk_size = chunk_size


    def analyze_file(self, file_path):
        with open(file_path, 'rb') as f:
            result = self.prepare_analysis_report_dictionary()
            result['found strings'] = self._find_from_file_obj(f)
            return result

    def _handle_begin_of_string(self,data):
        start_pattern = '[{}]+'.format(self.printable)
        match = re.match(start_pattern.encode('utf-8'), data)
        return _check_match(match)

    def _handle_end_of_string(self,data):
        end_pattern = '[{}]+\Z'.format(self.printable)
        match = re.search(end_pattern.encode('utf-8'), data)
        return _check_match(match)

    def _find_from_file_obj(self,file_obj):
        found_strings = []
        offset = 0
        cached = StringMatch()
        for data in read_in_chunks(file_obj, self.chunk_size):
            left_boundary = self._handle_begin_of_string(data)
            left_boundary.shift_start_by(offset)

            right_boundary = self._handle_end_of_string(data)
            right_boundary.shift_start_by(offset)

            if len(cached + left_boundary) >= self.min_length:
                match = cached + left_boundary
                if len(left_boundary) < len(data):
                    found_strings.append(match.get_plain_tuple())
                    cached = right_boundary
                else: 
                    cached = match
            else:
                cached = right_boundary

            data = data[len(left_boundary):len(cached)-1]

            for mo in self.string_re.finditer(data):
                start = offset + mo.start()
                match = mo.group().decode('utf-8')
                found_strings.append((start, match))
            offset += self.chunk_size

        if len(cached) != 0:
            found_strings.append(cached.get_plain_tuple())

        return found_strings
