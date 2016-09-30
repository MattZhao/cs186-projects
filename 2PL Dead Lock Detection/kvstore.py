class InMemoryKVStore:
    def __init__(self):
        self._kv_store = {}

    def get(self, key):
        return self._kv_store.get(key, None)

    def put(self, key, value):
        self._kv_store[key] = value

class DBMStore:
    def __init__(self):
        import dbm
        self._kv_store = dbm.open('cache', 'c')

    def get(self, key):
        return self._kv_store.get(key, None)

    def put(self, key, value):
        self._kv_store[key] = value
