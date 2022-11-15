#! /usr/bin/python3

import argparse
import logging
from pathlib import Path
import transactionutils

logging.getLogger().setLevel(logging.INFO)

parser = argparse.ArgumentParser()

parser.add_argument(
    "-peh",
    "--perc_empty_hus",
    type=float,
    default=0.00,
    help="Percentage of empty lines",
)
parser.add_argument(
    "-pew",
    "--perc_empty_wife",
    type=float,
    default=0.00,
    help="Percentage of empty lines",
)
parser.add_argument("-pwh", "--perc_withdraw_hus", type=float, default=0.50)
parser.add_argument("-pww", "--perc_withdraw_wife", type=float, default=0.50)
parser.add_argument("-nlh", "--num_lines_hus", type=int, default=100)
parser.add_argument("-nlw", "--num_lines_wife", type=int, default=100)


args = parser.parse_args()


if not (binary := Path("../../bank")).exists():
    print("bank executable does not exist")
    exit(1)

new_var = transactionutils.TransactionTester(binary).test_random_input(
    args.balance, args.husband.absolute(), args.wife.absolute()
)

if new_var:
    print("Passed")
    exit(0)
else:
    print("Failed")
    exit(1)
