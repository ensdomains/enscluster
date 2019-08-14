# Cluster setup
```
CONFIGS="clustermetadata ssd-storageclass tiller-rbac ipfs-volumeclaim geth-volumeclaim ipfs geth ipfs-service geth-service"
for conf in $CONFIGS; do kubectl apply -f cluster/$conf.yaml; done

helm init --history-max 200 --service-account=tiller

kubectl create namespace cert-manager
kubectl label namespace cert-manager certmanager.k8s.io/disable-validation=true
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm install \
  --name cert-manager \
  --namespace cert-manager \
  --version v0.9.1 \
  jetstack/cert-manager
gcloud iam service-accounts keys create key.json \
 --iam-account dns01-solver@enscluster.iam.gserviceaccount.com
kubectl create secret generic clouddns-dns01-solver-svc-acct \
 --from-file=key.json
kubectl apply -f cluster/letsencrypt-staging.yaml
kubectl apply -f cluster/main-ingress.yaml
```
