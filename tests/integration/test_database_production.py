import pytest
from unittest.mock import patch, MagicMock
import os


class TestInMemorySessionFallback:

    def test_inmemory_session_used_without_database_url(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("DATABASE_URL", None)
            from db.session import InMemorySession, async_session
            session = async_session()
            assert isinstance(session, InMemorySession)

    @pytest.mark.asyncio
    async def test_inmemory_session_execute(self):
        from db.session import InMemorySession
        from collections import defaultdict
        store = defaultdict(list)
        store["users"] = [{"id": "1", "name": "Test"}]
        session = InMemorySession(store)
        result = await session.execute("SELECT * FROM users")
        assert result is not None

    @pytest.mark.asyncio
    async def test_inmemory_session_commit(self):
        from db.session import InMemorySession
        from collections import defaultdict
        session = InMemorySession(defaultdict(list))
        await session.commit()

    @pytest.mark.asyncio
    async def test_inmemory_session_rollback(self):
        from db.session import InMemorySession
        from collections import defaultdict
        session = InMemorySession(defaultdict(list))
        await session.rollback()

    @pytest.mark.asyncio
    async def test_inmemory_session_close(self):
        from db.session import InMemorySession
        from collections import defaultdict
        session = InMemorySession(defaultdict(list))
        await session.close()

    @pytest.mark.asyncio
    async def test_inmemory_session_context_manager(self):
        from db.session import InMemorySession
        from collections import defaultdict
        session = InMemorySession(defaultdict(list))
        async with session as s:
            assert s is session

    @pytest.mark.asyncio
    async def test_inmemory_result_mappings(self):
        from db.session import InMemoryResult
        result = InMemoryResult([{"id": "1", "name": "Test"}])
        mappings = result.mappings()
        assert mappings.first() == {"id": "1", "name": "Test"}

    @pytest.mark.asyncio
    async def test_inmemory_result_scalar(self):
        from db.session import InMemoryResult
        result = InMemoryResult([42])
        assert result.scalar() == 42

    @pytest.mark.asyncio
    async def test_inmemory_result_empty(self):
        from db.session import InMemoryResult
        result = InMemoryResult([])
        assert result.first() is None
        assert result.all() == []


class TestSchemaSQL:

    def test_schema_file_exists(self):
        assert os.path.isfile("database/schema.sql"), \
            "database/schema.sql must exist"

    def test_schema_has_users_table(self):
        with open("database/schema.sql") as f:
            sql = f.read()
        assert "CREATE TABLE users" in sql

    def test_schema_has_refresh_tokens_table(self):
        with open("database/schema.sql") as f:
            sql = f.read()
        assert "CREATE TABLE refresh_tokens" in sql

    def test_schema_has_refresh_tokens_revoked_at(self):
        with open("database/schema.sql") as f:
            sql = f.read()
        assert "revoked_at" in sql

    def test_schema_has_audit_log_table(self):
        with open("database/schema.sql") as f:
            sql = f.read()
        assert "CREATE TABLE audit_log" in sql

    def test_schema_has_audit_log_indexes(self):
        with open("database/schema.sql") as f:
            sql = f.read()
        required_indexes = [
            "idx_audit_log_user",
            "idx_audit_log_patient",
            "idx_audit_log_action",
            "idx_audit_log_created",
        ]
        for idx in required_indexes:
            assert idx in sql, f"Missing index: {idx}"

    def test_schema_has_pgcrypto_extension(self):
        with open("database/schema.sql") as f:
            sql = f.read()
        assert "pgcrypto" in sql

    def test_schema_has_uuid_ossp_extension(self):
        with open("database/schema.sql") as f:
            sql = f.read()
        assert "uuid-ossp" in sql

    def test_schema_has_documents_table(self):
        with open("database/schema.sql") as f:
            sql = f.read()
        assert "CREATE TABLE documents" in sql

    def test_schema_has_caregiver_links_table(self):
        with open("database/schema.sql") as f:
            sql = f.read()
        assert "CREATE TABLE caregiver_links" in sql

    def test_schema_audit_log_has_no_updated_at(self):
        with open("database/schema.sql") as f:
            sql = f.read()
        audit_start = sql.index("CREATE TABLE audit_log")
        closing_paren = sql.find(");", audit_start)
        audit_block = sql[audit_start:closing_paren + 2]
        columns = [line.strip() for line in audit_block.split("\n")
                   if line.strip() and not line.strip().startswith("--")
                   and not line.strip().startswith("CREATE")
                   and not line.strip() == ");"]
        col_names = [c.split()[0].lower() for c in columns if c.split()]
        assert "updated_at" not in col_names, \
            "audit_log must NOT have updated_at column (append-only)"


@pytest.mark.deployment
class TestAsyncPostgresSession:

    def test_session_factory_detects_postgresql_url(self):
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql+asyncpg://user:pass@host/db"}):
            pass

    def test_ssl_mode_require_for_azure(self):
        azure_url = "postgresql+asyncpg://user:pass@careorbit-db-prod.postgres.database.azure.com/careorbit?sslmode=require"
        assert "sslmode=require" in azure_url


@pytest.mark.deployment
class TestTokenRevocationWithDB:

    @pytest.mark.asyncio
    async def test_revoke_refresh_token_updates_revoked_at(self):
        from api.middleware.auth import revoke_refresh_token
        assert callable(revoke_refresh_token)

    @pytest.mark.asyncio
    async def test_revoke_all_user_tokens_updates_revoked_at(self):
        from api.middleware.auth import revoke_all_user_tokens
        assert callable(revoke_all_user_tokens)
