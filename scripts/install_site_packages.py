import os
import shutil
import sys

src_dir = os.path.abspath("site-packages")

if len(sys.argv) == 1:
    dst_dir = os.path.abspath(".venv/lib/python3.12/site-packages")
else:
    dst_dir = sys.argv[1]

for file in os.listdir(src_dir):
    src_file = os.path.join(src_dir, file)
    dst_file = os.path.join(dst_dir, file)
    if os.path.isdir(src_file):
        shutil.copytree(src_file, dst_file, dirs_exist_ok=True)
