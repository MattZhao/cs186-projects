import logging

from kvstore import DBMStore, InMemoryKVStore
LOG_LEVEL = logging.WARNING

KVSTORE_CLASS = InMemoryKVStore

"""
Possible abort modes.
"""
USER = 0
DEADLOCK = 1

"""
Part I: Implementing request handling methods for the transaction handler

The transaction handler has access to the following objects:

self._lock_table: the global lock table. More information in the README.

self._acquired_locks: a list of locks acquired by the transaction. Used to
release locks when the transaction commits or aborts. This list is initially
empty.

self._desired_lock: the lock that the transaction is waiting to acquire as well
as the operation to perform. This is initialized to None.

self._xid: this transaction's ID. You may assume each transaction is assigned a
unique transaction ID.

self._store: the in-memory key-value store. You may refer to kvstore.py for
methods supported by the store.

self._undo_log: a list of undo operations to be performed when the transaction
is aborted. The undo operation is a tuple of the form (@key, @value). This list
is initially empty.

You may assume that the key/value inputs to these methods are already type-
checked and are valid.
"""
class _Lock:
    def __init__(self, curT = [], curL):
        """
        curT: current transactions: "_xid"
        curL: current lock type: "x" or "s"
        queue: a queue of locks, implemented with list
        """
        self.curL = curL    
        self.curT = curT
        self.queue = list()

class TransactionHandler:

    def __init__(self, lock_table, xid, store):
        '''
        Each lock in _lock_table is a class that includes a QUEUE
        Each lock in _desired_lock & _acquired_locks is only a (key, type) tuple
        '''
        self._lock_table = lock_table
        self._acquired_locks = []
        self._desired_lock = None
        self._xid = xid
        self._store = store
        self._undo_log = []

    def perform_put(self, key, value):
        """
        Handles the PUT request. You should first implement the logic for
        acquiring the exclusive lock. If the transaction can successfully
        acquire the lock associated with the key, insert the key-value pair
        into the store.

        Hint: if the lock table does not contain the key entry yet, you should
        create one.
        Hint: be aware that lock upgrade may happen.
        Hint: remember to update self._undo_log so that we can undo all the
        changes if the transaction later gets aborted. See the code in abort()
        for the exact format.

        @param self: the transaction handler.
        @param key, value: the key-value pair to be inserted into the store.

        @return: if the transaction successfully acquires the lock and performs
        the insertion/update, returns 'Success'. If the transaction cannot
        acquire the lock, returns None, and saves the lock that the transaction
        is waiting to acquire in self._desired_lock.
        """
        lock = self._lock_table.get(key)
        if lock == None:
            self._lock_table[key] = _Lock([self._xid], "x")
            log_entry = (key, None)
            self._undo_log.append(log_entry)
            self._store.put(key, value)
            self._acquired_locks.append((key, "x"))
            if (key, "s") in self._acquired_locks:
                redundant_lock = (key, "s")
                self._acquired_locks.remove(redundant_lock)
            return 'Success'
        elif lock != None:
            if lock.curL == "x":
                # if (key, "x") in self._acquired_locks:
                if self._xid in lock.curT:
                    if (key, "x") not in self._acquired_locks:
                        self._acquired_locks.append((key, "x"))
                    if (key, "s") in self._acquired_locks:
                        self._acquired_locks.remove((key, "s"))
                    log_entry = (key, self._store.get(key))
                    self._undo_log.append(log_entry)
                    self._store.put(key, value)
                    return 'Success'
                else: 
                    lock.queue.append([self._xid, "x"])
                    self._desired_lock = (self._xid, "x")

            elif lock.curL == "s":
                if self._xid in lock.curT:
                    #case 1: immediate update from "s" to "x" 
                    if len(lock.curT) == 1 :
                        lock.curL = "x"
                        old_entry = (key, self._store.get(key))
                        self._undo_log.append(old_entry)
                        self._store.put(key, value)
                        if (key, "s") in self._acquired_locks:
                            self._acquired_locks.remove((key, "s"))
                        if self._desired_lock == (key, "s"):
                            self._desired_lock == None
                        if (key, "x") not in self._acquired_locks:
                            self._acquired_locks.append((key, "x"))
                        return 'Success'
                    # case 2: push to top of queue and wait for update
                    elif len(lock.curT) > 1 :
                        lock.queue.insert(0,[self._xid, "x"]) 
                        self._desired_lock = (key, "x")
                else:
                    lock.queue.append([self.xid, "x"])
                    self._desired_lock = (key, "x")

    def perform_get(self, key):                     
        """
        Handles the GET request. You should first implement the logic for
        acquiring the shared lock. If the transaction can successfully acquire
        the lock associated with the key, read the value from the store.

        Hint: if the lock table does not contain the key entry yet, you should
        create one.

        @param self: the transaction handler.
        @param key: the key to look up from the store.

        @return: if the transaction successfully acquires the lock and reads
        the value, returns the value. If the key does not exist, returns 'No
        such key'. If the transaction cannot acquire the lock, returns None,
        and saves the lock that the transaction is waiting to acquire in
        self._desired_lock.
        """
        lock = self._lock_table.get(key)
        if lock != None 
            if self._xid not in lock.curT and lock.curL == "s":
                if len(lock.queue) == 0:
                    lock.curT.append(self._xid)
                    self._acquired_locks.append((key, "s"))
                    return self._store.get(key)
                elif len(lock.queue) > 0:
                    lock.queue.append([self._xid, "s"])
                    self._desired_lock = (key, "s")
            elif self._xid not in lock.curT and lock.curL == "x":
                lock.queue.append([self._xid, "s"])
                self._desired_lock = (key, "s")
            elif self._xid in lock.curT:
                return self._store.get(key)
        else:
            value = self._store.get(key)
            if value == None:
                return "No such key"
            elif value != None:
                self._lock_table[key] = _Lock([self._xid], "s")
                self._acquired_locks.append((key, "s"))
                return value

    def commit(self):
        """
        Commits the transaction.

        Note: This method is already implemented for you, and you only need to
        implement the subroutine release_locks().

        @param self: the transaction handler.

        @return: returns 'Transaction Completed'
        """
        self.release_and_grant_locks()
        return 'Transaction Completed'

    def abort(self, mode):
        """
        Aborts the transaction.

        Note: This method is already implemented for you, and you only need to
        implement the subroutine release_locks().

        @param self: the transaction handler.
        @param mode: mode can either be USER or DEADLOCK. If mode == USER, then
        it means that the abort is issued by the transaction itself (user
        abort). If mode == DEADLOCK, then it means that the transaction is
        aborted by the coordinator due to deadlock (deadlock abort).

        @return: if mode == USER, returns 'User Abort'. If mode == DEADLOCK,
        returns 'Deadlock Abort'.
        """
        while (len(self._undo_log) > 0):
            k,v = self._undo_log.pop()
            self._store.put(k, v)
        self.release_and_grant_locks()
        if (mode == USER):
            return 'User Abort'
        else:
            return 'Deadlock Abort'


    def release_and_grant_locks(self):                                      """如何update别的session的acquired locks呢？"""
        """
        Releases all locks acquired by the transaction and grants them to the
        next transactions in the queue. This is a helper method that is called
        during transaction commits or aborts. 

        Hint: you can use self._acquired_locks to get a list of locks acquired
        by the transaction.
        Hint: be aware that lock upgrade may happen.

        @param self: the transaction handler.
        """
        # remove lock still in queue
        if self._desired_lock != None:
            desired_key = self._desired_lock[0]
            lockObjToModify = self._lock_table.get(key)
            for i in range(len(lockObjToModify.queue)):
                if i[0] = self._xid:
                    lockObjToModify.queue.remove(i)

        for l in self._acquired_locks:
            key = l[0]
            lockObj = self._lock_table.get(key)

            if len(lockObj.curT) == 1:
                if len(lockObj.queue) == 0:
                    lockObj = None
                elif len(lockObj.queue) > 0:
                    ll = lockObj.queue.pop(0)
                    lockObj.curT = []
                    lockObj.curT.append(ll[0])
                    lockObj.curL = ll[1]
            elif len(lockObj.curT) == 2:
                lockObj.curT.remove(self._xid)
                if len(lockObj.queue) != 0:
                    ll = lockObj.queue[0]
                    if lockObj.curT[0] ==  ll[0] and lockObj.curL == "s" and ll[1] == "x":
                        lockObj.queue.pop(0)
                        lockObj.curL = "x"
            elif len(lockObj.queue) > 2:
                lockObj.curT.remove(self._xid)
          
        self._acquired_locks = []
        self._desired_lock = None


    def check_lock(self):
        """
        If perform_get() or perform_put() returns None, then the transaction is
        waiting to acquire a lock. This method is called periodically to check
        if the lock has been granted due to commit or abort of other
        transactions. If so, then this method returns the string that would 
        have been returned by perform_get() or perform_put() if the method had
        not been blocked. Otherwise, this method returns None.

        As an example, suppose Joe is trying to perform 'GET a'. If Nisha has an
        exclusive lock on key 'a', then Joe's transaction is blocked, and
        perform_get() returns None. Joe's server handler starts calling
        check_lock(), which keeps returning None. While this is happening, Joe
        waits patiently for the server to return a response. Eventually, Nisha
        decides to commit his transaction, releasing his exclusive lock on 'a'.
        Now, when Joe's server handler calls check_lock(), the transaction
        checks to make sure that the lock has been acquired and returns the
        value of 'a'. The server handler then sends the value back to Joe.

        Hint: self._desired_lock contains the lock that the transaction is
        waiting to acquire.
        Hint: remember to update the self._acquired_locks list if the lock has
        been granted.
        Hint: if the transaction has been granted an exclusive lock due to lock
        upgrade, remember to clean up the self._acquired_locks list.
        Hint: remember to update self._undo_log so that we can undo all the
        changes if the transaction later gets aborted.

        @param self: the transaction handler.

        @return: if the lock has been granted, then returns whatever would be
        returned by perform_get() and perform_put() when the transaction
        successfully acquired the lock. If the lock has not been granted,
        returns None.
        """
        key = self._desired_lock[0]
        lockType = self._desired_lock[1]

        lockObj = self._lock_table.get(key)
        if lockType == "x":
            if self._xid in lockObj.curT and lockObj.curL == "x":
                old_val = self._store.get(key)
                self._undo_log.append((key, old_val))
                self._store.put(key, value)
                if (key, "s") in self._acquired_locks
                    self._acquired_locks.remove((key, "s"))
                else:
                    self._acquired_locks.append((key, "x"))
                self._desired_lock = None
                return 'Success'
        elif lockType == "s":
            if self._xid in lockObj.curT:
                if lockObj.curL == "x" and (key, "x") not in self._acquired_locks:
                    self._acquired_locks.append((key, "x"))
                if lockObj.curL == "s" and (key, "s") not in self._acquired_locks:
                    self._acquired_locks.append((key, "s"))
                if (key, "x") in self._acquired_locks and (key, "s") in self._acquired_locks:
                    self._acquired_locks.remove((key, "s"))

                self._desired_lock = None
                value = self._store.get(key)
                if value == None:
                    return 'No Such Key'
                else:
                    return value

"""
Part II: Implement deadlock detection method for the transaction coordinator

The transaction coordinator has access to the following object:

self._lock_table: see description from Part I
"""

class TransactionCoordinator:

    def __init__(self, lock_table):
        self._lock_table = lock_table

    def detect_deadlocks(self):
        """
        Constructs a waits-for graph from the lock table, and runs a cycle
        detection algorithm to determine if a transaction needs to be aborted.
        You may choose which one transaction you plan to abort, as long as your
        choice is deterministic. For example, if transactions 1 and 2 form a
        cycle, you cannot return transaction 1 sometimes and transaction 2 the
        other times.

        This method is called periodically to check if any operations of any
        two transactions conflict. If this is true, the transactions are in
        deadlock - neither can proceed. If there are multiple cycles of
        deadlocked transactions, then this method will be called multiple
        times, with each call breaking one of the cycles, until it returns None
        to indicate that there are no more cycles. Afterward, the surviving
        transactions will continue to run as normal.

        Note: in this method, you only need to find and return the xid of a
        transaction that needs to be aborted. You do not have to perform the
        actual abort.

        @param self: the transaction coordinator.

        @return: If there are no cycles in the waits-for graph, returns None.
        Otherwise, returns the xid of a transaction in a cycle.
        """
        pass # Part 2.1: your code here!
