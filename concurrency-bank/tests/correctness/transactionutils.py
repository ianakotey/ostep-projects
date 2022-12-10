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
from typing import Callable, Iterable, Optional, Sequence
import re

from tempfile import NamedTemporaryFile

logging.getLogger().setLevel(logging.INFO)


regex = re.compile(r"test (\d{1,2}):.*(?:passed|failed).*$", re.MULTILINE)

opening_balance_patern = re.compile(
    r"^(?:Opening|Closing) balance: (?P<opening_balance>\d+)$", re.MULTILINE)
closing_balance_patern = re.compile(
    r"^Closing balance: (?P<closing_balance>\d+)$", re.MULTILINE)

transaction_data_pattern = re.compile(
    r"^(?P<type>deposit|withdraw)+ (?P<amount>-?\d+)$"
)
transaction_record_pattern = re.compile(
    r"^(?P<type>Deposit|Withdraw): (?P<amount>-?\d+), "
    r"User: (?P<user>Husband|Wife), "
    r"(?:Account balance after: (?P<balance>-?\d+)"
    r"|(?:Transaction (?P<status>declined|failed)))$",
    re.MULTILINE
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


        if binary_location is None:
            binary_location = source.parent

        if not binary_location.exists():
            raise ValueError("Binary output location does not exist")
        if not binary_location.is_dir():
            raise ValueError(
                "Binary output location cannot be a file!")

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
        self, start_balance: int, husband: Path, wife: Path,
        custom_check: Callable[[list[TransactionRecord]],
                               bool] = lambda _: True
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

                out, _ = test_runner.communicate(timeout=200)
                out_lines = out.splitlines()

                if (num_lines := len(out_lines)) <= 1:
                    logging.error(
                        f"Invalid number of output lines: {num_lines}"
                    )
                    return False
                else:
                    if not self.verify_transactions(
                        start_balance, husband_queue, wife_queue, out_lines,
                        custom_check
                    ):
                        return False

            except TimeoutExpired:
                logging.critical("Timed out on test")
                return False

        logging.debug(
            f"test: {self.binary} {start_balance} {husband} {wife} completed sucessfully"
        )

        return True

    def verify_transactions(
        self,
        start_balance: int,
        husband_queue: deque[TransactionData],
        wife_queue: deque[TransactionData],
        out_lines: Sequence[str],
        custom_check: Callable[[list[TransactionRecord]],
                               bool] = lambda _: True

    ) -> bool:

        balance: int = start_balance

        if opening_match := re.match(opening_balance_patern, out_lines[0]):

            if opening_balance := int(opening_match.group('opening_balance')) != balance:
                logging.info(
                    f"Start balance mismatch: found {start_balance}, expected {balance}")
                return False

        out_queue = deque(
            TransactionRecord.from_iter(out_lines[1:-1])
        )

        for transaction_record in out_queue:

            if transaction_record.user == "Husband":
                try:
                    current_trans = husband_queue.popleft()
                except IndexError:
                    return False

            elif transaction_record.user == "Wife":
                try:
                    current_trans = wife_queue.popleft()
                except IndexError:
                    return False

            else:  # Somehow, an unknown user may show up
                return False

            if not self.verify_transaction(
                balance, transaction_record, current_trans
            ):
                return False
            else:
                balance = (
                    transaction_record.balance_after
                    if transaction_record.balance_after is not None
                    else balance
                )

        if (remaining := (len(husband_queue) + len(wife_queue))) != 0:
            logging.error(f"{remaining} transactions unprocessed")
            return False

        if not custom_check(list(out_queue)):
            logging.error("Concurency test failed")
            return False

        if closing_match := re.match(closing_balance_patern, out_lines[-1]):

            if closing_balance := int(closing_match.group('closing_balance')) != balance:
                logging.info(
                    f"closing balance mismatch: found {closing_balance}, expected {balance}")
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
            logging.info(f"Current balance: {balance}")
            logging.info(f"Amount in record: {transaction_record.amount}")
            logging.info(f"Amount in transaction: {transaction.amount}")
            logging.info(f"Transaction: {transaction}")
            logging.info(f"Record: {transaction_record}")
            return False

        if (
            transaction_record.amount < 0
            and transaction_record.balance_after != None
        ):
            logging.error(
                f"Transaction amount negative ({transaction_record.amount}) yet not declined"
                f"\nRecord: {transaction_record}"
            )
            return False

        # Todo: refactor if-else ladder
        td, tr = transaction, transaction_record

        if td.amount != tr.amount:
            logging.error("Test 1 failed!")
            logging.info(f"current balance: {balance}")
            logging.info(f"Transaction under test: {transaction}")
            logging.info(
                f"Transaction record being verified: {transaction_record}"
            )
            return False

        elif td.amount < 0 and tr.balance_after is not None:
            # Test 2: Negative amounts were rejected
            logging.error("Test 2 failed!")
            logging.info(f"current balance: {balance}")
            logging.info(f"Transaction under test: {transaction}")
            logging.info(
                f"Transaction record being verified: {transaction_record}"
            )
            return False

        elif td.type == TransactionType.WITHDRAWAL and td.amount > balance and tr.balance_after is not None:
            # Test 3: No withdrawal underflow allowed
            logging.error("Test 3 failed!")
            logging.info(f"current balance: {balance}")
            logging.info(f"Transaction under test: {transaction}")
            logging.info(
                f"Transaction record being verified: {transaction_record}"
            )
            return False

        elif td.amount < 0 and tr.balance_after is not None:
            # Test 4: Negative transactions not allowed
            logging.error("Test 4 failed!")
            logging.info(f"current balance: {balance}")
            logging.info(f"Transaction under test: {transaction}")
            logging.info(
                f"Transaction record being verified: {transaction_record}"
            )
            return False

        elif td.type == TransactionType.WITHDRAWAL \
                and (0 <= td.amount < balance and tr.balance_after != balance - td.amount):
            # Test 5: Check for correct balance after withdrawal

            # Special case for withdrawal: 0 amount can either succeed or be rejected
            if td.amount == 0 and tr.balance_after in {None, balance}:
                return True

            logging.error("Test 5 failed!")
            logging.info(f"current balance: {balance}")
            logging.info(f"Transaction under test: {transaction}")
            logging.info(
                f"Transaction record being verified: {transaction_record}"
            )
            logging.info(
                f"Expected {balance - td.amount} after withdrawal: found {tr.balance_after}")
            return False

        elif td.type == TransactionType.DEPOSIT \
            and ( td.amount >= 0 and tr.balance_after != balance + td.amount):
            
            # Special case for deposit: 0 amount can either succeed or be rejected
            if td.amount == 0 and tr.balance_after in {None, balance}:
                return True
            
            # Test 6: Check for correct balance after deposit
            logging.error("Test 6 failed!")
            logging.info(f"current balance: {balance}")
            logging.info(f"Transaction under test: {transaction}")
            logging.info(
                f"Transaction record being verified: {transaction_record}"
            )
            logging.info(
                f"Expected {balance + td.amount} after deposit: found {tr.balance_after}")
            return False

        return True

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

                probability = randint(0,100)
                if probability < empty_thresh:
                    file.write("\n")
                elif probability > withdraw_thresh:
                    file.write(
                        f"withdraw {randint(amount_range.start, amount_range.stop)}\n"
                    )
                else:
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
