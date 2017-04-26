from common_analysis_base import AnalysisPluginFile
from common_helper_files import read_in_chunks
from . import __version__

import re
import string


class StringMatch:
    def __init__(self, begin, end, content):
        self.begin = begin
        self.end = end
        self.content = content

    def __repr__(self):
        return '[{}]: ({}:{}) -> {}'.format(self.__class__.__name__, self.begin, self.end, self.content)


system_version = __version__

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
            result['found strings'] = [(m.begin, m.content) for m in self._find_from_file_obj(f)]
            return result

    def _append_found_string(self, found_strings, mo, offset):
        if mo:
            new_str_match = StringMatch(mo.start()+offset, mo.end()+offset, mo.group().decode('utf-8'))
            found_strings.append(new_str_match)
        return found_strings

    def _merge_found_strings(self, found_strings):
        filtered_findings = []
        for i in range(len(found_strings)):
            if found_strings[i].begin == found_strings[i].end:
                continue
            for j in range(i+1, len(found_strings)):
                if found_strings[i].end >= found_strings[j].begin:
                    start = found_strings[i].end - found_strings[j].begin
                    found_strings[i].content += found_strings[j].content[start:]
                    found_strings[i].end = found_strings[j].end

                    found_strings[j].begin = 0
                    found_strings[j].end = 0
                    found_strings[j].content = ''
                else:
                    break
            if len(found_strings[i].content) >= self.min_length:
                filtered_findings.append(found_strings[i])
        return filtered_findings

    def _find_from_file_obj(self, file_obj):
        found_strings = []
        offset = 0
        string_at_start = re.compile(r'^[{}]+'.format(self.printable).encode('utf-8'))
        string_at_end = re.compile(r'[{}]+$'.format(self.printable).encode('utf-8'))

        for data in read_in_chunks(file_obj, self.chunk_size):
            start_mo = string_at_start.search(data)
            end_mo = string_at_end.search(data)
            self._append_found_string(found_strings, start_mo, offset)
            self._append_found_string(found_strings, end_mo, offset)

            for mo in self.string_re.finditer(data):
                self._append_found_string(found_strings, mo, offset)

            offset += len(data)
        return self._merge_found_strings(found_strings)
