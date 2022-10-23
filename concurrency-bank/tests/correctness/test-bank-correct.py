import argparse
from pathlib import Path
import transactionutils

import logging
logging.getLogger().setLevel(logging.INFO)

parser = argparse.ArgumentParser()

parser.add_argument("balance", type=int)
parser.add_argument("husband", type=Path)
parser.add_argument("wife", type=Path)

args = parser.parse_args()

if any(
    map(lambda file: not file.exists(), (args.husband, args.wife))
):
    print("Error from test: All files must exist!")
    exit(1)

if not (binary := Path("../../bank")).exists():
    print("bank executable does not exist")
    exit(1)

if transactionutils.TransactionTester(binary).run_and_test_output(
    args.balance, args.husband.absolute(), args.wife.absolute()
):
    print("Passed")
    exit(0)
else:
    print("Failed")
    exit(1)
