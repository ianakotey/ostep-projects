# Testing

In this directory, you should write the program `bank.c` and compile it into
the binary `bank` (e.g., `gcc -o bank bank.c -Wall -Werror -lpthread -O`).

After doing so, you can run the tests from this directory by running the
`test-bank.sh` script. If all goes well, you will see:

```sh
prompt> ./test-bank.sh
test 1: passed
test 2: passed
test 3: passed
test 4: passed
test 5: passed
test 6: passed
test 7: passed
test 8: passed
test 9: passed
test 10: passed
prompt>
```

Hint: You may also compile and run the tests simultaneously by running the `test-bank.sh` script.

The `test-bank.sh` script is just a wrapper for the `run-tests.sh` script in
the `tester` directory of this repository. This program has a few options; see
the relevant
[README](https://github.com/remzi-arpacidusseau/ostep-projects/blob/master/tester/README.md)
for details.
