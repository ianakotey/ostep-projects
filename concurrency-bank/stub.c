/*

! should be compiled using -lpthread -lrt flags

 */

#include <pthread.h>  // POSIX thread
#include <stdio.h>    // C I/O library
#include <stdlib.h>   // C standard library
#include <sys/wait.h> // declarations for waiting
#include <unistd.h>   // UNIX standard symbolic constants and types


/**
 * An account is a structure that represents a bank account.
 * @property {int} balance - The amount of money in the account.
 */
typedef struct __account {
    int balance;
} account;

/**
 * The type of transaction.
 */
typedef enum __transaction_t { Withdraw, Deposit, Unknown } transaction_t;

/**
 * A transaction is a structure that contains a transaction type and an amount.
 * @property {transaction_t} transactionType - The type of transaction.
 * @property {int} amount - The amount of the transaction.
 */
typedef struct __transaction {
    transaction_t transactionType;
    int amount;
} transaction;

/**
 * A transactionQueue is a struct that contains a long and a pointer to a transaction.
 * @property {long} size - The number of transactions in the queue.
 * @property {transaction} transactions - an array of transactions
 */
typedef struct __transactionQueue {
    long size;
    transaction *transactions;

} transactionQueue;

/**
 * ExecuteTransactionsStruct is a struct that contains a pointer to an account and a pointer to a
 * transactionQueue.
 * @property {account} transactingAccount - The account that is currently being transacted.
 * @property {transactionQueue} currentTransactionQueue - A queue of transactions that are to be
 * executed.
 */
typedef struct __executeTransactionsStruct {
    account *transactingAccount;
    transactionQueue *currentTransactionQueue;

} executeTransactionsStruct;

void *parseTransactions( void *voidFileName );
transaction createTransaction( char *transactionRecord );
void *executeTransactions( void */* A void pointer to the executeTransactionsStruct struct. */
voidExecuteTransactionsStruct );
void processTransaction( account *transactingAccount, transaction *currentTransaction );
int deposit( void *account, int amount );
int withdraw( void *account, int amount );



/*
    The definitions below are just used as example code.
    Your code will have to actually read data from files to get the data
    ! Remove them!
*/
#define IS_WITHDRAWAL 1
#define AMOUNT_READ 1
#define THERE_IS_DATA_IN_FILE_1 1
#define THERE_IS_DATA_IN_FILE_2 1


int main( int argc, char *argv [] ) {

    account *theirAccount;


    // Major step 1
    // Print the opening account balance
    //   in the format specified
    printf( "<Account Balance as specified>" );


    // Major step 2
    // Read and process transactions in separate threads
    // ...


    // Major step 4
    // Print the closing account balance 
    //   in the format specified
    printf( "<Account Balance as specified>" );


    return 0;
}




/**
 * It reads a file, and returns a struct containing the number of transactions in the file, and an
 * array of transactions
 *
 * Args:
 *   voidFileName (void): THe name of the file.
 *
 * Returns:
 *   A void pointer to a transactionQueue struct.
 */
void *parseTransactions( void *voidFileName ) {
    // ! Warning: This value is invalid. Do not use!
    return ( void * ) 0;
}

/**
 * Create a transaction struct/object from a 'string'
 *
 * Args:
 *   transactionRecord (char): A string containing the transaction type and amount.
 *
 * Returns:
 *   A transaction struct.
 */
transaction createTransaction( char *transactionString ) {
    // ! Warning: This value is invalid. Do not use!
    return *( ( transaction * ) 0 );
}

/**
 * Process a queue of transactions
 *
 * Args:
 *   voidExecuteTransactionsStruct (void): a void pointer to the executeTransactionsStruct struct
 */
void *executeTransactions( void *voidExecuteTransactionsStruct ) {
    // ! Warning: This value is invalid. Do not use!
    return ( void * ) 0;
}

/**
 * "This function takes a pointer to an account and a pointer to a transaction,
 * and then processes the transaction on the account."
 *
 * Args:
 *   transactingAccount (account): This is a pointer to account that is being transacted on.
 *   currentTransaction (transaction): a pointer to a transaction struct
 */
void processTransaction( account *transactingAccount, transaction *currentTransaction ) { }

/**
 * It withdraws money from the provided account
 *
 * Args:
 *   account (void *): The account to be used
 *   amount  (int): the amount to be withdrawn
 */
int withdraw( void *account, int amount ) {
    return 0;
}

/**
 * Deposit an amount into provided account
 *
 * Args:
 *   account (void *): The account to be used
 *   amount  (int): The amount to be deposited
 */
int deposit( void *account, int amount ) {
    return 0;
}