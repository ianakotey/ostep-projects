
# echo $0
# exit 1
SCRIPT_PATH=$(dirname "$(realpath -s "$0")")
o="/tmp/"
f="valid_trans_10000_0_500000.txt"

if ! [[ -w $o$f ]]; then
    $SCRIPT_PATH/../correctness/generate_file.py -f $f -o $o -n 10000 -r "0:300000"
else
    echo $o$f already exists!
fi