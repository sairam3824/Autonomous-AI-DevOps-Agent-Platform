from typing import Any

from app.agents.base_agent import BaseAgent
from app.core.logging import get_logger

logger = get_logger(__name__)

DOCKER_COMPOSE_TEMPLATES: dict[str, str] = {
    "web_db": """version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/app
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: always
    deploy:
      resources:
        limits:
          memory: 1G

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: app
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: always

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: always

volumes:
  postgres_data:
  redis_data:
""",
    "microservices": """version: '3.8'

services:
  api-gateway:
    build:
      context: ./gateway
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    environment:
      - SERVICE_A_URL=http://service-a:8001
      - SERVICE_B_URL=http://service-b:8002
    depends_on:
      - service-a
      - service-b
    restart: always

  service-a:
    build:
      context: ./service-a
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/service_a
      - RABBITMQ_URL=amqp://rabbit:5672
    depends_on:
      - db
      - rabbitmq
    restart: always

  service-b:
    build:
      context: ./service-b
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/service_b
      - RABBITMQ_URL=amqp://rabbit:5672
    depends_on:
      - db
      - rabbitmq
    restart: always

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: app
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  rabbitmq:
    image: rabbitmq:3-management-alpine
    ports:
      - "15672:15672"
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    restart: always

volumes:
  postgres_data:
  rabbitmq_data:
""",
    "static_site": """version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./dist:/usr/share/nginx/html:ro
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    restart: always
    deploy:
      resources:
        limits:
          memory: 256M
""",
}

K8S_DEPLOYMENT_TEMPLATE = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}
  namespace: {namespace}
  labels:
    app: {name}
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: {name}
  template:
    metadata:
      labels:
        app: {name}
    spec:
      containers:
        - name: {name}
          image: {image}
          ports:
            - containerPort: {port}
          resources:
            requests:
              memory: "{mem_request}"
              cpu: "{cpu_request}"
            limits:
              memory: "{mem_limit}"
              cpu: "{cpu_limit}"
          livenessProbe:
            httpGet:
              path: {health_path}
              port: {port}
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: {health_path}
              port: {port}
            initialDelaySeconds: 5
            periodSeconds: 5
          env:
            - name: APP_ENV
              value: "production"
      restartPolicy: Always
---
apiVersion: v1
kind: Service
metadata:
  name: {name}-service
  namespace: {namespace}
spec:
  selector:
    app: {name}
  ports:
    - protocol: TCP
      port: {port}
      targetPort: {port}
  type: ClusterIP
"""

TERRAFORM_TEMPLATE = """terraform {{
  required_providers {{
    local = {{
      source  = "hashicorp/local"
      version = "~> 2.5"
    }}
    null = {{
      source  = "hashicorp/null"
      version = "~> 3.2"
    }}
  }}
}}

variable "app_name" {{
  description = "Application name"
  type        = string
  default     = "{app_name}"
}}

variable "environment" {{
  description = "Environment"
  type        = string
  default     = "production"
}}

variable "replicas" {{
  description = "Number of replicas"
  type        = number
  default     = {replicas}
}}

resource "local_file" "docker_compose" {{
  content  = <<-EOT
{compose_content}
EOT
  filename = "${{path.module}}/output/docker-compose.yml"
}}

resource "local_file" "env_file" {{
  content  = <<-EOT
APP_NAME=${{var.app_name}}
ENVIRONMENT=${{var.environment}}
REPLICAS=${{var.replicas}}
EOT
  filename = "${{path.module}}/output/.env"
}}

resource "null_resource" "docker_deploy" {{
  triggers = {{
    compose_hash = local_file.docker_compose.content_md5
  }}

  provisioner "local-exec" {{
    command     = "docker compose -f ${{local_file.docker_compose.filename}} up -d"
    working_dir = "${{path.module}}/output"
  }}
}}

output "app_name" {{
  value = var.app_name
}}

output "compose_file" {{
  value = local_file.docker_compose.filename
}}
"""


class InfraAgent(BaseAgent):
    agent_type = "infra"

    async def validate_input(self, input_data: dict[str, Any]) -> tuple[bool, str]:
        config_type = input_data.get("config_type", "")
        if config_type not in ("docker_compose", "kubernetes", "terraform"):
            return False, f"Invalid config_type: {config_type}. Must be docker_compose, kubernetes, or terraform."
        description = input_data.get("app_description", "")
        if not description or len(description) < 5:
            return False, "app_description is required and must be at least 5 characters."
        return True, "Valid"

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        config_type = input_data["config_type"]
        description = input_data["app_description"]
        options = input_data.get("options", {})

        ollama_available = await self._is_ollama_available()

        if ollama_available:
            return await self._llm_generate(config_type, description, options)
        else:
            return await self._rule_based_fallback(input_data)

    async def _llm_generate(
        self, config_type: str, description: str, options: dict[str, Any]
    ) -> dict[str, Any]:
        system_prompt = (
            "You are an expert DevOps engineer. Generate production-ready infrastructure "
            "configurations based on the user's description. Output ONLY the configuration "
            "content with no explanations or markdown fences."
        )

        prompts = {
            "docker_compose": (
                f"Generate a Docker Compose YAML for: {description}\n"
                f"Options: {options}\n"
                "Include health checks, resource limits, named volumes, proper networking, "
                "and restart policies. Use version 3.8."
            ),
            "kubernetes": (
                f"Generate Kubernetes manifests for: {description}\n"
                f"Options: {options}\n"
                "Include Deployment, Service, ConfigMap. Add resource requests/limits, "
                "liveness/readiness probes, and proper labels."
            ),
            "terraform": (
                f"Generate a Terraform configuration using local provider for: {description}\n"
                f"Options: {options}\n"
                "Use local and null providers. Include variables, resources, and outputs."
            ),
        }

        model = self._code_model if config_type != "terraform" else self._model
        result = await self._call_ollama(prompts[config_type], model=model, system=system_prompt)

        if result.strip():
            return {
                "config_type": config_type,
                "generated_config": result.strip(),
                "source": "llm",
                "model": model,
                "description": description,
            }

        return await self._rule_based_fallback(
            {"config_type": config_type, "app_description": description, "options": options}
        )

    async def _rule_based_fallback(self, input_data: dict[str, Any]) -> dict[str, Any]:
        config_type = input_data["config_type"]
        description = input_data.get("app_description", "").lower()
        options = input_data.get("options", {})

        if config_type == "docker_compose":
            return self._generate_docker_compose(description, options)
        elif config_type == "kubernetes":
            return self._generate_kubernetes(description, options)
        elif config_type == "terraform":
            return self._generate_terraform(description, options)
        return {"error": f"Unknown config_type: {config_type}"}

    def _generate_docker_compose(self, description: str, options: dict[str, Any]) -> dict[str, Any]:
        if any(kw in description for kw in ["microservice", "micro-service", "gateway"]):
            template = DOCKER_COMPOSE_TEMPLATES["microservices"]
        elif any(kw in description for kw in ["static", "nginx", "html"]):
            template = DOCKER_COMPOSE_TEMPLATES["static_site"]
        else:
            template = DOCKER_COMPOSE_TEMPLATES["web_db"]

        return {
            "config_type": "docker_compose",
            "generated_config": template,
            "source": "template",
            "template_used": "auto-detected",
            "description": description,
        }

    def _generate_kubernetes(self, description: str, options: dict[str, Any]) -> dict[str, Any]:
        name = options.get("name", "app")
        namespace = options.get("namespace", "default")
        image = options.get("image", f"{name}:latest")
        port = options.get("port", 8000)
        replicas = options.get("replicas", 2)

        config = K8S_DEPLOYMENT_TEMPLATE.format(
            name=name,
            namespace=namespace,
            image=image,
            port=port,
            replicas=replicas,
            mem_request="128Mi",
            cpu_request="100m",
            mem_limit="512Mi",
            cpu_limit="500m",
            health_path=options.get("health_path", "/health"),
        )

        return {
            "config_type": "kubernetes",
            "generated_config": config,
            "source": "template",
            "description": description,
        }

    def _generate_terraform(self, description: str, options: dict[str, Any]) -> dict[str, Any]:
        app_name = options.get("name", "my-app")
        replicas = options.get("replicas", 2)
        compose = DOCKER_COMPOSE_TEMPLATES["web_db"].replace("\n", "\n    ")

        config = TERRAFORM_TEMPLATE.format(
            app_name=app_name,
            replicas=replicas,
            compose_content=compose,
        )

        return {
            "config_type": "terraform",
            "generated_config": config,
            "source": "template",
            "description": description,
        }
