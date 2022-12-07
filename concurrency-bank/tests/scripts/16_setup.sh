
# echo $0
# exit 1

# SCRIPT_PATH=$(dirname "$(realpath -s "$0")")
old_path=$(pwd -P)
SCRIPT_PATH=$( cd "$(dirname "$0")" ; pwd -P )

o="/tmp/"
f="valid_trans_16.txt"

if ! [[ -w $o$f ]]; then
    echo "Generating random file for testing"
    "$SCRIPT_PATH/../correctness/generate_file.py" -f $f -o $o -n 10000 -r "0:300000"
fi

ln -sf $o$f /tmp/Wife.txt

ln -sf "$SCRIPT_PATH/../assets/no_transactions_wel.txt" /tmp/Husband.txt