

import transactionutils
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()


parser.add_argument("n_lines", type=int, default=1000)
parser.add_argument("amount_range", default="-50:3000")
parser.add_argument("perc_empty", type=float, default=0.00)
parser.add_argument("perc_withdraw", type=float, default=0.50)
parser.add_argument("output_path", type=Path, default=Path.cwd())
args = parser.parse_args()

f_args = {
    "n_lines": args.n_lines,
    "amount_range": range( *args.amount_range.split( ":" ) ),
    "perc_empty": args.perc_empty,
    "perc_withdraw": args.perc_withdraw,
    "perc_withdraw": args.perc_withdraw,
}


file = transactionutils.TransactionTester.create_test_file( **f_args )

file.rename( args.output_path / file.name )

print(file)
