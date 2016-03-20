import unittest

from kvstore import InMemoryKVStore
from student import DEADLOCK, USER, TransactionCoordinator, TransactionHandler

class Part2Test(unittest.TestCase):

    def test_deadlock_rw_rw(self):
        # Should pass after 2
        lock_table = {}
        store = InMemoryKVStore()
        t0 = TransactionHandler(lock_table, 0, store)
        t1 = TransactionHandler(lock_table, 1, store)
        t2 = TransactionHandler(lock_table, 2, store)
        coordinator = TransactionCoordinator(lock_table)
        self.assertEqual(coordinator.detect_deadlocks(), None)
        self.assertEqual(t0.perform_get('a'), 'No such key')
        self.assertEqual(coordinator.detect_deadlocks(), None)
        self.assertEqual(t0.perform_get('b'), 'No such key')
        self.assertEqual(coordinator.detect_deadlocks(), None)
        self.assertEqual(t0.perform_put('a', 'a0'), 'Success')
        self.assertEqual(coordinator.detect_deadlocks(), None)
        self.assertEqual(t0.perform_put('b', 'b0'), 'Success')
        self.assertEqual(coordinator.detect_deadlocks(), None)
        self.assertEqual(t0.commit(), 'Transaction Completed')
        self.assertEqual(coordinator.detect_deadlocks(), None)
        self.assertEqual(t1.perform_get('a'), 'a0')                  # T1 R(a)
        self.assertEqual(t2.perform_get('b'), 'b0')                  # T2 R(b)      
        self.assertEqual(coordinator.detect_deadlocks(), None)     
        self.assertEqual(t1.perform_put('b', 'b1'), None)            # T1 W(b)
        self.assertEqual(coordinator.detect_deadlocks(), None)      
        self.assertEqual(t1.check_lock(), None)
        self.assertEqual(t2.perform_put('a', 'a1'), None)            # T2 W(a)
        abort_id = coordinator.detect_deadlocks()
        self.assertTrue(abort_id == 1 or abort_id == 2)

    def test_deadlock_wr_rw(self):
        # Should pass after 2
        lock_table = {}
        store = InMemoryKVStore()
        t0 = TransactionHandler(lock_table, 0, store)
        t1 = TransactionHandler(lock_table, 1, store)
        t2 = TransactionHandler(lock_table, 2, store)
        coordinator = TransactionCoordinator(lock_table)
        self.assertEqual(coordinator.detect_deadlocks(), None)
        self.assertEqual(t0.perform_get('a'), 'No such key')
        self.assertEqual(t0.perform_get('b'), 'No such key')
        self.assertEqual(t0.perform_put('a', 'a0'), 'Success')
        self.assertEqual(t0.perform_put('b', 'b0'), 'Success')
        self.assertEqual(t0.commit(), 'Transaction Completed')
        self.assertEqual(coordinator.detect_deadlocks(), None)
        self.assertEqual(t1.perform_put('a', 'a1'), 'Success')       # T1 W(a)
        self.assertEqual(t2.perform_get('b'), 'b0')                  # T2 R(b)
        self.assertEqual(coordinator.detect_deadlocks(), None)              #error
        self.assertEqual(t1.perform_put('b', 'b1'), None)            # T1 W(b)
        self.assertEqual(coordinator.detect_deadlocks(), None)              #error
        self.assertEqual(t1.check_lock(), None)
        self.assertEqual(t2.perform_get('a'), None)                  # T2 R(a)
        abort_id = coordinator.detect_deadlocks()
        self.assertTrue(abort_id == 1 or abort_id == 2)

    def test_deadlock_ww_rw(self):
        # Should pass after 2
        lock_table = {}
        store = InMemoryKVStore()
        t0 = TransactionHandler(lock_table, 0, store)
        t1 = TransactionHandler(lock_table, 1, store)
        t2 = TransactionHandler(lock_table, 2, store)
        coordinator = TransactionCoordinator(lock_table)
        self.assertEqual(coordinator.detect_deadlocks(), None)
        self.assertEqual(t0.perform_get('a'), 'No such key')
        self.assertEqual(t0.perform_get('b'), 'No such key')
        self.assertEqual(t0.perform_put('a', 'a0'), 'Success')
        self.assertEqual(t0.perform_put('b', 'b0'), 'Success')
        self.assertEqual(t0.commit(), 'Transaction Completed')
        self.assertEqual(coordinator.detect_deadlocks(), None)
        self.assertEqual(t1.perform_put('a', 'a1'), 'Success')       # T1 W(a)
        self.assertEqual(t2.perform_get('b'), 'b0')                  # T2 R(b)
        self.assertEqual(coordinator.detect_deadlocks(), None)
        self.assertEqual(t1.perform_put('b', 'b1'), None)            # T1 W(b)
        self.assertEqual(coordinator.detect_deadlocks(), None)
        self.assertEqual(t1.check_lock(), None)
        self.assertEqual(t2.perform_put('a', 'a2'), None)            # T2 W(a)
        abort_id = coordinator.detect_deadlocks()
        self.assertTrue(abort_id == 1 or abort_id == 2)


    def test_deadlock_identical(self):
        # Should pass after 2
        lock_table = {}
        store = InMemoryKVStore()
        t0 = TransactionHandler(lock_table, 0, store)
        t2 = TransactionHandler(lock_table, 2, store)
        coordinator = TransactionCoordinator(lock_table)
        self.assertEqual(coordinator.detect_deadlocks(), None)
        self.assertEqual(t0.perform_put('a', 'a0'), 'Success')
        self.assertEqual(t0.perform_put('b', 'b0'), 'Success')
        self.assertEqual(t2.perform_get('a'), None) 
        self.assertEqual(t2.perform_get('b'), None) 

    def test_deadlock_naive(self):
        # Should pass after 2
        lock_table = {}
        store = InMemoryKVStore()
        t0 = TransactionHandler(lock_table, 0, store)
        t2 = TransactionHandler(lock_table, 2, store)
        coordinator = TransactionCoordinator(lock_table)
        self.assertEqual(coordinator.detect_deadlocks(), None)
        self.assertEqual(t0.perform_put('a', 'a0'), 'Success')
        self.assertEqual(t0.commit(), 'Transaction Completed')
        self.assertEqual(t0.perform_get('a'), 'a0') 
        self.assertEqual(t2.perform_get('a'), 'a0')
        self.assertEqual(t0.perform_put('a', 'ab'), None)
        self.assertEqual(coordinator.detect_deadlocks(), None)

    def test_deadlock_gap_queue(self):
        lock_table = {}
        store = InMemoryKVStore()
        t0 = TransactionHandler(lock_table, 0, store)
        t1 = TransactionHandler(lock_table, 1, store)
        t2 = TransactionHandler(lock_table, 2, store)
        t3 = TransactionHandler(lock_table, 3, store)
        coordinator = TransactionCoordinator(lock_table)
        self.assertEqual(coordinator.detect_deadlocks(), None)
        self.assertEqual(t2.perform_put('a', 'a0'), 'Success')
        self.assertEqual(t0.perform_get('a'), None)
        self.assertEqual(t3.perform_put('b', 'b0'), 'Success')        
        self.assertEqual(t0.perform_get('b'), None)
        self.assertEqual(t1.perform_put('b', 'b1'), None)
        self.assertEqual(t2.perform_get('b'), None)
        abort_id = coordinator.detect_deadlocks()
        self.assertTrue(abort_id == 0 or abort_id == 2)
    
    def test_multi_deadlock(self):
        lock_table = {}
        store = InMemoryKVStore()
	t0 = TransactionHandler(lock_table, 0, store)
	t1 = TransactionHandler(lock_table, 1, store)
	t2 = TransactionHandler(lock_table, 2, store)
	t3 = TransactionHandler(lock_table, 3, store)
	t4 = TransactionHandler(lock_table, 4, store)
	coordinator = TransactionCoordinator(lock_table)
	self.assertEqual(coordinator.detect_deadlocks(), None)
	self.assertEqual(t0.perform_put('a', 'apple'), 'Success')
	self.assertEqual(t0.commit(), 'Transaction Completed')
	self.assertEqual(t1.perform_get('a'), 'apple')
	self.assertEqual(t2.perform_get('a'), 'apple')
	self.assertEqual(coordinator.detect_deadlocks(), None)
	self.assertEqual(t1.perform_put('a', 'banana'), None)
	self.assertEqual(t2.perform_put('a', 'pear'), None)
	self.assertEqual(t3.perform_put('a', 'cherry'), None)
	self.assertEqual(t4.perform_put('a', 'orange'),None)
	aid = coordinator.detect_deadlocks()
	self.assertTrue(aid == 2 or aid == 1)
	self.assertEqual(t2.check_lock(), None)
	self.assertEqual(t1.abort(USER), 'User Abort')

	self.assertEqual(t2.check_lock(), 'Success')
	self.assertEqual(t2.perform_get('a'), 'pear')
	self.assertEqual(t3.check_lock(), None)
	self.assertEqual(t4.check_lock(), None)

	aa = coordinator.detect_deadlocks()
	self.assertEqual(aa, None)





if __name__ == '__main__':
    unittest.main()
