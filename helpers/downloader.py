import os
import urllib.request
import logging
import argparse
import binascii
from pathlib import Path
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)

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

def generate_filename(url):
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    domain_part = url.split('//')[-1].split('/')[0].replace('.', '_')
    return f"{domain_part}_{url_hash}.txt"

def parse_blocklists(settings):
    blocklists_str = settings.get('BLOCKLISTS', '')
    if not blocklists_str:
        return []
    urls = [url.strip() for url in blocklists_str.split(',') if url.strip()]
    return [(url, generate_filename(url)) for url in urls]

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--output_dir", default="../lists", help="Directory to save the files")
parser.add_argument("--append_crc32", action='store_true', help="Append crc32 code to output file names")
args = parser.parse_args()

# Create the directory if it doesn't exist
os.makedirs(args.output_dir, exist_ok=True)

# Load blocklists from settings.env
settings = load_settings()
files = parse_blocklists(settings)

if not files:
    logging.warning("No blocklists found in settings.env. Using default fallback lists.")
    files = [
        ('https://codeberg.org/hagezi/mirror2/raw/branch/main/dns-blocklists/wildcard/pro-onlydomains.txt', 'hagezi_multipro.txt'),
        ('https://raw.githubusercontent.com/mullvad/dns-blocklists/main/output/doh/doh_adblock.txt', 'mullvad_adblock.txt'),
        ('https://raw.githubusercontent.com/mullvad/dns-blocklists/main/output/doh/doh_privacy.txt', 'mullvad_privacy.txt'),
    ]

# Download and rename files
for url, filename in files:
    try:
        logging.info(f"Starting download of {url} to {filename}")
        response = urllib.request.urlopen(url)
        data = response.read()      # a `bytes` object
        crc32_code = binascii.crc32(data) & 0xffffffff  # compute CRC32
        filename_without_ext, extension = os.path.splitext(filename)
        if args.append_crc32:
            new_filename = os.path.join(args.output_dir, f"{filename_without_ext}-{format(crc32_code, '08x')}{extension}")
        else:
            new_filename = os.path.join(args.output_dir, filename)
        with open(new_filename, 'wb') as f:
            f.write(data)
        logging.info(f"Successfully downloaded {url} to {new_filename}")
    except Exception as e:
        logging.error(f"Error downloading {url} to {filename}: {e}")
