import re
from typing import Any

from app.agents.base_agent import BaseAgent
from app.core.logging import get_logger

logger = get_logger(__name__)

ANTI_PATTERNS: list[dict[str, Any]] = [
    {
        "id": "no_cache",
        "name": "Missing Dependency Cache",
        "pattern": r"(?:npm install|pip install|yarn install|go build)",
        "negative_pattern": r"(?:cache|restore_cache|actions/cache)",
        "severity": "warning",
        "suggestion": "Add dependency caching to speed up builds. Use actions/cache for GitHub Actions.",
        "fix_example": "- uses: actions/cache@v4\n  with:\n    path: ~/.npm\n    key: ${{ runner.os }}-npm-${{ hashFiles('**/package-lock.json') }}",
    },
    {
        "id": "hardcoded_secrets",
        "name": "Potential Hardcoded Secrets",
        "pattern": r"(?:password|secret|api_key|token)\s*[:=]\s*['\"][^$\{][^'\"]{3,}['\"]",
        "negative_pattern": None,
        "severity": "critical",
        "suggestion": "Never hardcode secrets. Use encrypted secrets or environment variables.",
        "fix_example": "Use ${{ secrets.MY_SECRET }} in GitHub Actions or credentials binding in Jenkins.",
    },
    {
        "id": "no_timeout",
        "name": "Missing Job Timeout",
        "pattern": r"(?:jobs:|stages:)",
        "negative_pattern": r"timeout",
        "severity": "warning",
        "suggestion": "Add timeout-minutes to prevent stuck jobs from consuming resources.",
        "fix_example": "timeout-minutes: 30",
    },
    {
        "id": "no_artifact",
        "name": "Missing Artifact Upload",
        "pattern": r"(?:build|compile|dist|output)",
        "negative_pattern": r"(?:upload-artifact|artifacts:|archiveArtifacts)",
        "severity": "info",
        "suggestion": "Upload build artifacts to preserve outputs between jobs and for debugging.",
        "fix_example": "- uses: actions/upload-artifact@v4\n  with:\n    name: build\n    path: dist/",
    },
    {
        "id": "no_matrix",
        "name": "No Matrix Testing",
        "pattern": r"(?:node-version|python-version|java-version):\s*['\"]?\d",
        "negative_pattern": r"matrix",
        "severity": "info",
        "suggestion": "Use matrix strategy to test across multiple versions simultaneously.",
        "fix_example": "strategy:\n  matrix:\n    node-version: [18, 20, 22]",
    },
    {
        "id": "latest_tag",
        "name": "Using :latest Tag",
        "pattern": r"image:\s*\S+:latest",
        "negative_pattern": None,
        "severity": "warning",
        "suggestion": "Pin image versions for reproducible builds. Using :latest can cause unexpected breakages.",
        "fix_example": "image: node:20-alpine  # Instead of node:latest",
    },
    {
        "id": "no_fail_fast",
        "name": "No Fail-Fast Strategy",
        "pattern": r"matrix:",
        "negative_pattern": r"fail-fast",
        "severity": "info",
        "suggestion": "Consider setting fail-fast: false to see all matrix failures, not just the first.",
        "fix_example": "strategy:\n  fail-fast: false",
    },
    {
        "id": "no_concurrency",
        "name": "No Concurrency Control",
        "pattern": r"(?:on:\s*(?:push|pull_request))",
        "negative_pattern": r"concurrency",
        "severity": "info",
        "suggestion": "Add concurrency groups to cancel redundant runs on the same branch.",
        "fix_example": "concurrency:\n  group: ${{ github.workflow }}-${{ github.ref }}\n  cancel-in-progress: true",
    },
    {
        "id": "no_security_scan",
        "name": "No Security Scanning",
        "pattern": r"(?:build|test|deploy)",
        "negative_pattern": r"(?:snyk|trivy|codeql|semgrep|safety|audit|security)",
        "severity": "warning",
        "suggestion": "Add security scanning (dependency audit, container scan, SAST) to your pipeline.",
        "fix_example": "- name: Security audit\n  run: npm audit --audit-level=moderate",
    },
    {
        "id": "shell_injection",
        "name": "Potential Shell Injection",
        "pattern": r"run:.*\$\{\{\s*github\.event\.(?:issue|pull_request|comment)",
        "negative_pattern": None,
        "severity": "critical",
        "suggestion": "User-controlled input in run commands can lead to shell injection. Use an intermediate environment variable.",
        "fix_example": "env:\n  TITLE: ${{ github.event.issue.title }}\nrun: echo \"$TITLE\"",
    },
]

PIPELINE_TEMPLATES: dict[str, str] = {
    "github_actions": """name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

concurrency:
  group: ${{{{ github.workflow }}}}-${{{{ github.ref }}}}
  cancel-in-progress: true

jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    strategy:
      matrix:
        node-version: [18, 20]
      fail-fast: false

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{{{ matrix.node-version }}}}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Lint
        run: npm run lint

      - name: Test
        run: npm test -- --coverage

      - name: Upload coverage
        uses: actions/upload-artifact@v4
        with:
          name: coverage-${{{{ matrix.node-version }}}}
          path: coverage/

  build:
    needs: test
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Build
        run: npm run build

      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: build
          path: dist/

  docker:
    needs: build
    runs-on: ubuntu-latest
    timeout-minutes: 20
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - name: Build Docker image
        run: docker build -t app:${{{{ github.sha }}}} .

      - name: Security scan
        run: docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image app:${{{{ github.sha }}}}
""",
    "jenkins": """pipeline {{
    agent any

    options {{
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }}

    environment {{
        APP_NAME = '{app_name}'
        DOCKER_REGISTRY = 'registry.example.com'
    }}

    stages {{
        stage('Checkout') {{
            steps {{
                checkout scm
            }}
        }}

        stage('Install') {{
            steps {{
                sh 'npm ci'
            }}
        }}

        stage('Lint & Test') {{
            parallel {{
                stage('Lint') {{
                    steps {{
                        sh 'npm run lint'
                    }}
                }}
                stage('Test') {{
                    steps {{
                        sh 'npm test -- --coverage'
                    }}
                    post {{
                        always {{
                            junit 'test-results/**/*.xml'
                            publishHTML(target: [
                                reportName: 'Coverage Report',
                                reportDir: 'coverage/lcov-report',
                                reportFiles: 'index.html'
                            ])
                        }}
                    }}
                }}
            }}
        }}

        stage('Build') {{
            steps {{
                sh 'npm run build'
                archiveArtifacts artifacts: 'dist/**/*', fingerprint: true
            }}
        }}

        stage('Docker Build') {{
            when {{
                branch 'main'
            }}
            steps {{
                sh "docker build -t ${{DOCKER_REGISTRY}}/${{APP_NAME}}:${{BUILD_NUMBER}} ."
            }}
        }}
    }}

    post {{
        failure {{
            echo 'Pipeline failed!'
        }}
        success {{
            echo 'Pipeline succeeded!'
        }}
        always {{
            cleanWs()
        }}
    }}
}}
""",
    "gitlab_ci": """stages:
  - test
  - build
  - deploy

variables:
  NODE_VERSION: "20"

cache:
  key: ${{CI_COMMIT_REF_SLUG}}
  paths:
    - node_modules/
    - .npm/

test:
  stage: test
  image: node:${{NODE_VERSION}}-alpine
  script:
    - npm ci --cache .npm
    - npm run lint
    - npm test -- --coverage
  coverage: '/Lines\\s*:\\s*(\\d+\\.?\\d*)%/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml
    expire_in: 7 days
  timeout: 30m

build:
  stage: build
  image: node:${{NODE_VERSION}}-alpine
  script:
    - npm ci --cache .npm
    - npm run build
  artifacts:
    paths:
      - dist/
    expire_in: 1 week
  only:
    - main
    - develop

docker_build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker tag $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA $CI_REGISTRY_IMAGE:latest
  only:
    - main
  timeout: 20m
""",
}


class PipelineAgent(BaseAgent):
    agent_type = "pipeline"

    async def validate_input(self, input_data: dict[str, Any]) -> tuple[bool, str]:
        action = input_data.get("action", "analyze")
        if action == "analyze":
            yaml_content = input_data.get("yaml_content", "")
            if not yaml_content or len(yaml_content) < 10:
                return False, "yaml_content is required and must be at least 10 characters."
        elif action == "generate":
            requirements = input_data.get("requirements", "")
            if not requirements or len(requirements) < 10:
                return False, "requirements is required and must be at least 10 characters."
        return True, "Valid"

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        action = input_data.get("action", "analyze")

        if action == "analyze":
            return await self._analyze_pipeline(input_data)
        elif action == "generate":
            return await self._generate_pipeline(input_data)
        elif action == "validate":
            return self._validate_yaml(input_data)
        else:
            return {"error": f"Unknown action: {action}"}

    async def _analyze_pipeline(self, input_data: dict[str, Any]) -> dict[str, Any]:
        yaml_content = input_data["yaml_content"]
        platform = input_data.get("platform", "github_actions")

        anti_patterns = self._detect_anti_patterns(yaml_content)
        score = self._calculate_score(anti_patterns)

        ollama_available = await self._is_ollama_available()
        llm_analysis = ""
        optimized_yaml = None

        if ollama_available:
            prompt = (
                f"Analyze this {platform} CI/CD pipeline YAML and provide:\n"
                "1. Summary of what it does\n"
                "2. Top 3 improvements\n"
                "3. An optimized version\n\n"
                f"```yaml\n{yaml_content}\n```"
            )
            llm_analysis = await self._call_ollama(prompt, model=self._code_model)

        suggestions = []
        for ap in anti_patterns:
            suggestions.append({
                "id": ap["id"],
                "title": ap["name"],
                "severity": ap["severity"],
                "description": ap["suggestion"],
                "fix_example": ap["fix_example"],
            })

        return {
            "action": "analyze",
            "platform": platform,
            "anti_patterns": anti_patterns,
            "suggestions": suggestions,
            "score": score,
            "summary": llm_analysis or self._generate_summary(anti_patterns, score),
            "optimized_yaml": optimized_yaml,
        }

    def _detect_anti_patterns(self, yaml_content: str) -> list[dict[str, Any]]:
        found = []
        for pattern_def in ANTI_PATTERNS:
            match = re.search(pattern_def["pattern"], yaml_content, re.IGNORECASE)
            if match:
                neg = pattern_def.get("negative_pattern")
                if neg is None:
                    found.append(pattern_def)
                elif not re.search(neg, yaml_content, re.IGNORECASE):
                    found.append(pattern_def)
        return found

    def _calculate_score(self, anti_patterns: list[dict[str, Any]]) -> int:
        score = 100
        for ap in anti_patterns:
            if ap["severity"] == "critical":
                score -= 25
            elif ap["severity"] == "warning":
                score -= 10
            elif ap["severity"] == "info":
                score -= 5
        return max(0, score)

    def _generate_summary(self, anti_patterns: list[dict[str, Any]], score: int) -> str:
        critical = sum(1 for ap in anti_patterns if ap["severity"] == "critical")
        warnings = sum(1 for ap in anti_patterns if ap["severity"] == "warning")
        infos = sum(1 for ap in anti_patterns if ap["severity"] == "info")

        grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F"

        return (
            f"Pipeline Score: {score}/100 (Grade: {grade}). "
            f"Found {len(anti_patterns)} issues: "
            f"{critical} critical, {warnings} warnings, {infos} informational. "
            + ("Immediate action required for critical issues." if critical > 0 else "Pipeline is in good shape.")
        )

    async def _generate_pipeline(self, input_data: dict[str, Any]) -> dict[str, Any]:
        requirements = input_data["requirements"]
        platform = input_data.get("platform", "github_actions")

        ollama_available = await self._is_ollama_available()

        if ollama_available:
            prompt = (
                f"Generate a production-ready {platform} CI/CD pipeline for:\n{requirements}\n\n"
                "Include: caching, testing, linting, building, security scanning, "
                "artifact upload, and proper triggers. Output ONLY the YAML."
            )
            result = await self._call_ollama(prompt, model=self._code_model)
            if result.strip():
                return {
                    "action": "generate",
                    "platform": platform,
                    "yaml_content": result.strip(),
                    "source": "llm",
                    "requirements": requirements,
                }

        return await self._rule_based_fallback(input_data)

    def _validate_yaml(self, input_data: dict[str, Any]) -> dict[str, Any]:
        import yaml

        yaml_content = input_data.get("yaml_content", "")
        errors: list[str] = []
        try:
            parsed = yaml.safe_load(yaml_content)
            if parsed is None:
                errors.append("YAML is empty or contains only comments.")
            elif not isinstance(parsed, dict):
                errors.append("Top-level YAML must be a mapping (dict).")
        except yaml.YAMLError as e:
            errors.append(f"YAML syntax error: {e}")

        return {
            "action": "validate",
            "valid": len(errors) == 0,
            "errors": errors,
        }

    async def _rule_based_fallback(self, input_data: dict[str, Any]) -> dict[str, Any]:
        platform = input_data.get("platform", "github_actions")
        requirements = input_data.get("requirements", "web application")

        template = PIPELINE_TEMPLATES.get(platform, PIPELINE_TEMPLATES["github_actions"])
        if platform == "jenkins":
            app_name = "my-app"
            for word in requirements.split():
                if len(word) > 3 and word.isalpha():
                    app_name = word.lower()
                    break
            template = template.format(app_name=app_name)

        return {
            "action": "generate",
            "platform": platform,
            "yaml_content": template,
            "source": "template",
            "requirements": requirements,
        }
