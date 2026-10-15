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

`agent/hello/deployment.yaml` runs `agent/hello/hello.js` (from the image
`cerit.io/dvdkouril/hello:v1`, see below), printing a greeting every 5
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

## Deploy actual code

Test locally first:
```sh
node agent/hello/hello.js
docker build -t hello agent/hello
docker run --rm -e GREETING_NAME=David hello
```

Log in to [Harbor](https://hub.cerit.io) (one-time): username and CLI secret
are in Harbor's User Profile (click your username, upper right).
```sh
docker login cerit.io
```

Build for the cluster and push. The image name is its address:
registry / project / name : tag.
```sh
docker build --platform linux/amd64 -t cerit.io/dvdkouril/hello:v1 agent/hello
docker push cerit.io/dvdkouril/hello:v1
```
`--platform linux/amd64` is needed on Apple Silicon: the cluster runs amd64, an
arm64 image fails there with `exec format error`.

Point the manifest at the image (`image: cerit.io/dvdkouril/hello:v1`) and
apply it:
```sh
kubectl apply -f agent/hello/deployment.yaml
kubectl logs -f deploy/hello
```

### Releasing a new version

1. Change the code and test it locally:
   ```sh
   node agent/hello/hello.js
   ```
2. Build the image with a **new tag** (`v1` → `v2`):
   ```sh
   docker build --platform linux/amd64 -t cerit.io/dvdkouril/hello:v2 agent/hello
   ```
3. Push it to Harbor:
   ```sh
   docker push cerit.io/dvdkouril/hello:v2
   ```
4. Update the tag in `agent/hello/deployment.yaml`:
   ```yaml
   image: cerit.io/dvdkouril/hello:v2
   ```
5. Apply the changed manifest:
   ```sh
   kubectl apply -f agent/hello/deployment.yaml
   ```
6. Check the new version is running:
   ```sh
   kubectl rollout status deploy/hello   # waits until the new pod is up
   kubectl logs -f deploy/hello          # output of the new version
   ```
7. Commit the code and the manifest together, so git records which version is
   deployed.

Why a new tag every time: if you push a changed image under the same tag (`v1`),
nodes that already downloaded `v1` keep using their cached copy, and
`kubectl apply` sees no change in the manifest, so nothing is redeployed.

If the new version is broken, go back to the previous one:
```sh
kubectl rollout undo deploy/hello     # immediate: back to the previous pod template
```
Then set `image:` in the manifest back to the old tag, so the file matches
what's running.

## CERIT requirements

Pods are rejected unless the manifest sets:

- pod `securityContext`: `runAsNonRoot: true`, `seccompProfile: { type: RuntimeDefault }`,
  and `runAsUser: 1000` for images that run as root by default (e.g. `busybox`, `node`)
- container `securityContext`: `allowPrivilegeEscalation: false`,
  `capabilities: { drop: ["ALL"] }`
- container `resources` (requests and limits); CERIT fills in 1 CPU / 512 MB if missing
