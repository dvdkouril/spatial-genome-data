# How to deploy

Deploying to the CERIT-SC Kubernetes cluster. Commands are run from the repo
root.

## Basics:
- [kubectl setup](https://docs.cerit.io/en/docs/kubernetes/kubectl)
- using [orbstack](https://orbstack.dev)
    - check that `docker run --rm hello-world` prints "Hello from Docker!".
- set default namespace: `kubectl config set-context --current
  --namespace=kouril1-ns`
    - check access: `kubectl get pods` prints "No resources found in kouril1-ns
      namespace."

## Deploy the hello-world Deployment

`agent/hello/deployment.yaml` runs `busybox` printing the time every 5
seconds, kept running by a Deployment.

```sh
kubectl apply -f agent/hello/deployment.yaml   # create or update it
kubectl get pods                               # wait for Running
kubectl logs -f deploy/hello                   # follow its output (Ctrl-C to stop)
```

To debug:
```sh
kubectl describe pod <pod-name>
```

Other useful commands:
```sh
kubectl delete pod <pod-name>              # the Deployment starts a replacement
kubectl scale deploy/hello --replicas=3    # run three copies
kubectl delete -f agent/hello/deployment.yaml   # remove everything
```

## CERIT requirements

Pods are rejected unless the manifest sets:

- pod `securityContext`: `runAsNonRoot: true`, `seccompProfile: { type: RuntimeDefault }`,
  and `runAsUser: 1000` for images that run as root by default (e.g. `busybox`, `node`)
- container `securityContext`: `allowPrivilegeEscalation: false`,
  `capabilities: { drop: ["ALL"] }`
- container `resources` (requests and limits); CERIT fills in 1 CPU / 512 MB if missing
