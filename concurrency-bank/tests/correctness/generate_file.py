#! /usr/bin/python3

from typing import Optional
import transactionutils
import argparse
from pathlib import Path
import shutil


parser = argparse.ArgumentParser()

parser.add_argument( "-n", "--n_lines", type=int, default=1000, required=False )
parser.add_argument( "-r", "--amount_range", default="-50:3000", required=False )
parser.add_argument( "-pe", "--perc_empty", type=float, default=0.00, required=False )
parser.add_argument( "-pw", "--perc_withdraw", type=float, default=0.50, required=False )
parser.add_argument( "-o", "--output_path", type=Path, default=Path.cwd(), required=False )
parser.add_argument( "-f", "--file_name", type=str, default=None, required=False )
args = parser.parse_args()

f_args = {
    "n_lines": args.n_lines,
    "amount_range": range( *list( map( lambda x: int(x), args.amount_range.lstrip('\\').split( ":" ) ) ) ),
    "perc_empty": args.perc_empty,
    "perc_withdraw": args.perc_withdraw,
    "perc_withdraw": args.perc_withdraw,
}

file = transactionutils.TransactionTester.create_test_file( **f_args )

out_file = args.output_path / (args.file_name if args.file_name else file.name)
shutil.move( file, out_file )

print( out_file )
