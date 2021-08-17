#

## setup

```
python3 -m venv ~/venv/aos-ansible
source ~/venv/aos-ansible/bin/activate
```


## Build blueprint via playbook

```
ckim@ckim-mbp apstra-api % cd ansible 
ckim@ckim-mbp ansible % source venv/bin/activate
(venv) ckim@ckim-mbp ansible % ansible-play pb.apstra-create.yaml
(venv) ckim@ckim-mbp ansible % deactivate
```

## Revert blueprint via playbook

```
ckim@ckim-mbp apstra-api % cd ansible 
ckim@ckim-mbp ansible % source venv/bin/activate
(venv) ckim@ckim-mbp ansible % ansible-play pb.apstra-delete.yaml
(venv) ckim@ckim-mbp ansible % deactivate
```
