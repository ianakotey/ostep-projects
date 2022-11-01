import transactionutils
import argparse

parser = argparse.ArgumentParser()


parser.add_argument("n_lines", type=int)
parser.add_argument("amount_range")
parser.add_argument("perc_empty", type=float)
parser.add_argument("perc_withdraw", type=float)
args = parser.parse_args()

args = {
    "n_lines": args.n_lines,
    "amount_range": range(*args.amount_range.split(":")),
    "perc_empty": args.perc_empty,
    "perc_withdraw": args.perc_withdraw,
}


file = transactionutils.TransactionTester.create_test_file(
    **args
)

print(file)



