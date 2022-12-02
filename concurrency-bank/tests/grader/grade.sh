if [[ -z $1 ]]; then
    echo "Source directory unset: Using cwd"
    src_dir="$(realpath -s .)"
else
    src_dir="$(realpath -s "$1")"
fi

if [[ -z $2 ]]; then
    echo "test directory unset: Using default"
    test_dir="$(realpath -s "../..")"
else
    test_dir="$(realpath -s "$2")"
fi

if [[ -z $3 ]]; then
    echo "Output directory unset: Using src_dir/out"
    mkdir -p "$src_dir"/out
    out_dir="$src_dir"/out
else
    test_dir="$(realpath -s "$3")"
fi

log_file="$out_dir"/result.log

function get_test_score() {
    local score=$1
    if [[ $score -ge 1 && $score -le 10 ]]; then
        echo 25
    elif [[ $score -ge 11 && $score -le 18 ]]; then
        echo 55
    elif [[ $score -eq 19 ]]; then
        echo 110
    else
        echo 0
        return 1
    fi

}

