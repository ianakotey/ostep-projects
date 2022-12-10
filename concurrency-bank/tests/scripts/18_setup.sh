
# echo $0
# exit 1

# SCRIPT_PATH=$(dirname "$(realpath -s "$0")")
old_path=$(pwd -P)
SCRIPT_PATH=$( cd "$(dirname "$0")" ; pwd -P )

o="/tmp/"
f1="mixed_trans_18_1.txt"
f2="mixed_trans_18_2.txt"

if ! [[ -w $o$f1 ]]; then
    echo "Generating random file for testing"
    "$SCRIPT_PATH/../correctness/generate_file.py" -f $f1 -o $o -n 1000000 -r "\-30000:30000" -pe 0.30 -pw 0.20
fi

if ! [[ -w $o$f2 ]]; then
    echo "Generating random file for testing"
    "$SCRIPT_PATH/../correctness/generate_file.py" -f $f2 -o $o -n 1000000 -r "\-30000:30000" -pe 0.30 -pw 0.50
fi

ln -sf $o$f1 /tmp/Husband.txt

ln -sf $o$f2 /tmp/Wife.txt