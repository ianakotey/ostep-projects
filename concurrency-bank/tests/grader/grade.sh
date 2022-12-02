
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

global_log="$out_dir"/all.log
global_scores="$out_dir"/all.csv

csv_header="name, Test 1, Test 2, Test 3, Test 4, Test 5, Test 6, Test 7, Test 8, Test 9, Test 10, Test 11, Test 12, Test 13, Test 14, Test 15, Test 16, Test 17, Test 18, Test 19"

function get_test_score() {
    local score=$1
    if [[ $score -ge 1 && $score -le 10 ]]; then
        echo 2.5
    elif [[ $score -ge 11 && $score -le 18 ]]; then
        echo 5.5
    elif [[ $score -eq 19 ]]; then
        echo 11
    else
        echo 0
        return 1
    fi

}

function run_test() {
    local test_folder=$1
    local test_num=$2
    local name=$3
    local local_log=$4

    old_folder=$(pwd)

    if ! cd "$test_folder"; then
        echo "Warning: unable to move to test folder. Aborting test for $name"
        return
    fi

    echo -n "Running test $test_num for $name..." | tee -a "$local_log" "$global_log"
    output=$("$test_folder"/test-bank.sh -t "$test_num")
    local test_rc=$?

    echo "$output" >> "$out_dir/$name.output"

    if [[ $test_rc -eq 0 ]]; then
        echo "passed" | tee -a "$local_log" "$global_log"
        cd "$old_folder" || return 0
        return 0
    else
        echo "failed" | tee -a "$local_log" "$global_log"
        cd "$old_folder" || return 1
        return 1
    fi

}

# Grade an individual folder
# Params:
#   src_file - a source file
#   test_folder - a concurrency-bank subfolder of the ostep-projects repo
#   local_log - file to log grading logs
# Returns: non-zero error code of gcc if compilation failed
function grade_submission() {
    local src_file="$1"
    local test_folder="$2"
    local local_log="$3"
    local score=0

    name=$(basename  -s .c "$src_file")
    local record="$name"

    echo "Beginning grading for $name" | tee -a "$local_log" >> "$global_log"

    rm "$out_dir/$name.output" 2> /dev/null
    rm "$out_dir/$name.log" 2> /dev/null

    rm "$test_folder/bank" 2> /dev/null
    rm "$test_folder"/bank 2> /dev/null

    # compile here
    compile_out=$(gcc "$src_file" -Wall -Werror --output "$test_folder"/bank 2>&1)
    local compile_stat=$?
    if [ $compile_stat -ne 0 ]; then
        echo "Warning: could not compile" $"$src_file" ": Return code: $compile_stat" | tee -a "$global_log" "$local_log"
        echo "$compile_out" | tee -a "$local_log"
    fi

    for n in {1..19}; do

        run_test "$test_folder" $n "$name" "$local_log"

        if [[ $? -eq 0 ]]; then
            test_result=$(get_test_score "$n")
            echo "score earned: $test_result" | tee -a "$local_log"
            score=$(echo "scale=2; $test_result + $score" | bc -l)
        else
            test_result=0
        fi

        record="$record,$test_result"

    done

    echo "$score" > "$out_dir/$name.score"
    echo "$record" >> "$global_scores"

    echo "Final score: $score" | tee -a "$local_log"

}

# Grade all tests in the folder provided
# Params: folder - a directory with source files
# Returns: nothing
function grade_all() {
    local code_folder=$1
    local test_folder=$2

    rm "$global_log" 2> /dev/null
    rm "$global_scores" 2> /dev/null

    echo "$csv_header" >> "$global_scores"

    for code_file in "$code_folder"/*.c; do

        local_log="$out_dir"/"$(basename -s .c "$code_file")".log
        grade_submission "$code_file" "$test_folder" "$local_log"

    done

}

grade_all "$src_dir" "$test_dir"
