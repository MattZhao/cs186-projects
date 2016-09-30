import unittest

from kvstore import InMemoryKVStore
from student import USER, TransactionHandler

def helper(t0, t1):
    print "t0 lock table : "
    print t0._lock_table
    print "t1 lock table : "
    print t1._lock_table
    print "t0 _acquired_locks : "
    print t0._acquired_locks
    print "t1 _acquired_locks : "
    print t1._acquired_locks
    print "t0 store"
    print t0._store
    print "t1 store"
    print t1._store


class Part1Test(unittest.TestCase):

    # PASSED
    def test_commit(self):
        # Sanity check
        lock_table = {}
        store = InMemoryKVStore()
        t0 = TransactionHandler(lock_table, 0, store)
        self.assertEqual(t0.perform_get('a'), 'No such key')
        self.assertEqual(t0.perform_put('a', '0'), 'Success')
        self.assertEqual(t0.perform_get('a'), '0')
        self.assertEqual(t0.commit(), 'Transaction Completed')
        self.assertEqual(store.get('a'), '0')

    # PASSED
    def test_abort(self):
        # Sanity check
        lock_table = {}
        store = InMemoryKVStore()
        t0 = TransactionHandler(lock_table, 0, store)
        self.assertEqual(t0.perform_get('a'), 'No such key')
        self.assertEqual(t0.perform_put('a', '0'), 'Success')
        self.assertEqual(t0.perform_get('a'), '0')
        self.assertEqual(t0.abort(USER), 'User Abort')
        self.assertEqual(store.get('a'), None)

    # PASSED
    def test_multiple_read(self):
        # Sanity check
        lock_table = {}
        store = InMemoryKVStore()
        store.put('a', '0')
        t0 = TransactionHandler(lock_table, 0, store)
        t1 = TransactionHandler(lock_table, 1, store)
        t2 = TransactionHandler(lock_table, 2, store)
        self.assertEqual(t0.perform_get('a'), '0')
        self.assertEqual(t1.perform_get('a'), '0')
        self.assertEqual(t2.perform_get('a'), '0')
        self.assertEqual(t0.commit(), 'Transaction Completed')
        self.assertEqual(t1.abort(USER), 'User Abort')
        self.assertEqual(t2.perform_get('a'), '0')

    # PASSED
    def test_rw(self):
        # Should pass after 1.1
        lock_table = {}
        store = InMemoryKVStore()
        t0 = TransactionHandler(lock_table, 0, store)
        t1 = TransactionHandler(lock_table, 1, store)
        self.assertEqual(t0.perform_get('a'), 'No such key')
        self.assertEqual(t1.perform_get('a'), 'No such key')   
        self.assertEqual(t1.perform_put('a', '0'), None)
        self.assertEqual(t0.commit(), 'Transaction Completed')
        self.assertEqual(store.get('a'), None)


    # PASSED
    def test_ww(self):
        # Should pass after 1.1
        lock_table = {}
        store = InMemoryKVStore()
        t0 = TransactionHandler(lock_table, 0, store)
        t1 = TransactionHandler(lock_table, 1, store)
        self.assertEqual(t0.perform_get('a'), 'No such key')
        self.assertEqual(t0.perform_put('a', '0'), 'Success')
        self.assertEqual(t1.perform_put('a', '1'), None)
        self.assertEqual(t0.commit(), 'Transaction Completed')
        self.assertEqual(store.get('a'), '0')

    # PASSED
    def test_wr(self):
        # Should pass after 1.1
        lock_table = {}
        store = InMemoryKVStore()
        t0 = TransactionHandler(lock_table, 0, store)
        t1 = TransactionHandler(lock_table, 1, store)
        self.assertEqual(t0.perform_get('a'), 'No such key')
        self.assertEqual(t0.perform_put('a', '0'), 'Success')
        self.assertEqual(t0.perform_get('a'), '0')
        self.assertEqual(t1.perform_get('a'), None)                 
        self.assertEqual(t0.commit(), 'Transaction Completed')
        self.assertEqual(store.get('a'), '0')

    # PASSED
    def test_commit_abort_commit(self):
        # Should pass after 1.2
        lock_table = {}
        store = InMemoryKVStore()
        t0 = TransactionHandler(lock_table, 0, store)
        t1 = TransactionHandler(lock_table, 1, store)
        t2 = TransactionHandler(lock_table, 2, store)
        self.assertEqual(t0.perform_get('a'), 'No such key')
        self.assertEqual(t0.perform_put('a', '0'), 'Success')
        self.assertEqual(t0.perform_get('a'), '0')
        self.assertEqual(t0.commit(), 'Transaction Completed')
        self.assertEqual(t1.perform_get('a'), '0')              # AssertionError: None != '0'
        self.assertEqual(t1.perform_put('a', '1'), 'Success')
        self.assertEqual(t1.perform_get('a'), '1')
        self.assertEqual(t1.abort(USER), 'User Abort')
        self.assertEqual(t2.perform_get('a'), '0')
        self.assertEqual(t2.perform_put('a', '2'), 'Success')
        self.assertEqual(t2.perform_get('a'), '2')
        self.assertEqual(t2.commit(), 'Transaction Completed')
        self.assertEqual(store.get('a'), '2')

    # PASSED
    def test_abort_commit(self):
        # Should pass after 1.2
        lock_table = {}
        store = InMemoryKVStore()
        t0 = TransactionHandler(lock_table, 0, store)
        t1 = TransactionHandler(lock_table, 1, store)
        self.assertEqual(t0.perform_get('a'), 'No such key')
        self.assertEqual(t0.perform_put('a', '0'), 'Success')
        self.assertEqual(t0.perform_get('a'), '0')
        self.assertEqual(t0.abort(USER), 'User Abort')
        self.assertEqual(t1.perform_get('a'), 'No such key')       
        self.assertEqual(t1.perform_put('a', '1'), 'Success')
        self.assertEqual(t1.perform_get('a'), '1')
        self.assertEqual(t1.commit(), 'Transaction Completed')
        self.assertEqual(store.get('a'), '1')

    # PASSED
    def test_commit_commit(self):
        # Should pass after 1.2
        lock_table = {}
        store = InMemoryKVStore()
        t0 = TransactionHandler(lock_table, 0, store)
        t1 = TransactionHandler(lock_table, 1, store)
        self.assertEqual(t0.perform_get('a'), 'No such key')
        self.assertEqual(t0.perform_put('a', '0'), 'Success')
        self.assertEqual(t0.perform_get('a'), '0')
        self.assertEqual(t0.commit(), 'Transaction Completed')
        self.assertEqual(t1.perform_get('a'), '0')               
        self.assertEqual(t1.perform_put('a', '1'), 'Success')
        self.assertEqual(t1.perform_get('a'), '1')
        self.assertEqual(t1.commit(), 'Transaction Completed')
        self.assertEqual(store.get('a'), '1')

    # PASSED
    def test_unlock_rw(self):
        # Should pass after 1.3
        lock_table = {}
        store = InMemoryKVStore()
        t0 = TransactionHandler(lock_table, 0, store)
        t1 = TransactionHandler(lock_table, 1, store)
        self.assertEqual(t0.perform_get('a'), 'No such key')         # T0 R(a)
        self.assertEqual(t1.perform_get('a'), 'No such key')
        self.assertEqual(t1.perform_put('a', '0'), None)             # T1 W(a)
        self.assertEqual(t1.check_lock(), None)
        self.assertEqual(t1.check_lock(), None)
        self.assertEqual(t0.commit(), 'Transaction Completed')
        self.assertEqual(t1.check_lock(), 'Success')            
        self.assertEqual(t1.perform_get('a'), '0')

    # PASSED
    def test_unlock_wr(self):
        # Should pass after 1.3
        lock_table = {}
        store = InMemoryKVStore()
        t0 = TransactionHandler(lock_table, 0, store)
        t1 = TransactionHandler(lock_table, 1, store)
        self.assertEqual(t0.perform_get('a'), 'No such key')
        self.assertEqual(t0.perform_put('a', '0'), 'Success')        # T0 W(a)
        self.assertEqual(t0.perform_get('a'), '0')
        self.assertEqual(t1.perform_get('a'), None)                  # T1 R(a)
        self.assertEqual(t1.check_lock(), None)
        self.assertEqual(t1.check_lock(), None)
        self.assertEqual(t0.commit(), 'Transaction Completed')
        self.assertEqual(t1.check_lock(), '0')                        
        self.assertEqual(t1.perform_get('a'), '0')

    # PASSED
    def test_unlock_ww(self):
        # Should pass after 1.3
        lock_table = {}
        store = InMemoryKVStore()
        t0 = TransactionHandler(lock_table, 0, store)
        t1 = TransactionHandler(lock_table, 1, store)
        self.assertEqual(t0.perform_get('a'), 'No such key')
        self.assertEqual(t0.perform_put('a', '0'), 'Success')        # T0 W(a)
        self.assertEqual(t1.perform_put('a', '1'), None)             # T1 W(a)
        self.assertEqual(t0.perform_get('a'), '0')
        self.assertEqual(t1.check_lock(), None)
        self.assertEqual(t1.check_lock(), None)
        self.assertEqual(t0.commit(), 'Transaction Completed')
        self.assertEqual(t1.check_lock(), 'Success')           # AssertionError: None != 'Success'
        self.assertEqual(t1.perform_get('a'), '1')

    # PASSED
    def test_multiple_read(self):
        lock_table = {}
        store = InMemoryKVStore()
        t0 = TransactionHandler(lock_table, 0, store)
        t1 = TransactionHandler(lock_table, 1, store)
        t2 = TransactionHandler(lock_table, 2, store)
        t3 = TransactionHandler(lock_table, 3, store)
        self.assertEqual(t0.perform_get('apple'), 'No such key')
        self.assertEqual(t1.perform_get('apple'), 'No such key')
        self.assertEqual(t2.perform_get('apple'), 'No such key')
        self.assertEqual(t0.perform_put('apple', '11'), None)   
        self.assertEqual(t0.check_lock(), None)      
        self.assertEqual(t1.commit(), 'Transaction Completed')
        self.assertEqual(t0.check_lock(), None)
        self.assertEqual(t2.commit(), 'Transaction Completed')
        self.assertEqual(t0.check_lock(), "Success")
        self.assertEqual(t0.perform_get('apple'), '11')
        self.assertEqual(t0.perform_get('banana'), 'No such key')
        self.assertEqual(t1.perform_get('apple'), None)
        self.assertEqual(t0.commit(), "Transaction Completed")
        self.assertEqual(t1.perform_get("apple"), "11")
        self.assertEqual(t2.perform_get("apple"), "11")
        self.assertEqual(t3.perform_get("apple"), "11")

    # PASSED 
    def test_1_thread_on_multiple_keys(self):
        lock_table = {}
        store = InMemoryKVStore()
        t0 = TransactionHandler(lock_table, 0, store)
        t1 = TransactionHandler(lock_table, 1, store)
        t2 = TransactionHandler(lock_table, 2, store)
        t3 = TransactionHandler(lock_table, 3, store)
        self.assertEqual(t0.perform_get('apple'), 'No such key')
        self.assertEqual(t1.perform_get('apple'), 'No such key')
        self.assertEqual(t2.perform_get('apple'), 'No such key')
        self.assertEqual(t0.perform_put('apple', '11'), None)   
        self.assertEqual(t0.check_lock(), None)      
        self.assertEqual(t1.commit(), 'Transaction Completed')
        self.assertEqual(t0.check_lock(), None)
        self.assertEqual(t2.commit(), 'Transaction Completed')
        self.assertEqual(t0.check_lock(), "Success")
        self.assertEqual(t0.perform_get('apple'), '11')
        self.assertEqual(t0.perform_put('apple', "10000"), 'Success')
        self.assertEqual(t0.perform_get('apple'), '10000')
        self.assertEqual(t0.perform_put("banana", '22'), "Success")
        self.assertEqual(t0.perform_get('banana'), '22')
        self.assertEqual(t1.perform_get('apple'), None)
        self.assertEqual(t0.commit(), 'Transaction Completed')
        self.assertEqual(t1.check_lock(),'10000')
        self.assertEqual(t1.perform_get("apple"), "10000")
        self.assertEqual(t2.perform_get("apple"), "10000")
        self.assertEqual(t3.perform_get("apple"), "10000")

    # PASSED
    def test_single_abort(self):
        lock_table = {}
        store = InMemoryKVStore()
        t0 = TransactionHandler(lock_table, 0, store)
        t1 = TransactionHandler(lock_table, 1, store)
        t2 = TransactionHandler(lock_table, 2, store)
        t3 = TransactionHandler(lock_table, 3, store)
        self.assertEqual(t0.perform_get('apple'), 'No such key')
        self.assertEqual(t1.perform_get('apple'), 'No such key')
        self.assertEqual(t2.perform_get('apple'), 'No such key')
        self.assertEqual(t0.perform_put('apple', '11'), None)   
        self.assertEqual(t0.check_lock(), None)      
        self.assertEqual(t1.commit(), 'Transaction Completed')
        self.assertEqual(t0.check_lock(), None)
        self.assertEqual(t2.commit(), 'Transaction Completed')
        self.assertEqual(t0.check_lock(), "Success")
        self.assertEqual(t0.perform_get('apple'), '11')
        self.assertEqual(t0.perform_get('banana'), 'No such key')
        self.assertEqual(t0.perform_put("banana", '22'), "Success")
        self.assertEqual(t1.perform_get('apple'), None)
        self.assertEqual(t0.abort(USER), 'User Abort')
        self.assertEqual(t1.check_lock(),'No such key')

    # PASSED
    def test_upgrade_s_x_multi(self):
        lock_table = {}
        store = InMemoryKVStore()
        t0 = TransactionHandler(lock_table, 0, store)
        t1 = TransactionHandler(lock_table, 1, store)
        t2 = TransactionHandler(lock_table, 2, store)
        self.assertEqual(t0.perform_put('noob', '555'), 'Success')
        self.assertEqual(t0.commit(),'Transaction Completed')
        self.assertEqual(t0.perform_get('noob'), '555')
        self.assertEqual(t1.perform_get('noob'),'555')
        self.assertEqual(t2.perform_get('noob'), '555')
        self.assertEqual(t1.perform_put('noob', '111'), None)
        self.assertEqual(t1.check_lock(), None)      
        self.assertEqual(t0.commit(), 'Transaction Completed')
        self.assertEqual(t1.check_lock(), None)      
        self.assertEqual(t2.commit(), 'Transaction Completed')
        self.assertEqual(t1.check_lock(), 'Success')  
        self.assertEqual(t1.perform_get('noob'), '111')    

    # PASSED
    def test_upgrade_in_put(self):
        lock_table = {}
        store = InMemoryKVStore()
        t0 = TransactionHandler(lock_table, 0, store)
        t1 = TransactionHandler(lock_table, 1, store)
        t2 = TransactionHandler(lock_table, 2, store)
        self.assertEqual(t0.perform_get('apple'), 'No such key')
        self.assertEqual(t1.perform_put('apple', '333'), None)
        self.assertEqual(t0.perform_put('apple', 'aaa'), 'Success')
        self.assertEqual(t0.perform_get('apple'), 'aaa')



if __name__ == '__main__':
    unittest.main()








