
# echo $0
# exit 1

# SCRIPT_PATH=$(dirname "$(realpath -s "$0")")
old_path=$(pwd -P)
SCRIPT_PATH=$( cd "$(dirname "$0")" ; pwd -P )

o="/tmp/"
f="valid_trans_15.txt"

if ! [[ -w $o$f ]]; then
    echo "Generating random file for testing"
    "$SCRIPT_PATH/../correctness/generate_file.py" -f $f -o $o -n 1000 -r "0:1000000"
fi

ln -sf $o$f "$SCRIPT_PATH/../../Husband.txt"

ln -sf "$SCRIPT_PATH/../assets/no_transactions_wel.txt" "$SCRIPT_PATH/../../Wife.txt"