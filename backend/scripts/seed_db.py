"""Seed script: creates demo user, project, sample data, and indexes FAISS."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.security import get_password_hash
from app.db.database import async_session_maker, init_db
from app.ml.rag_service import rag_service
from app.models.models import AgentRun, LogEntry, Pipeline, Project, User

SAMPLE_DATA_DIR = Path(__file__).parent.parent / "sample_data"


async def seed():
    print("Initializing database...")
    await init_db()

    async with async_session_maker() as db:
        from sqlalchemy import select

        result = await db.execute(select(User).where(User.email == "demo@devops.ai"))
        if result.scalar_one_or_none():
            print("Demo user already exists. Skipping seed.")
            return

        print("Creating demo user...")
        user = User(
            email="demo@devops.ai",
            username="demo",
            hashed_password=get_password_hash("demo1234"),
            role="admin",
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        print(f"  Created user: {user.email} (role: {user.role})")

        print("Creating sample project...")
        project = Project(
            name="E-Commerce Platform",
            description="Full-stack e-commerce application with microservices architecture. "
            "Includes API gateway, product service, order service, and payment service.",
            repo_url="https://github.com/example/ecommerce-platform",
            user_id=user.id,
        )
        db.add(project)
        await db.flush()
        await db.refresh(project)
        print(f"  Created project: {project.name}")

        print("Adding sample pipeline...")
        yaml_path = SAMPLE_DATA_DIR / "sample_github_actions.yaml"
        yaml_content = yaml_path.read_text() if yaml_path.exists() else "name: CI\non: [push]\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4"
        pipeline = Pipeline(
            name="CI/CD Pipeline",
            platform="github_actions",
            yaml_content=yaml_content,
            project_id=project.id,
        )
        db.add(pipeline)
        await db.flush()
        print("  Added sample pipeline")

        print("Adding sample logs...")
        logs_path = SAMPLE_DATA_DIR / "sample_k8s_logs.log"
        logs_content = logs_path.read_text() if logs_path.exists() else "Sample K8s log entry"
        log_entry = LogEntry(
            source="kubernetes",
            level="ERROR",
            content=logs_content,
            metadata_={"cluster": "production", "namespace": "default"},
            project_id=project.id,
        )
        db.add(log_entry)
        await db.flush()
        print("  Added sample log entries")

        print("Adding sample agent runs...")
        runs = [
            AgentRun(
                agent_type="heal",
                status="completed",
                input_data={"logs": "CrashLoopBackOff in pod web-app-xyz", "context": {"namespace": "production"}},
                output_data={
                    "diagnosis": [{"error": "CrashLoopBackOff", "severity": "high"}],
                    "summary": "Found CrashLoopBackOff. Check container logs and liveness probes.",
                },
                execution_time_ms=1250,
                user_id=user.id,
                project_id=project.id,
            ),
            AgentRun(
                agent_type="pipeline",
                status="completed",
                input_data={"action": "analyze", "yaml_content": yaml_content},
                output_data={
                    "score": 55,
                    "anti_patterns": ["no_cache", "no_timeout", "no_artifact"],
                    "summary": "Pipeline Score: 55/100. Found 5 issues.",
                },
                execution_time_ms=890,
                user_id=user.id,
                project_id=project.id,
            ),
            AgentRun(
                agent_type="infra",
                status="completed",
                input_data={"config_type": "docker_compose", "app_description": "E-commerce microservices"},
                output_data={
                    "config_type": "docker_compose",
                    "source": "template",
                    "generated_config": "version: '3.8'\nservices:\n  ...",
                },
                execution_time_ms=450,
                user_id=user.id,
                project_id=project.id,
            ),
        ]
        for run in runs:
            db.add(run)
        await db.flush()
        print(f"  Added {len(runs)} sample agent runs")

        await db.commit()

    print("Indexing DevOps knowledge base into FAISS...")
    knowledge_path = SAMPLE_DATA_DIR / "devops_knowledge.md"
    if knowledge_path.exists():
        content = knowledge_path.read_text()
        chunks = rag_service.index_documents([content], source="devops_knowledge_base")
        print(f"  Indexed {chunks} chunks into vector store")
    else:
        print("  Knowledge base file not found, skipping FAISS indexing")

    print("\nSeed complete!")
    print("  Login: demo@devops.ai / demo1234")
    print("  Project: E-Commerce Platform")


if __name__ == "__main__":
    asyncio.run(seed())
