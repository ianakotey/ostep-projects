rm bank 1>/dev/null 2>&1

gcc bank.c -o bank -Wall -Werror -lpthread

./test-bank.sh