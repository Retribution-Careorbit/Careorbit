import pytest
import os
import json


class TestRequirementsTxt:

    def test_requirements_file_exists(self):
        assert os.path.isfile("requirements.txt") or os.path.isfile("pyproject.toml"), \
            "requirements.txt or pyproject.toml must exist"

    def test_fastapi_in_dependencies(self):
        deps = _read_dependencies()
        assert any("fastapi" in d for d in deps), "fastapi must be in dependencies"

    def test_uvicorn_in_dependencies(self):
        deps = _read_dependencies()
        assert any("uvicorn" in d for d in deps), "uvicorn must be in dependencies"

    def test_pyjwt_in_dependencies(self):
        deps = _read_dependencies()
        assert any("pyjwt" in d.lower() or "python-jose" in d.lower() for d in deps), \
            "JWT library must be in dependencies"

    def test_sqlalchemy_in_dependencies(self):
        deps = _read_dependencies()
        assert any("sqlalchemy" in d.lower() for d in deps), \
            "SQLAlchemy must be in dependencies"


@pytest.mark.deployment
class TestAzureSDKDependencies:

    @pytest.mark.parametrize("package", [
        "azure-identity",
        "azure-keyvault-secrets",
    ])
    def test_azure_core_package_in_requirements(self, package):
        deps = _read_dependencies()
        assert any(package in d for d in deps), \
            f"{package} must be in requirements"

    @pytest.mark.parametrize("package", [
        "azure-ai-formrecognizer",
        "azure-ai-textanalytics",
        "azure-search-documents",
        "azure-storage-blob",
        "azure-communication-email",
    ])
    def test_azure_service_package_in_requirements(self, package):
        deps = _read_dependencies()
        assert any(package in d for d in deps), \
            f"{package} must be in requirements"

    def test_asyncpg_in_requirements(self):
        deps = _read_dependencies()
        assert any("asyncpg" in d for d in deps), \
            "asyncpg must be in requirements for async PostgreSQL"

    def test_alembic_in_requirements(self):
        deps = _read_dependencies()
        assert any("alembic" in d for d in deps), \
            "alembic must be in requirements for migrations"


@pytest.mark.deployment
class TestStaticWebAppConfig:

    def _find_swa_config(self):
        candidates = [
            "apps/frontend/staticwebapp.config.json",
            "staticwebapp.config.json",
            "client/staticwebapp.config.json",
        ]
        for path in candidates:
            if os.path.isfile(path):
                return path
        return None

    def test_staticwebapp_config_exists(self):
        path = self._find_swa_config()
        assert path is not None, \
            "staticwebapp.config.json must exist (checked apps/frontend/, root, client/)"

    def test_staticwebapp_config_valid_json(self):
        path = self._find_swa_config()
        if path:
            with open(path) as f:
                data = json.load(f)
            assert isinstance(data, dict)

    def test_staticwebapp_config_has_navigation_fallback(self):
        path = self._find_swa_config()
        if path:
            with open(path) as f:
                data = json.load(f)
            assert "navigationFallback" in data, \
                "staticwebapp.config.json must have navigationFallback for SPA routing"

    def test_staticwebapp_config_in_frontend_dir(self):
        assert (
            os.path.isfile("apps/frontend/staticwebapp.config.json")
            or os.path.isfile("client/staticwebapp.config.json")
        ), "staticwebapp.config.json must be in the frontend app directory (apps/frontend/ or client/)"


@pytest.mark.deployment
class TestDeployWorkflow:

    def test_deploy_workflow_exists(self):
        assert os.path.isfile(".github/workflows/deploy.yml"), \
            ".github/workflows/deploy.yml must exist"

    def test_deploy_workflow_valid_yaml(self):
        if os.path.isfile(".github/workflows/deploy.yml"):
            import yaml
            with open(".github/workflows/deploy.yml") as f:
                data = yaml.safe_load(f)
            assert isinstance(data, dict)
            assert "jobs" in data

    def test_deploy_workflow_has_required_jobs(self):
        if os.path.isfile(".github/workflows/deploy.yml"):
            import yaml
            with open(".github/workflows/deploy.yml") as f:
                data = yaml.safe_load(f)
            jobs = data.get("jobs", {})
            required = {"test", "deploy-dev", "deploy-release", "deploy-production", "deploy-frontend"}
            job_names = set(jobs.keys())
            missing = required - job_names
            assert len(missing) == 0, f"Deploy workflow missing jobs: {missing}"


class TestCIWorkflow:

    def test_ci_workflow_exists(self):
        assert os.path.isfile(".github/workflows/ci.yml"), \
            ".github/workflows/ci.yml must exist"

    def test_ci_workflow_valid_yaml(self):
        import yaml
        with open(".github/workflows/ci.yml") as f:
            data = yaml.safe_load(f)
        assert isinstance(data, dict)
        assert "jobs" in data

    def test_ci_workflow_has_safety_stage(self):
        import yaml
        with open(".github/workflows/ci.yml") as f:
            data = yaml.safe_load(f)
        assert "safety" in data.get("jobs", {}), \
            "CI must have a safety stage (Stage 1)"

    def test_ci_workflow_has_unit_stage(self):
        import yaml
        with open(".github/workflows/ci.yml") as f:
            data = yaml.safe_load(f)
        assert "unit" in data.get("jobs", {}), \
            "CI must have a unit test stage (Stage 2)"

    def test_ci_workflow_has_integration_stage(self):
        import yaml
        with open(".github/workflows/ci.yml") as f:
            data = yaml.safe_load(f)
        assert "integration" in data.get("jobs", {}), \
            "CI must have an integration test stage (Stage 3)"


def _read_dependencies():
    deps = []
    if os.path.isfile("requirements.txt"):
        with open("requirements.txt") as f:
            deps.extend(f.read().splitlines())
    if os.path.isfile("pyproject.toml"):
        with open("pyproject.toml") as f:
            content = f.read()
            deps.extend(content.splitlines())
    if os.path.isfile("apps/backend/requirements.txt"):
        with open("apps/backend/requirements.txt") as f:
            deps.extend(f.read().splitlines())
    return [d.strip().lower() for d in deps if d.strip() and not d.startswith("#")]
