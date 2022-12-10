#! /usr/bin/python3

import argparse
from pathlib import Path
from typing import List, Sequence, Tuple
import transactionutils

import logging

logging.getLogger().setLevel(logging.INFO)

parser = argparse.ArgumentParser()


parser.add_argument("binary", type=Path)
parser.add_argument("balance", type=int)
parser.add_argument("husband", type=Path)
parser.add_argument("wife", type=Path)
parser.add_argument("-c", "--custom", action="store_true")

args = parser.parse_args()


files: Tuple[Path,...] = tuple(
    map(lambda file: file.absolute(), (args.binary, args.husband, args.wife))
)


def verify_concurrency_nop(output: List[transactionutils.TransactionRecord]) -> bool:
    logging.debug("Using null concurrency test")
    return True


def verify_concurrency(output: List[transactionutils.TransactionRecord]) -> bool:
    """
    Assert that a series of transactions were interleaved
    """
    logging.debug(f"running concurrency test on {len(output)} records")
    quart = output[:(len(output)>>2)]
    return sorted(quart, key=lambda x: x.user) != quart


if args.custom:
    logging.debug(f"Using multithreaded analyzer")
    validator = verify_concurrency
else:
    validator = verify_concurrency_nop

for file in files:
    if not file.exists():
        print(f"File: {file} does not exist")
        exit(1)

if not (binary := Path(args.binary).absolute()).exists():
    print("bank executable does not exist")
    exit(1)

if transactionutils.TransactionTester(binary).run_and_test_output(
    args.balance, args.husband.absolute(), args.wife.absolute(),
    validator
):
    print("Passed")
    exit(0)
else:
    print("Failed")
    exit(1)
