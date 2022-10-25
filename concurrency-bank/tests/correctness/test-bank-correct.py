#! /usr/bin/python3

import argparse
from pathlib import Path
import transactionutils

import logging

logging.getLogger().setLevel(logging.INFO)

parser = argparse.ArgumentParser()


parser.add_argument("binary", type=Path)
parser.add_argument("balance", type=int)
parser.add_argument("husband", type=Path)
parser.add_argument("wife", type=Path)

args = parser.parse_args()


files: tuple[Path] = tuple(
    map(lambda file: file.absolute(), (args.binary, args.husband, args.wife))
)

for file in files:
    if not file.exists():
        print(f"File: {file} does not exist")
        exit(1)

if not (binary := Path(args.binary).absolute()).exists():
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
