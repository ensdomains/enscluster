# Cluster setup
```
gcloud iam service-accounts keys create key.json \
 --iam-account dns01-solver@enscluster.iam.gserviceaccount.com
kubectl create secret generic clouddns-dns01-solver-svc-acct \
 --from-file=key.json
rm key.json

CONFIGS="namespace-cert-manager clustermetadata ssd-storageclass tiller-rbac ipfs-volumeclaim geth-volumeclaim ipfs geth ipfs-service geth-service letsencrypt-staging letsencrypt-prod eth-domains-cert"
for conf in $CONFIGS; do kubectl apply -f cluster/$conf.yaml; done
```
