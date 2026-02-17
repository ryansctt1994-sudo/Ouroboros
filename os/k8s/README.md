# Kubernetes Configuration for EDEN AI

This directory contains Kubernetes manifests for deploying and scaling the EDEN AI service.

## Files

- **eden-ai-deployment.yaml**: Main deployment configuration with resource limits, health checks, and volume mounts
- **eden-ai-service.yaml**: Service definitions (ClusterIP and LoadBalancer)
- **eden-ai-hpa.yaml**: HorizontalPodAutoscaler for dynamic scaling (2-20 replicas)
- **prometheus-servicemonitor.yaml**: Prometheus ServiceMonitor for metrics collection
- **secrets.yaml**: Kubernetes secrets for API keys and TLS certificates

## Prerequisites

1. Kubernetes cluster (v1.22+)
2. kubectl configured
3. Prometheus Operator (for ServiceMonitor)
4. Prometheus Adapter (for custom metrics in HPA)
5. Persistent Volume for models

## Quick Start

### 1. Create Namespace (optional)
```bash
kubectl create namespace eden
```

### 2. Update Secrets
Edit `secrets.yaml` and replace placeholder values:
```bash
# Generate API key
echo -n "your-actual-api-key" | base64

# Update secrets.yaml with the encoded value
kubectl apply -f secrets.yaml
```

### 3. Create PersistentVolumeClaim for Models
```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: eden-models-pvc
  namespace: default
spec:
  accessModes:
    - ReadOnlyMany
  resources:
    requests:
      storage: 5Gi
  storageClassName: standard
EOF
```

### 4. Deploy Eden AI
```bash
# Apply all manifests
kubectl apply -f k8s/

# Or apply individually
kubectl apply -f secrets.yaml
kubectl apply -f eden-ai-deployment.yaml
kubectl apply -f eden-ai-service.yaml
kubectl apply -f eden-ai-hpa.yaml
kubectl apply -f prometheus-servicemonitor.yaml
```

### 5. Verify Deployment
```bash
# Check pods
kubectl get pods -l app=eden-ai

# Check HPA status
kubectl get hpa eden-ai-hpa

# Check service
kubectl get svc eden-ai

# View logs
kubectl logs -l app=eden-ai --tail=100 -f
```

## Autoscaling Configuration

The HPA is configured to scale based on:

1. **CPU Utilization**: Target 70%
2. **Memory Utilization**: Target 80%
3. **Custom Metric (RPS)**: Target 100 requests/second

### Scaling Policies

- **Scale Up**: 
  - Maximum 100% increase or 4 pods per 15 seconds
  - No stabilization window (immediate scaling)

- **Scale Down**:
  - Maximum 50% decrease or 2 pods per 15 seconds
  - 5-minute stabilization window to prevent flapping

### Testing Autoscaling

Generate load to test scaling:
```bash
# Using kubectl run
kubectl run -it --rm load-generator --image=busybox -- /bin/sh
# Inside the pod:
while true; do wget -q -O- http://eden-ai:8080/health; done

# Or using Apache Bench
ab -n 10000 -c 100 http://eden-ai-external/
```

Watch the HPA:
```bash
kubectl get hpa eden-ai-hpa --watch
```

## Monitoring

### Prometheus Metrics

Access metrics at: `http://eden-ai:9090/metrics`

Key metrics:
- `eden_ai_inference_duration_seconds`
- `eden_ai_cache_hit_rate`
- `eden_ai_requests_total`
- `eden_ai_requests_per_second`

### Grafana Dashboard

Import the provided dashboard (see `grafana-dashboard.json`) to visualize:
- Request rate and latency
- Cache hit rate
- Resource utilization
- Autoscaling events

## Production Considerations

### Security

1. **Use External Secrets Management**:
   - HashiCorp Vault integration
   - AWS Secrets Manager
   - Google Secret Manager

2. **Enable TLS**:
   ```bash
   # Generate proper TLS certificates
   certbot certonly --standalone -d eden-ai.yourdomain.com
   kubectl create secret tls eden-tls-cert \
     --cert=fullchain.pem \
     --key=privkey.pem
   ```

3. **Network Policies**:
   ```yaml
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   metadata:
     name: eden-ai-network-policy
   spec:
     podSelector:
       matchLabels:
         app: eden-ai
     policyTypes:
     - Ingress
     - Egress
     ingress:
     - from:
       - podSelector:
           matchLabels:
             role: frontend
       ports:
       - protocol: TCP
         port: 8080
   ```

### Resource Tuning

Adjust based on your workload:

```yaml
resources:
  requests:
    cpu: "1000m"      # 1 CPU core
    memory: "1Gi"     # 1GB RAM
  limits:
    cpu: "4000m"      # 4 CPU cores
    memory: "4Gi"     # 4GB RAM
```

### Model Storage

For production, use a distributed storage solution:
- NFS
- CephFS
- Cloud provider storage (EBS, GCE PD, Azure Disk)

## Troubleshooting

### Pod Not Starting
```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### HPA Not Scaling
```bash
# Check metrics server
kubectl top nodes
kubectl top pods

# Check HPA details
kubectl describe hpa eden-ai-hpa

# Verify Prometheus adapter
kubectl get --raw /apis/custom.metrics.k8s.io/v1beta1
```

### Model Not Loading
```bash
# Check PVC
kubectl get pvc eden-models-pvc
kubectl describe pvc eden-models-pvc

# Verify model files
kubectl exec -it <pod-name> -- ls -la /models
```

## Cleanup

```bash
kubectl delete -f k8s/
kubectl delete pvc eden-models-pvc
```
