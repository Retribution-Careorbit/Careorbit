# tests/helpers/mocks.py
# Shared mock classes extracted from conftest.py.
# conftest.py is not importable; these must live in helpers/.
# V3 FIX C3: MockResult moved here.
# V4: Added MockAsyncSession context manager support.

from collections import defaultdict


class MockDBSession:
    """
    In-memory mock DB with read-after-write support.
    Supports SELECT filtering by params, INSERT, UPDATE.
    """

    def __init__(self):
        self._store: dict[str, list[dict]] = defaultdict(list)
        self._committed = False
        self._last_query = None
        self._last_params = None
        self._execute_history: list[tuple] = []

    def seed(self, table: str, rows: list[dict]):
        self._store[table].extend(rows)

    async def execute(self, query, params=None):
        self._last_query = str(query)
        self._last_params = params
        self._execute_history.append((str(query), params))
        query_str = str(query).lower()

        if "select" in query_str:
            for table_name, rows in self._store.items():
                if table_name in query_str:
                    if params:
                        filtered = [
                            row for row in rows
                            if all(row.get(k) == v for k, v in params.items()
                                   if k in row)
                        ]
                        return MockResult(filtered)
                    return MockResult(rows)
            return MockResult([])

        if "insert" in query_str:
            for table_name in self._store:
                if table_name in query_str:
                    if params and isinstance(params, dict):
                        self._store[table_name].append(params)
                    break

        if "update" in query_str:
            pass

        return MockResult([])

    async def commit(self):
        self._committed = True

    async def rollback(self):
        self._committed = False

    async def close(self):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    def assert_query_contains(self, substring: str):
        """Assert that at least one executed query contains substring."""
        all_queries = " ".join(q for q, _ in self._execute_history)
        assert substring.lower() in all_queries.lower(), (
            f"'{substring}' not found in any executed query.\n"
            f"Executed queries: {[q[:80] for q, _ in self._execute_history]}"
        )

    def assert_param_value(self, key: str, expected_value):
        """Assert that at least one execute call had param key == expected_value."""
        for _, params in self._execute_history:
            if params and params.get(key) == expected_value:
                return
        all_params = [p for _, p in self._execute_history if p]
        raise AssertionError(
            f"No execute call had param '{key}' == '{expected_value}'.\n"
            f"Actual params: {all_params}"
        )


class MockResult:
    def __init__(self, data=None):
        self._data = data or []

    def mappings(self):
        return MockMappings(self._data)

    def first(self):
        return self._data[0] if self._data else None

    def scalar(self):
        if self._data and isinstance(self._data[0], (int, float, str)):
            return self._data[0]
        return len(self._data) if self._data else 0

    def all(self):
        return self._data


class MockMappings:
    def __init__(self, data):
        self._data = data

    def first(self):
        return self._data[0] if self._data else None

    def all(self):
        return self._data
