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
    out_dir="$(realpath -s "$3")"
fi

global_log="$out_dir/all.log"
global_scores="$out_dir/all.csv"

compile_penalty=10
late_penalty=20

csv_header="name, Compiled correctly, Late, Test 1, Test 2, Test 3, Test 4, Test 5, Test 6, Test 7, Test 8, Test 9, Test 10, Test 11, Test 12, Test 13, Test 14, Test 15, Test 16, Test 17, Test 18, Test 19, Total"

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

    if [[ -f "$out_dir/$name.done" ]]; then
        echo "Skipping already completed test for $name" | tee -a "$global_log"
        return 0
    fi

    rm "$out_dir/$name.output" 2> /dev/null
    rm "$out_dir/$name.log" 2> /dev/null

    rm "$test_folder/bank" 2> /dev/null
    rm "$test_folder"/bank 2> /dev/null

    # compile here
    compile_out=$(gcc "$src_file" -Wall --output "$test_folder"/bank 2>&1)
    local compile_stat=$?
    compile_out_len=$(echo $compile_out | wc -c)

    if [ $compile_stat -ne 0 ]; then
        echo "Warning: could not compile $(basename $src_file): Return code: $compile_stat" | tee -a "$global_log" "$local_log"
        echo "$compile_out" >> "$local_log"
        record="$record, N"

    elif [[ $compile_out_len -gt 5  ]]; then
        echo "Warning: $(basename $src_file) compiled with $compile_out_len lines of warnings"
        echo "$compile_out" >> "$local_log"
        record="$record, N"
    else
        echo "Info: Code compiled successfully" | tee -a "$local_log" "$global_log"
        record="$record, Y"
    fi

    if [[ $name == *LATE* ]]; then
        record="$record, Y"
    else
        record="$record, N"
    fi

    for n in {1..19}; do

        run_test "$test_folder" $n "$name" "$local_log"

        if [[ $? -eq 0 ]]; then
            test_result=$(get_test_score "$n")
            echo "score earned: $test_result" | tee -a "$local_log"
            score=$(echo "scale=2; $test_result + $score" | bc -l)
        else
            test_result=0

            for f in "$test_folder"/tests-out/$n.*; do

                echo -e "\n$(basename "$f")" >> "$out_dir/$name.output"
                cat "$f" >> "$out_dir/$name.output"
                echo -e "\n" >> "$out_dir/$name.output"

            done
        fi

        record="$record, $test_result"

    done

    echo "Original score: $score" | tee -a "$local_log"

    if [[ $compile_out_len -gt 1 && $compile_stat -eq 0 ]]; then
        echo "Penalty for compilation with warnings: -$compile_penalty"
        score=$(echo "scale=2; $score - $compile_penalty" | bc -l)
    fi

    if [[ $name == *LATE* ]]; then
        echo "Penalty for late submission: -$late_penalty"
        score=$(echo "scale=2; $score - $late_penalty" | bc -l)
    fi

    # reset score to 0 if negative
    if [[ $(echo "scale=4; $score < 0" | bc -l) -eq 1 ]]; then
        score=0
    fi

    record="$record, $score"
    echo "$record" >> "$global_scores"

    echo "$score" > "$out_dir/$name.score"

    echo "Final score: $score" | tee -a "$local_log"

    touch "$out_dir/$name.done"

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
