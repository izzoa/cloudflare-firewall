import re
import os
import glob
import argparse
from typing import List
from pathlib import Path

class CustomFilterTransform:
    def __init__(self, max_entries=None):
        self.seen = set()
        self.max_entries = max_entries
        self.entry_count = 0

    def transform(self, line):
        if self.max_entries and self.entry_count >= self.max_entries:
            return None
        line = line.strip()
        if len(line) > 0 and not line.startswith('#') and line not in self.seen and (self.is_domain(line) or self.is_ip(line)):
            self.seen.add(line)
            self.entry_count += 1
            return line + '\n'
        return None

    def is_domain(self, domain):
        pattern = r'^([a-z0-9]+(-[a-z0-9]+)*\.)*[a-z0-9]+\.[a-z]{2,}$'
        return bool(re.match(pattern, domain))

    def is_ip(self, ip):
        pattern = r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9]?[0-9])\.(25[0-5]|2[0-4][0-9]|[01]?[0-9]?[0-9])\.(25[0-5]|2[0-4][0-9]|[01]?[0-9]?[0-9])\.(25[0-5]|2[0-4][0-9]|[01]?[0-9]?[0-9])$'
        return bool(re.match(pattern, ip))

def load_settings():
    settings_path = Path(__file__).parent.parent / 'settings.env'
    settings = {}
    if settings_path.exists():
        with open(settings_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    settings[key.strip()] = value.strip()
    return settings

def calculate_max_entries(settings):
    free_account = settings.get('FREE_ACCOUNT', 'false').lower() == 'true'
    max_lists = int(settings.get('MAX_LISTS', '300'))
    entries_per_list = 1000 if free_account else 5000
    return max_lists * entries_per_list

def start(files: List[str], output_file: str):
    settings = load_settings()
    max_entries = calculate_max_entries(settings) if settings else None

    filter_obj = CustomFilterTransform(max_entries=max_entries)

    with open(output_file, 'w') as out_file:
        for file_name in files:
            with open(file_name, 'r') as in_file:
                for line in in_file.readlines():
                    res = filter_obj.transform(line)
                    if res is not None:
                        out_file.write(res)

    if max_entries:
        print(f'Processing completed! Entries processed: {filter_obj.entry_count}/{max_entries}')
    else:
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
