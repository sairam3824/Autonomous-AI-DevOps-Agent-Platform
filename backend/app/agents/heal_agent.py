import re
from typing import Any

from app.agents.base_agent import BaseAgent
from app.core.logging import get_logger

logger = get_logger(__name__)

K8S_ERROR_PATTERNS: list[dict[str, Any]] = [
    {
        "pattern": r"CrashLoopBackOff",
        "name": "CrashLoopBackOff",
        "category": "pod_crash",
        "description": "Container is repeatedly crashing and Kubernetes keeps restarting it.",
        "diagnostic_commands": [
            "kubectl describe pod {pod_name} -n {namespace}",
            "kubectl logs {pod_name} -n {namespace} --previous",
            "kubectl get events -n {namespace} --field-selector involvedObject.name={pod_name}",
        ],
        "common_causes": [
            "Application error causing exit on startup",
            "Missing configuration or environment variables",
            "Health check failing immediately",
            "Missing dependencies or volumes",
            "Insufficient memory causing OOM",
        ],
        "remediation": [
            "Check container logs: kubectl logs {pod_name} -n {namespace} --previous",
            "Verify environment variables and ConfigMaps are correct",
            "Check if required services/databases are reachable",
            "Increase initialDelaySeconds on liveness probe",
            "Check resource limits aren't too restrictive",
        ],
        "safe_commands": [
            "kubectl rollout restart deployment/{deployment_name} -n {namespace}",
            "kubectl scale deployment/{deployment_name} --replicas=0 -n {namespace} && kubectl scale deployment/{deployment_name} --replicas=1 -n {namespace}",
        ],
    },
    {
        "pattern": r"OOMKilled",
        "name": "OOMKilled",
        "category": "resource",
        "description": "Container exceeded its memory limit and was killed by the kernel.",
        "diagnostic_commands": [
            "kubectl describe pod {pod_name} -n {namespace}",
            "kubectl top pod {pod_name} -n {namespace}",
            "kubectl get pod {pod_name} -n {namespace} -o jsonpath='{.spec.containers[*].resources}'",
        ],
        "common_causes": [
            "Memory limit set too low for the application",
            "Memory leak in the application",
            "JVM heap size not aligned with container limits",
            "Large data processing without streaming",
        ],
        "remediation": [
            "Increase memory limits in the deployment spec",
            "Profile the application for memory leaks",
            "For JVM apps: set -Xmx to ~75% of container memory limit",
            "Implement pagination or streaming for large datasets",
        ],
        "safe_commands": [
            "kubectl patch deployment {deployment_name} -n {namespace} -p '{\"spec\":{\"template\":{\"spec\":{\"containers\":[{\"name\":\"{container_name}\",\"resources\":{\"limits\":{\"memory\":\"1Gi\"}}}]}}}}'",
        ],
    },
    {
        "pattern": r"ImagePullBackOff|ErrImagePull",
        "name": "ImagePullBackOff",
        "category": "image",
        "description": "Kubernetes cannot pull the container image.",
        "diagnostic_commands": [
            "kubectl describe pod {pod_name} -n {namespace}",
            "kubectl get events -n {namespace} | grep -i pull",
            "kubectl get secrets -n {namespace} | grep -i registry",
        ],
        "common_causes": [
            "Image tag doesn't exist in the registry",
            "Private registry without proper imagePullSecrets",
            "Registry is unreachable (network issue)",
            "Typo in image name or tag",
        ],
        "remediation": [
            "Verify image exists: docker pull {image_name}",
            "Check imagePullSecrets are configured correctly",
            "Ensure registry credentials are valid and not expired",
            "Verify network connectivity to the registry",
        ],
        "safe_commands": [
            "kubectl create secret docker-registry regcred --docker-server=<registry> --docker-username=<user> --docker-password=<pass> -n {namespace}",
        ],
    },
    {
        "pattern": r"Pending",
        "name": "Pod Pending",
        "category": "scheduling",
        "description": "Pod cannot be scheduled to any node.",
        "diagnostic_commands": [
            "kubectl describe pod {pod_name} -n {namespace}",
            "kubectl get nodes -o wide",
            "kubectl describe nodes | grep -A5 'Allocated resources'",
            "kubectl get events -n {namespace} --field-selector reason=FailedScheduling",
        ],
        "common_causes": [
            "Insufficient CPU or memory on nodes",
            "Node selectors or affinity rules not satisfied",
            "PersistentVolumeClaim not bound",
            "Taints on nodes without matching tolerations",
        ],
        "remediation": [
            "Check node resources: kubectl top nodes",
            "Review nodeSelector/affinity rules in the pod spec",
            "Verify PVC is bound: kubectl get pvc -n {namespace}",
            "Check for taints: kubectl describe nodes | grep Taints",
        ],
        "safe_commands": [],
    },
    {
        "pattern": r"Evicted",
        "name": "Pod Evicted",
        "category": "resource",
        "description": "Pod was evicted due to node resource pressure.",
        "diagnostic_commands": [
            "kubectl get pods -n {namespace} --field-selector status.phase=Failed",
            "kubectl describe node {node_name}",
            "kubectl top nodes",
        ],
        "common_causes": [
            "Node disk pressure (ephemeral storage full)",
            "Node memory pressure",
            "Node PID pressure",
        ],
        "remediation": [
            "Clean up unused images: docker system prune",
            "Set ephemeral-storage limits on pods",
            "Add more nodes to the cluster",
            "Set resource requests/limits properly",
        ],
        "safe_commands": [
            "kubectl delete pods --field-selector status.phase=Failed -n {namespace}",
        ],
    },
    {
        "pattern": r"CreateContainerConfigError",
        "name": "CreateContainerConfigError",
        "category": "config",
        "description": "Container could not be created due to configuration error.",
        "diagnostic_commands": [
            "kubectl describe pod {pod_name} -n {namespace}",
            "kubectl get configmaps -n {namespace}",
            "kubectl get secrets -n {namespace}",
        ],
        "common_causes": [
            "Referenced ConfigMap or Secret doesn't exist",
            "Missing key in ConfigMap/Secret",
            "Invalid volume mount configuration",
        ],
        "remediation": [
            "Verify all referenced ConfigMaps exist",
            "Verify all referenced Secrets exist",
            "Check volume mount paths are correct",
            "Ensure referenced keys exist in ConfigMaps/Secrets",
        ],
        "safe_commands": [],
    },
]

DOCKER_ERROR_PATTERNS: list[dict[str, Any]] = [
    {
        "pattern": r"exit code 137",
        "name": "OOM Kill (Exit 137)",
        "description": "Container was killed due to out-of-memory. Exit code 137 = SIGKILL.",
        "remediation": [
            "Increase memory limit in docker-compose or docker run",
            "Check for memory leaks in the application",
            "Use --memory flag to set appropriate limits",
        ],
    },
    {
        "pattern": r"exit code 1",
        "name": "Application Error (Exit 1)",
        "description": "Application exited with error code 1 (general error).",
        "remediation": [
            "Check application logs: docker logs <container>",
            "Verify environment variables are set correctly",
            "Check if required services are reachable",
        ],
    },
    {
        "pattern": r"port is already allocated|address already in use",
        "name": "Port Conflict",
        "description": "The requested port is already in use by another process.",
        "remediation": [
            "Find process using port: lsof -i :<port> or netstat -tlnp | grep <port>",
            "Stop the conflicting process or change the port mapping",
            "Use a different host port in your docker-compose.yml",
        ],
    },
    {
        "pattern": r"network .+ not found",
        "name": "Network Not Found",
        "description": "Docker network referenced in compose file doesn't exist.",
        "remediation": [
            "Create the network: docker network create <name>",
            "Remove external: true from compose file to auto-create",
            "Check network name for typos",
        ],
    },
]


class HealAgent(BaseAgent):
    agent_type = "heal"

    async def validate_input(self, input_data: dict[str, Any]) -> tuple[bool, str]:
        logs = input_data.get("logs", "")
        error_description = input_data.get("error_description", "")
        if not logs and not error_description:
            return False, "Either 'logs' or 'error_description' is required."
        return True, "Valid"

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        logs = input_data.get("logs", "")
        error_description = input_data.get("error_description", "")
        context = input_data.get("context", {})
        combined_input = f"{error_description}\n{logs}".strip()

        k8s_matches = self._match_k8s_errors(combined_input)
        docker_matches = self._match_docker_errors(combined_input)

        pod_name = context.get("pod_name", "<pod-name>")
        namespace = context.get("namespace", "default")
        deployment_name = context.get("deployment_name", "<deployment-name>")
        container_name = context.get("container_name", "<container-name>")
        node_name = context.get("node_name", "<node-name>")
        image_name = context.get("image_name", "<image-name>")

        diagnosis: list[dict[str, Any]] = []

        for match in k8s_matches:
            entry = {
                "error": match["name"],
                "category": match["category"],
                "description": match["description"],
                "common_causes": match["common_causes"],
                "diagnostic_commands": [
                    cmd.format(
                        pod_name=pod_name,
                        namespace=namespace,
                        deployment_name=deployment_name,
                        container_name=container_name,
                        node_name=node_name,
                        image_name=image_name,
                    )
                    for cmd in match["diagnostic_commands"]
                ],
                "remediation": match["remediation"],
                "safe_auto_fix": [
                    cmd.format(
                        pod_name=pod_name,
                        namespace=namespace,
                        deployment_name=deployment_name,
                        container_name=container_name,
                    )
                    for cmd in match.get("safe_commands", [])
                ],
            }
            diagnosis.append(entry)

        for match in docker_matches:
            entry = {
                "error": match["name"],
                "category": "docker",
                "description": match["description"],
                "remediation": match["remediation"],
                "diagnostic_commands": [],
                "common_causes": [],
                "safe_auto_fix": [],
            }
            diagnosis.append(entry)

        ollama_available = await self._is_ollama_available()
        llm_analysis = ""

        if ollama_available and combined_input:
            prompt = (
                "You are a Kubernetes and Docker troubleshooting expert. "
                "Analyze these logs/errors and provide:\n"
                "1. Root cause analysis\n"
                "2. Step-by-step fix instructions\n"
                "3. Prevention measures\n\n"
                f"Error/Logs:\n{combined_input[:3000]}"
            )
            llm_analysis = await self._call_ollama(prompt)

        return {
            "diagnosis": diagnosis,
            "errors_found": len(diagnosis),
            "llm_analysis": llm_analysis,
            "severity": self._calculate_severity(diagnosis),
            "summary": self._generate_heal_summary(diagnosis, llm_analysis),
        }

    def _match_k8s_errors(self, text: str) -> list[dict[str, Any]]:
        matched = []
        for pattern_def in K8S_ERROR_PATTERNS:
            if re.search(pattern_def["pattern"], text, re.IGNORECASE):
                matched.append(pattern_def)
        return matched

    def _match_docker_errors(self, text: str) -> list[dict[str, Any]]:
        matched = []
        for pattern_def in DOCKER_ERROR_PATTERNS:
            if re.search(pattern_def["pattern"], text, re.IGNORECASE):
                matched.append(pattern_def)
        return matched

    def _calculate_severity(self, diagnosis: list[dict[str, Any]]) -> str:
        if not diagnosis:
            return "unknown"
        categories = [d.get("category", "") for d in diagnosis]
        if "pod_crash" in categories or "resource" in categories:
            return "high"
        if "image" in categories or "config" in categories:
            return "medium"
        return "low"

    def _generate_heal_summary(self, diagnosis: list[dict[str, Any]], llm_analysis: str) -> str:
        if not diagnosis and not llm_analysis:
            return "No known error patterns detected. Consider providing more log context."

        errors = [d["error"] for d in diagnosis]
        summary = f"Found {len(diagnosis)} issue(s): {', '.join(errors)}. "

        if diagnosis:
            first = diagnosis[0]
            summary += f"Primary issue: {first['description']} "
            if first.get("remediation"):
                summary += f"Recommended first step: {first['remediation'][0]}"

        return summary

    async def _rule_based_fallback(self, input_data: dict[str, Any]) -> dict[str, Any]:
        return await self.execute(input_data)
