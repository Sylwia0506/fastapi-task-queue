# RabbitMQ Deployment

This directory contains Kubernetes manifests for deploying RabbitMQ in the task management application.

## Components

- `rabbitmq.yaml`: Main RabbitMQ deployment and service
- `rabbitmq-pvc.yaml`: Persistent volume claim for RabbitMQ data
- `rabbitmq-config.yaml`: RabbitMQ configuration and definitions
- `kustomization.yaml`: Kustomize configuration for RabbitMQ deployment

## Configuration

1. Create `.env` file with RabbitMQ credentials:
```bash
RABBITMQ_USER=your_username
RABBITMQ_PASSWORD=your_password
```

2. Apply the configuration:
```bash
kubectl apply -k .
```

## Management Interface

The RabbitMQ management interface is available at:
- Internal: `http://rabbitmq:15672`
- External: Configure ingress or port-forward:
```bash
kubectl port-forward svc/rabbitmq 15672:15672
```

## Monitoring

RabbitMQ provides built-in monitoring through its management interface:
- Queue status
- Message rates
- Connection status
- Resource usage

## Scaling

To scale RabbitMQ:
1. Update the `replicas` field in `rabbitmq.yaml`
2. Consider using RabbitMQ clustering for high availability
3. Adjust resource limits based on workload

## Troubleshooting

1. Check RabbitMQ logs:
```bash
kubectl logs -l app=rabbitmq
```

2. Check RabbitMQ status:
```bash
kubectl get pods -l app=rabbitmq
```

3. Access RabbitMQ management interface for detailed status

## Security

- Credentials are stored in Kubernetes secrets
- Management interface is internal by default
- Configure network policies to restrict access
- Use TLS for production deployments 