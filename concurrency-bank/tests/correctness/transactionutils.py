#! /usr/bin/python3

from __future__ import annotations
import binascii

from dataclasses import dataclass
from enum import Enum, auto, unique
import logging
from math import floor
from pathlib import Path
from collections import deque
from random import randint
from subprocess import PIPE, Popen, TimeoutExpired
from sys import stdout
from typing import Iterable, Optional
import re

from tempfile import NamedTemporaryFile

logging.getLogger().setLevel(logging.INFO)


regex = re.compile(r"test (\d{1,2}):.*(passed|failed).*$", re.MULTILINE)


transaction_data_pattern = re.compile(
    r"^(?P<type>deposit|withdraw)+ (?P<amount>-{0,1}\d+)$"
)
transaction_record_pattern = re.compile(
    r"^(?P<type>Deposit|Withdraw): (?P<amount>-{0,1}\d+), "
    r"User: (?P<user>Husband|Wife), "
    r"(?:Account balance after: (?P<balance>-{0,1}\d+)|(?P<status>Transaction (?:declined|failed)))$"
)


@unique
class TransactionType(Enum):
    WITHDRAWAL = auto()
    DEPOSIT = auto()


@dataclass()
class TransactionRecord:
    type: TransactionType
    user: str
    amount: int
    balance_after: Optional[int]

    @classmethod
    def from_str(cls, transaction_record: str) -> TransactionRecord:

        if (m := transaction_record_pattern.match(transaction_record)) is None:

            raise ValueError(
                f"""String "{transaction_record}" does not match """
                f"""the required pattern "<{transaction_record_pattern}>"."""
            )

        return cls(
            TransactionType.WITHDRAWAL
            if m["type"] == "Withdraw"
            else TransactionType.DEPOSIT,
            m["user"],
            int(m["amount"]),
            int(m["balance"]) if m["balance"] is not None else None,
        )

    @classmethod
    def from_iter(cls, iter: Iterable[str]) -> Iterable[TransactionRecord]:
        return (cls.from_str(line) for line in iter)

    @classmethod
    def from_file(cls, file: Path) -> Iterable[TransactionRecord]:
        return cls.from_iter(file.open())


@dataclass()
class TransactionData:
    type: TransactionType
    amount: int

    @classmethod
    def from_str(cls, transaction_str: str) -> Optional[TransactionData]:
        if len(transaction_str) == 0:
            return None
        if (m := transaction_data_pattern.match(transaction_str)) is None:

            raise ValueError(
                f"""String "{transaction_str.strip(chr(10))}" does not match the required pattern "<withdraw|deposit int>"."""
            )

        return cls(
            TransactionType.WITHDRAWAL
            if m["type"] == "withdraw"
            else TransactionType.DEPOSIT,
            int(m["amount"]),
        )

    @classmethod
    def from_iter(
        cls, iter: Iterable[str]
    ) -> Iterable[Optional[TransactionData]]:
        return (cls.from_str(line) for line in iter)

    @classmethod
    def from_file(cls, file: Path) -> Iterable[Optional[TransactionData]]:
        return cls.from_iter(filter(lambda l: l != "\n", file.open()))


@dataclass()
class TransactionTester:
    binary: Path

    @classmethod
    def from_source(
        cls, source: Path, binary_location: Optional[Path] = None
    ) -> TransactionTester:
        if not source.exists():
            raise ValueError("Source file does not exist!")
        if not source.is_file():
            raise ValueError("Source file cannot be a directory!")

        match binary_location:
            case None:
                binary_location = source.parent
            case loc:
                if not loc.exists():
                    raise ValueError("Binary output location does not exist")
                if not loc.is_dir():
                    raise ValueError("Binary output location cannot be a file!")

        with Popen(
            [
                "gcc",
                source.absolute(),
                "-Wall",
                "-Werror",
                "-lpthread",
                "-O",
                "-o",
                (result := binary_location / source.stem),
            ],
            shell=False,
            cwd=source.parent,
            stdout=PIPE,
            stderr=PIPE,
        ) as comp:
            try:
                out, _ = comp.communicate(timeout=10)
                if out.strip() != b"":
                    logging.error(out)
                    logging.error(_)

                if comp.returncode != 0:
                    raise ValueError(
                        f"Compilation failed with return code {comp.returncode}"
                    )

                if not result.exists():
                    raise ValueError(
                        "Compilation suceeded but binary not found."
                    )

                return TransactionTester(result)

            except TimeoutExpired as exc:
                logging.warning(f"Code compilation timed out")
                comp.terminate()
                raise ValueError("Code failed to compile") from exc

    def run_and_test_output(
        self, start_balance: int, husband: Path, wife: Path
    ) -> bool:
        husband_queue = deque(filter(None, TransactionData.from_file(husband)))
        wife_queue = deque(filter(None, TransactionData.from_file(wife)))
        with Popen(
            [self.binary, str(start_balance), husband, wife],
            text=True,
            shell=False,
            stdout=PIPE,
            cwd=self.binary.parent,
            stderr=PIPE,
        ) as test_runner:  #
            logging.debug(f"Beginning test...")
            try:
                out, _ = test_runner.communicate(timeout=20)
                out_lines = out.splitlines()
                match len(out_lines):
                    case 0 | 1:
                        logging.error(
                            f"Invalid number of output lines: {len(out_lines)}"
                        )
                        return False
                    case 2:
                        return len(husband_queue) + len(
                            wife_queue
                        ) == 0 and out_lines == [
                            f"Opening balance: {start_balance}",
                            f"Closing balance: {start_balance}",
                        ]
                    case _:

                        out_queue = deque(
                            TransactionRecord.from_iter(out_lines[1:-1])
                        )

                        return self.verify_transactions(
                            start_balance, husband_queue, wife_queue, out_queue
                        )

            except TimeoutExpired:
                logging.critical("Timed out on test")

        logging.info(
            f"test: {self.binary} {start_balance} {husband} {wife} completed"
        )

        return False

    def verify_transactions(
        self,
        start_balance: int,
        husband_queue: deque[TransactionData],
        wife_queue: deque[TransactionData],
        out_queue: deque[TransactionRecord],
    ) -> bool:

        balance: int = start_balance

        for transaction_record in out_queue:
            match transaction_record:
                case trans_r if trans_r.user == "Husband":
                    try:
                        husband_trans = husband_queue.popleft()
                    except IndexError:
                        return False

                    if not self.verify_transaction(
                        balance, trans_r, husband_trans
                    ):
                        return False
                    else:
                        balance = (
                            trans_r.balance_after
                            if trans_r.balance_after is not None
                            else balance
                        )

                case trans_r if trans_r.user == "Wife":
                    try:
                        wife_trans = wife_queue.popleft()
                    except IndexError:
                        return False
                    if not self.verify_transaction(
                        balance, trans_r, wife_trans
                    ):
                        return False
                    else:
                        balance = (
                            trans_r.balance_after
                            if trans_r.balance_after is not None
                            else balance
                        )
                case _:  # Somehow, an unknown user may show up
                    return False

        return True

    def verify_transaction(
        self,
        balance: int,
        transaction_record: TransactionRecord,
        transaction: TransactionData,
    ) -> bool:

        if transaction_record.amount != transaction.amount:
            logging.error("Transaction amount mismatch")
            logging.info(f"Amount in record: {transaction_record.amount}")
            logging.info(f"Amount in transaction: {transaction.amount}")
            return False

        if (
            transaction_record.amount < 0
            and transaction_record.balance_after != None
        ):
            logging.error(
                f"Transaction amount negative ({transaction_record.amount}) yet not declined"
            )
            return False

        match (transaction, transaction_record):
            # Test 1: Amount match
            case (x, y) if x.amount != y.amount:
                logging.error("Test 1 failed!")
                logging.info(f"current balance: {balance}")
                logging.info(f"Transaction under test: {transaction}")
                logging.info(
                    f"Transaction record being verified: {transaction_record}"
                )
                return False
            # Test 2: Negative amounts were rejected
            case (x, y) if x.amount < 0 and y.balance_after is not None:
                logging.error("Test 2 failed!")
                logging.info(f"current balance: {balance}")
                logging.info(f"Transaction under test: {transaction}")
                logging.info(
                    f"Transaction record being verified: {transaction_record}"
                )
                return False
            # Test 3: No underflow allowed
            case (
                TransactionData(TransactionType.WITHDRAWAL, _) as x,
                y,
            ) if x.amount > balance and y.balance_after is not None:
                logging.error("Test 3 failed!")
                logging.info(f"current balance: {balance}")
                logging.info(f"Transaction under test: {transaction}")
                logging.info(
                    f"Transaction record being verified: {transaction_record}"
                )
                return False
            # Test 4: Negative transactions not allowed
            case (x, y) if x.amount < 0 and y.balance_after is not None:
                logging.error("Test 4 failed!")
                logging.info(f"current balance: {balance}")
                logging.info(f"Transaction under test: {transaction}")
                logging.info(
                    f"Transaction record being verified: {transaction_record}"
                )
                return False
            # Test 5: Check for correct balance after withdrawal
            case (
                TransactionData(TransactionType.WITHDRAWAL, _) as x,
                y,
            ) if 0 <= x.amount < balance and y.balance_after != balance - x.amount:
                logging.error("Test 5 failed!")
                logging.info(f"current balance: {balance}")
                logging.info(f"Transaction under test: {transaction}")
                logging.info(
                    f"Transaction record being verified: {transaction_record}"
                )
                return False

            # Test 6: Check for correct balance after deposit
            case (
                TransactionData(TransactionType.DEPOSIT, a) as x,
                y,
            ) if a > 0 and y.balance_after != balance + x.amount:
                logging.error("Test 6 failed!")
                logging.info(f"current balance: {balance}")
                logging.info(f"Transaction under test: {transaction}")
                logging.info(
                    f"Transaction record being verified: {transaction_record}"
                )
                return False

        return True

    def run_tests(self):
        if not self.binary.exists():
            logging.critical("binary does not exist passed")
            return

        self.run_basic_tests()

    # Todo: cleanup and stuff
    # Critical: Violation of single responsibility
    def run_basic_tests(self):
        for t_num in range(1, 11):  # TODO: Remove magic numbers
            with Popen(
                f"""./test-bank.sh -t {t_num}""",
                text=True,
                shell=True,
                stdout=PIPE,
                cwd=self.binary.parent,
                stderr=PIPE,
            ) as test_runner:  #
                logging.debug(f"Executed basic test #{t_num}")
                try:
                    out, _ = test_runner.communicate(timeout=20)
                    out_lines = out.splitlines()
                    # print( out, file=stdout )
                    # print( _, file=stdout )

                    if match := regex.match(out):
                        num, status = match.group(1, 2)

                        if status == "passed":
                            logging.info(f"Passed basic test {num}/10")
                            logging.debug(
                                f"Pass message: {'None' if len(out_lines) == 0 else out_lines[0]}"
                            )
                            # solo_test[ 'Passed' ] += 1
                            # solo_test[ 'Remarks' ].append( f"Passed test {num}" )
                        else:
                            logging.error(f"Failed basic test {num}/10")
                            logging.debug(
                                f"Failure message: {'None' if len(out_lines) == 0 else out_lines[0]}"
                            )
                            # solo_test[ 'Failed' ] += 1
                            # solo_test[ 'Remarks' ].append( f"Failed test {num}" )
                    else:
                        # other possible failure
                        logging.error(f"Failed basic test {t_num}/10")
                        # unnecessary allocation in splitlines, I know
                        logging.debug(
                            f"Failure message: {'None' if len(out_lines) == 0 else out_lines[0]}"
                        )

                except TimeoutExpired:
                    logging.critical(f"Timed out on test {t_num}/10")
                    pass

    def test_random_input(
        self,
        start_balance: int,
        husband_transactions: int,
        wife_transactions: int,
        perc_empty: float = 0.20,
        perc_withdraw=0.40,
    ) -> bool:

        husband = self.create_test_file(
            husband_transactions,
            perc_empty=perc_empty,
            perc_withdraw=perc_withdraw,
        )
        wife = self.create_test_file(
            wife_transactions,
            perc_empty=perc_empty,
            perc_withdraw=perc_withdraw,
        )

        return self.run_and_test_output(start_balance, husband, wife)

    @staticmethod
    def create_test_file(
        n_lines: int,
        *,
        amount_range: range = range(0, 3_000),
        perc_empty: float = 0.20,
        perc_withdraw=0.20,
    ) -> Path:

        empty_thresh = floor(perc_empty * 100)
        withdraw_thresh = floor(perc_withdraw * 100)
        with NamedTemporaryFile(
            mode="w", prefix="test_", suffix=".txt", delete=False
        ) as file:
            for _ in range(n_lines):

                match randint(0, 100):
                    case x if x < empty_thresh:
                        file.write("\n")
                    case x if x > withdraw_thresh:
                        file.write(
                            f"withdraw {randint(amount_range.start, amount_range.stop)}\n"
                        )
                    case _:
                        file.write(
                            f"deposit {randint(amount_range.start, amount_range.stop)}\n"
                        )

            return Path(file.name)


if __name__ == "__main__":

    file_name_1 = TransactionTester.create_test_file(2_000, perc_withdraw=0.6)
    file_name_2 = TransactionTester.create_test_file(
        2_000, perc_withdraw=0.3, amount_range=range(-2000, 2000)
    )

    print(
        TransactionTester.from_source(Path("../../bank.c")).run_and_test_output(
            0, file_name_1, file_name_2
        )
    )

    # cleanup
    file_name_1.unlink(missing_ok=True)
    file_name_1.unlink(missing_ok=True)
