import subprocess
import os
from pathlib import Path

from django

from db.utils.multiple_run_adder import MultipleRunAdder


os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'


TSHC_VALIDATION_OUTPUT_DIR = '/network/sequenced/MiSeq_data/TSHC/research_and_validation/v1.0.0'


output_dirs = [
    TSHC_VALIDATION_OUTPUT_DIR,
]

commandline_usage_list = []
for output_dir in output_dirs:
    p1 = subprocess.Popen(
        ['tree', '-if', 
         '-L', '4',
         '-I', '*failed*',
         output_dir], 
        stdout=subprocess.PIPE,
    )
    p2 = subprocess.Popen(
        ['grep', 'commandline'],
        stdin=p1.stdout,
        stdout=subprocess.PIPE
    )
    cmdline_files = list(map(
        lambda x: Path(x.decode().strip().replace('\\','')),
        p2.stdout.readlines()
    ))
    commandline_usage_list.extend(cmdline_files)

mra = MultipleRunAdder(commandline_usage_list[:2])
mra.update_database()
