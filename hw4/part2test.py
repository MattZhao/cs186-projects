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
        self.assertEqual(t0.perform_get('b'), 'No such key')
        self.assertEqual(t0.perform_put('a', 'a0'), 'Success')
        self.assertEqual(t0.perform_put('b', 'b0'), 'Success')
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
        self.assertEqual(coordinator.detect_deadlocks(), None)
        self.assertEqual(t1.perform_put('b', 'b1'), None)            # T1 W(b)
        self.assertEqual(coordinator.detect_deadlocks(), None)
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

if __name__ == '__main__':
    unittest.main()
