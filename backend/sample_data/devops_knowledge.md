# DevOps Knowledge Base

## Kubernetes Troubleshooting

### CrashLoopBackOff
CrashLoopBackOff is one of the most common Kubernetes errors. It occurs when a container starts, crashes, and then Kubernetes tries to restart it repeatedly with an exponential backoff delay.

**Common Causes:**
- Application code errors causing immediate exit on startup
- Missing environment variables or configuration files
- Database connection failures at startup
- Health check (liveness probe) failing too quickly
- Insufficient memory causing OOM kills
- Missing dependencies or shared libraries
- Incorrect command or entrypoint in the container image
- File permission issues on mounted volumes

**Diagnostic Steps:**
1. Check pod status: `kubectl get pods -n <namespace>`
2. Describe the pod for events: `kubectl describe pod <pod-name> -n <namespace>`
3. Check current container logs: `kubectl logs <pod-name> -n <namespace>`
4. Check previous container logs: `kubectl logs <pod-name> -n <namespace> --previous`
5. Check events: `kubectl get events -n <namespace> --sort-by='.lastTimestamp'`

**Resolution:**
- Fix the application error shown in logs
- Ensure all required ConfigMaps and Secrets exist
- Increase initialDelaySeconds on liveness probes (start with 30-60 seconds)
- Verify database and service dependencies are reachable
- Check resource limits aren't too restrictive

### OOMKilled (Out of Memory)
The OOMKilled error occurs when a container tries to use more memory than its configured limit, causing the Linux kernel's OOM killer to terminate the process.

**Common Causes:**
- Memory limits set too low for the application's needs
- Memory leaks in the application code
- JVM heap size not properly configured relative to container limits
- Processing large datasets without streaming or pagination
- Too many concurrent connections or threads

**Diagnostic Steps:**
1. Check pod status for OOMKilled: `kubectl describe pod <pod-name>`
2. Monitor memory usage: `kubectl top pod <pod-name>`
3. Check resource limits: `kubectl get pod <pod-name> -o jsonpath='{.spec.containers[*].resources}'`

**Resolution:**
- Increase memory limits gradually (start with 2x current limit)
- For JVM apps, set -Xmx to approximately 75% of the container memory limit
- Profile the application for memory leaks using tools like pprof, heapdump, or VisualVM
- Implement streaming for large data processing
- Add memory-aware caching with eviction policies

### ImagePullBackOff
This error indicates Kubernetes cannot pull the specified container image from the registry.

**Common Causes:**
- Image tag doesn't exist (typo or deleted tag)
- Private registry without proper imagePullSecrets
- Registry authentication credentials expired
- Network connectivity issues to the registry
- Rate limiting by Docker Hub or other registries

**Resolution:**
- Verify the image exists: `docker pull <image:tag>`
- Create or update imagePullSecrets: `kubectl create secret docker-registry`
- Check network policies aren't blocking registry access
- Consider using a local registry mirror for rate-limited registries

### Pod Stuck in Pending State
A pod in Pending state cannot be scheduled to any node.

**Common Causes:**
- Insufficient cluster resources (CPU or memory)
- Node selectors or affinity rules not matching any node
- PersistentVolumeClaim not bound
- Taints on all nodes without matching tolerations
- Resource quotas exceeded

**Diagnostic Steps:**
1. Check scheduler events: `kubectl describe pod <pod-name>`
2. Check node resources: `kubectl top nodes`
3. Check PVC status: `kubectl get pvc`
4. Check taints: `kubectl describe nodes | grep -A3 Taints`

## Docker Best Practices

### Multi-Stage Builds
Multi-stage builds significantly reduce final image size by separating build dependencies from runtime.

```dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# Production stage
FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
USER node
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

### Layer Caching
Order Dockerfile instructions from least to most frequently changing:
1. Base image and system packages (rarely change)
2. Application dependencies (change occasionally)
3. Application code (changes frequently)

### Security Best Practices
- Always use a non-root user: `USER node` or `USER 1000`
- Pin base image versions: `node:20.11-alpine` not `node:latest`
- Use `.dockerignore` to exclude unnecessary files
- Scan images for vulnerabilities: `docker scout`, `trivy`, or `snyk`
- Don't store secrets in images; use runtime environment variables or secret managers
- Minimize installed packages and remove package manager caches

### Health Checks
Always include HEALTHCHECK in production Dockerfiles:
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1
```

## GitHub Actions Best Practices

### Dependency Caching
Always cache dependencies to speed up builds:
```yaml
- uses: actions/cache@v4
  with:
    path: ~/.npm
    key: ${{ runner.os }}-npm-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-npm-
```

### Matrix Testing
Test across multiple versions simultaneously:
```yaml
strategy:
  matrix:
    node-version: [18, 20, 22]
    os: [ubuntu-latest, macos-latest]
  fail-fast: false
```

### Concurrency Control
Prevent redundant builds on the same branch:
```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

### Security
- Never hardcode secrets; use `${{ secrets.NAME }}`
- Use `permissions` to limit GITHUB_TOKEN scope
- Pin action versions with SHA: `actions/checkout@abc123`
- Be cautious with `pull_request_target` trigger (runs in context of base branch)
- Never use user-controlled input directly in `run:` commands (shell injection risk)

### Artifact Management
Upload build outputs and test results:
```yaml
- uses: actions/upload-artifact@v4
  with:
    name: build-output
    path: dist/
    retention-days: 7
```

### Timeout Configuration
Always set job timeouts to prevent stuck jobs:
```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 30
```

## CI/CD Anti-Patterns

1. **No caching** - Reinstalling all dependencies on every run wastes time and bandwidth
2. **Hardcoded secrets** - Embedding passwords or API keys in pipeline files is a security risk
3. **No timeouts** - Jobs without timeouts can run indefinitely, consuming resources
4. **Sequential-only execution** - Not parallelizing independent jobs wastes build time
5. **No artifact preservation** - Losing build outputs between jobs creates redundant work
6. **Using :latest tags** - Unpinned image tags cause non-reproducible builds
7. **No security scanning** - Skipping vulnerability scans in CI leaves blind spots
8. **Monolithic pipelines** - Giant single-job pipelines are hard to debug and maintain
9. **No concurrency control** - Multiple builds on the same branch waste resources
10. **Manual deployments** - Not automating deployment from CI creates inconsistency

## Terraform Best Practices

### State Management
- Always use remote state backends (S3, GCS, Azure Blob, Terraform Cloud)
- Enable state locking to prevent concurrent modifications
- Never commit state files to version control

### Module Structure
```
terraform/
├── modules/
│   ├── networking/
│   ├── compute/
│   └── database/
├── environments/
│   ├── dev/
│   ├── staging/
│   └── production/
└── main.tf
```

### Best Practices
- Use `terraform fmt` and `terraform validate` in CI
- Pin provider versions in `required_providers`
- Use `terraform plan` before `terraform apply`, always
- Tag all resources with environment, team, and cost-center
- Use data sources instead of hardcoding resource IDs
- Implement drift detection in CI/CD pipelines

## Monitoring and Logging

### Structured Logging
Use JSON structured logging for machine-parseable logs:
```json
{"timestamp": "2024-01-15T10:30:00Z", "level": "ERROR", "service": "api", "message": "Connection refused", "host": "db-primary", "port": 5432}
```

### Key Metrics to Monitor
- **RED Method** (for services): Rate, Errors, Duration
- **USE Method** (for resources): Utilization, Saturation, Errors
- **Four Golden Signals**: Latency, Traffic, Errors, Saturation

### Alerting Best Practices
- Alert on symptoms, not causes
- Include runbooks in alert descriptions
- Set appropriate severity levels
- Avoid alert fatigue by tuning thresholds
- Use SLO-based alerting where possible
