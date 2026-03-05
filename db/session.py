from contextlib import asynccontextmanager
from collections import defaultdict


class InMemorySession:
    def __init__(self, store):
        self._store = store
        self._execute_history = []

    async def execute(self, query, params=None):
        self._execute_history.append((str(query), params))
        query_str = str(query).lower()

        if "select" in query_str:
            for table_name, rows in self._store.items():
                if table_name in query_str:
                    if params:
                        filtered = [
                            row for row in rows
                            if all(row.get(k) == v for k, v in params.items() if k in row)
                        ]
                        return InMemoryResult(filtered)
                    return InMemoryResult(rows)
            return InMemoryResult([])

        if "insert" in query_str:
            for table_name in self._store:
                if table_name in query_str:
                    if params and isinstance(params, dict):
                        self._store[table_name].append(params)
                    break
            else:
                for word in query_str.split():
                    if word not in ("insert", "into", "values", "(", ")", ",", "select"):
                        if not word.startswith(":") and not word.startswith("'"):
                            self._store[word] = self._store.get(word, [])
                            if params and isinstance(params, dict):
                                self._store[word].append(params)
                            break

        return InMemoryResult([])

    async def commit(self):
        pass

    async def rollback(self):
        pass

    async def close(self):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class InMemoryResult:
    def __init__(self, data=None):
        self._data = data or []

    def mappings(self):
        return InMemoryMappings(self._data)

    def first(self):
        return self._data[0] if self._data else None

    def scalar(self):
        if self._data and isinstance(self._data[0], (int, float, str)):
            return self._data[0]
        return len(self._data) if self._data else 0

    def all(self):
        return self._data


class InMemoryMappings:
    def __init__(self, data):
        self._data = data

    def first(self):
        return self._data[0] if self._data else None

    def all(self):
        return self._data


_global_store = defaultdict(list)


def async_session():
    return InMemorySession(_global_store)
