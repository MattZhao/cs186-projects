
# Homework 4: Transactions
### CS186, UC Berkeley, Spring 2016
#### Points: [10% of your final grade](https://sites.google.com/site/cs186spring2016/home/basic-information)
#### Due: Friday Mar 18, 2016, 11:59 PM
#### Note: *This homework is to be done individually!*


## Part 0: Introductions

### Description

In this homework, you will implement a Concurrency Control Manager 
in Python, which will be used to manage access to a "key-value" store 
-- a simple kind of database.  You will be responsible to implement
the data structures and protocols for:

- Strict Two-Phase Locking (Strict 2PL)
- Deadlock Detection

This assignment will be implemented entirely in Python 2.7.
We will not be using Jupyter Notebook.

### Key-Value Stores

A key-value store (KVS) is simply a hash table that can be persisted
to storage.
The basic types of requests to a KVS are `PUT`, and `GET`.

We have provided a client and server that support a simple "query 
language" for our KVS.  Here are the basic commands:

- `GET k` returns the value corresponding to key `k`.
- `PUT k v` creates a new mapping from `k` to `v` if key `k` does not already exist, or overwrites the previous value corresponding to `k` otherwise.

### The CS186 Key Value Store

We have provided a KVS implementation that functions, but does so
*without* any concurrency control -- meaning that clients can see
interleaved schedules that are not serializable!  This could be confusing; 
your job is to interpose a 2PL implementation to fix this.  In this 
section we provide some background on the CS186 KVS.

We are using a [client-server model](https://en.wikipedia.org/wiki/Client%E2%80%93server_model) to send requests from multiple clients to a single server.
A server process listens for incoming connections from client processes.

When a client tries to connect, the server creates a *server handler* object dedicated to that client, which manages all future communication with that client.
All inter-process communication occurs through [UDS sockets](https://en.wikipedia.org/wiki/Unix_domain_socket) - nothing gets sent over the Internet.

We have already implemented all of the code to perform client-server communication - you do not need to worry about this.
However, note that some operating systems do not provide support for UDS sockets.
In particular, this project will not run on Windows.
For this assignment, we will only support the `hive` machines, though you 
may be able to get it running on Linux or MacOS (at your own risk!)
Keeping this in mind, **please ensure that your solution works correctly on the hive machines**, if you want to be sure it will receive full credit 
during autograding.

When the server process starts, it creates the storage structure for the KVS.
We have two implementations of key-value stores - a disk-based version (`DBMStore`), and an in-memory version (`InMemoryKVStore`).
These two classes are defined in `kvstore.py`, and they have the exact same interface.
By default, all of our code uses the simple in-memory version.
If you want to use the disk-based version instead, change the constant `KVSTORE_CLASS` in `student.py` to `DBMStore`.
The rest of this document assumes that `KVSTORE_CLASS` is set to `InMemoryKVStore`.

### Running the CS186 KVS
Let's try running the code (from one of the `hive` machines mentioned above).
Open up two terminal windows, and ssh to the same machine from each one.
(If you try to create a client process on a different machine than the server process, it will not be able to connect!)
In each window, `cd` to the `hw4` directory.
In the first window, run the following:

    $ python runserver.py

In the second window, run the following sequence of `GET`, `PUT`, and `EXIT` requests.  (Beware that our parser is rather simple!)
Note the output after each one:

    $ python runclient.py
    GET a
    No such key
    PUT a 1
    Success
    GET a
    1
    EXIT
    User Abort

The client process has terminated, but the server process is still running, in case more clients want to connect.
To terminate the server process, type Ctrl-C in the server window.

You may want to run your server as a background process:

    $ python runserver.py &

For more information on UNIX background processes (and how to work with them) see web info [like this](https://www.digitalocean.com/community/tutorials/how-to-use-bash-s-job-control-to-manage-foreground-and-background-processes).

### Digging Deeper

Let's see what happens when we have more than one client process.
As before, open up three terminal windows, ssh to the same machine on each one, and `cd` to the `hw4` directory.
In the first window, run the server, as above.
In the second window, run the following:

    $ python runclient.py
    GET a
    No such key

In the third window, run the following:

    $ python runclient.py
    GET a
    No such key

Go back to the second window, and run the following:

    PUT a 1
    Success

Go back to the third window, and run the following:

    GET a
    1
    PUT a 2
    Success
    EXIT
    User Abort

Go back to the second window, and run the following:

    GET a
    2
    EXIT
    User Abort

Lastly, close the server in the first window.

Actions performed by one client can affect the other in an unserializable way! For example, within a single client, we cannot guarantee that the value returned by calling `GET a` is the last value that we stored by calling `PUT a`.

The purpose of this assignment is to ensure serializable behavior by adding concurrency control to our existing key-value store.

### How it Works
All actions (`GET`, `PUT`) of a client will run in a single transaction.
After the transaction terminates, the client cannot perform any more communication with the server.

A transaction can terminate in four ways:

1. The user can choose to commit the transaction (by entering the command `COMMIT`).
2. The user can choose to abort the transaction (by entering the command `ABORT` or by typing `EXIT`).
3. The system itself can choose to abort the transaction.
4. The client process can crash (the user presses Ctrl-C before a previous command completes).

**Note:** The CS186 KVS will take care of Aborts for you -- it will ensure that any transaction that is aborted will "undo" its effects on the KVS.  However, you will need to make sure that the effects of a Running or Aborting transaction cannot be seen by other transactions (via concurrency control!)

# Your Job
Given the CS186 KVS described above, your job is to implement Strict 2PL and Deadlock Detection (including identifying a transaction to be aborted.)

## Important Notes
**student.py is the only file that you need to modify.**

**Do NOT modify any other files.**

**You do NOT need to look at other files except for part1test.py and part2test.py.**

### Updates

This is a new assignment, so there will be bugs.
Let us know on Piazza if you find any!
We will post updates on Piazza when bugs are found and make the appropriate changes to the files here.
Please bear with us, and **remember to pull regularly.**



##General Notes

**Global lock table**

Both parts of this assignment require access/modification to a global lock
table that is shared among all transactions. 

We provide a skeleton for the global lock table: a
Python dictionary, whose keys can be any key in the KVS (i.e. the name
of anything that can be `PUT`ed or `GET`ed).  You will need to write code
to manage this dictionary's values to implement a lock table.

As discussed in class, the lock table needs to keep track, for each 
key in the table, of two basic things:

1. Which transactions currently have a lock on that key (the "granted group" of transactions), and what the lock mode is.
2. A queue of transactions that are waiting to be granted a lock on that key -- and the lock mode that they are waiting for.

When a transaction requests a lock in a mode that conflicts with the current holder of the lock, the requesting transaction should be placed on a FIFO queue of transactions waiting for that lock.

When a transaction leaves the system (via commit or abort), all mutually
compatible transactions at the head of the FIFO queue should be granted the
lock.

We will only implement two lock modes in this homework: Shared and 
Exclusive.

**Concurrent Access to the Lock Table? No worries.**

In the CS186 KVS, there is a *single thread of control*, and your code will run in that thread.  This means that your code does not have to worry about being "interrupted" as it manipulates the lock table data structure, which is nice.

However, be aware that if your code runs for a very long time, the CS186 KVS Server is not able to do anything else!!  So try to keep your routines
simple and quick.

## Part 1: TransactionHandler

Each client communicates with a single server handler.
Each server handler has an associated `TransactionHandler` object.
In the homework skeleton code we are giving you, `TransactionHandler` (inside `student.py`) does not take any steps to ensure transactional isolation from other `TransactionHandler` objects.
You are responsible for implementing the methods in the `TransactionHandler` class.

**Your methods must be non-blocking.**
As mentioned above, each method must return in a reasonable amount of time.
For example, if you are unable to acquire a shared lock on a key because another transaction has an exclusive lock on it, you cannot simply loop until the other transaction releases the lock!

**Your methods must not raise exceptions.**
You may find it useful to raise exceptions while debugging.
If this happens, the client will disconnect automatically and its
transaction will be aborted, so the next request from the client will 
fail with an error.  Make sure your final code does not raise exceptions.

We provide test cases as you proceed through the different methods.
All tests for Part 1 are in file `part1test.py`. To run them, type:

    $ python part1test.py

These tests do not provide complete coverage of edge cases that you may encounter.
**We will be grading on a separate, more rigorous set of tests, so you are encouraged to write tests yourself.**

We provide a brief overview of each task below.
**Please refer to student.py for more detailed instructions of how to implement each method.**

### 1.1: TransactionHandler.perform_get(), TransactionHandler.perform_put()

Handle the `GET`/`PUT` request.  `GET` is equivalent to "read", `PUT` is 
equivalent to "write".

After your code for this part is complete, you should pass the tests `test_rw()`, `test_wr()`, and `test_ww()`.
With this task completed, your code will correctly block a transaction when a `GET` or `PUT` operation conflicts with another transaction's `GET` or `PUT` operation.
However, we have yet to implement the "cleanup" logic that needs to run
at the end of transaction, which will also unblock other transactions
that are waiting for locks.
We implement this next.

### 1.2: TransactionHandler.release_and_grant_locks()

A helper method that is called during transactions commits or aborts.
Releases all locks acquired by the transaction and, for each lock, grants it to the set of mutually compatible transactions at the head of the queue for
that locks.
We have already provided the implementation of `commit()` and `abort()` in `student.py`, but you need to fill in this helper method.

After your code for this part is complete, you will pass the tests `test_commit_commit()`, `test_abort_commit()`, and `test_commit_abort_commit()`.

### 1.3: TransactionHandler.check_lock()

For a transaction that has been waiting to acquire a lock, this method is periodically called to check if the lock has been granted to this 
transaction due to commit/abort of other transactions.
If so, then perform the operation that the transaction was originally trying
to do, and return the appropriate value.
Otherwise return `None`.

After your code for this part is complete, you will pass the tests `test_unlock_rw()`, `test_unlock_wr()`, `test_unlock_ww()`.

## Part 2: TransactionCoordinator

There is a single `TransactionCoordinator` object on the server side for all transactions.
This has only one method, `detect_deadlocks()`, which is called periodically to check whether any transactions are unable to proceed due to deadlock.
If so, then one of the transactions is aborted.

You will need to construct a waits-for graph from the lock table, and run a cycle detection algorithm to determine if a transaction needs to be aborted.  If a
cycle is detected, you should return the ID of a transaction on the cycle (you may choose which one you like) for the system to abort.

**Please refer to student.py for more detailed instruction of how to implement the method.**

All tests for Part 2 are in file `part2test.py`. To run them, type:

    $ python part2test.py

As before, remember that these tests do not provide complete coverage of edge cases.

## Submission Instructions
Before you submit, remember to pull from `course`, to make sure you have the most up-to-date code, and run all the tests again.
To submit, remember to push to `release/hw4` with:

    $ git push origin master:release/hw4

Detailed submission instructions are in [HW0](https://github.com/berkeley-cs186/course/tree/master/hw0).

#### Please?

Fill out our [HW4 Evaluation and Feedback form](https://docs.google.com/a/berkeley.edu/forms/d/1-dUKVUt5jpQDG7jN2Mjm77T3Esxpndn4VgHcxkC37FE/viewform) to help us with HW5 and future iterations of this course!
