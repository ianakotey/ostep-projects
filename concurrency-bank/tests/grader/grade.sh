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

function run_test() {
    local test_folder=$1
    local test_num=$2
    local name=$3

    local old_folder=$(pwd)

    if ! cd "$test_folder"; then
        echo "Warning: unable to move to test folder. Aborting test for $name"
        return
    fi

    echo -n "Running test $test_num for $name..."
    local output=$("$test_folder"/test-bank.sh -t "$test_num")
    local test_rc=$?

    if [[ $test_rc -eq 0 ]]; then
        echo passed
        cd "$old_folder" || return 0
        return 0
    else
        echo failed
        cd "$old_folder" || return 1
        return 1
    fi

}
    fi

    echo failed
    cd "$old_folder" || return 1

}

