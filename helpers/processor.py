import re
import os
import glob
import argparse
from typing import List

class CustomFilterTransform:
    def __init__(self):
        self.seen = set()

    def transform(self, line):
        line = line.strip()
        if len(line) > 0 and not line.startswith('#') and line not in self.seen and (self.is_domain(line) or self.is_ip(line)):
            self.seen.add(line)
            return line + '\n'
        return None

    def is_domain(self, domain):
        pattern = r'^([a-z0-9]+(-[a-z0-9]+)*\.)*[a-z0-9]+\.[a-z]{2,}$'
        return bool(re.match(pattern, domain))

    def is_ip(self, ip):
        pattern = r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9]?[0-9])\.(25[0-5]|2[0-4][0-9]|[01]?[0-9]?[0-9])\.(25[0-5]|2[0-4][0-9]|[01]?[0-9]?[0-9])\.(25[0-5]|2[0-4][0-9]|[01]?[0-9]?[0-9])$'
        return bool(re.match(pattern, ip))

def start(files: List[str], output_file: str):
    filter_obj = CustomFilterTransform()

    with open(output_file, 'w') as out_file:
        for file_name in files:
            with open(file_name, 'r') as in_file:
                for line in in_file.readlines():
                    res = filter_obj.transform(line)
                    if res is not None:
                        out_file.write(res)

    print('Processing completed!')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Read files and apply filtering')
    parser.add_argument('files', metavar='F', type=str, nargs='*', help='an input file or directory for processing')
    parser.add_argument('--out', dest='output_file', default='../output.txt', help='the output file (default: output.txt)')
    args = parser.parse_args()

    files = []
    for path in args.files:
        if os.path.isdir(path):
            files.extend(glob.glob(path + '/*.txt'))
        else:
            files.append(path)

    start(files, args.output_file)
