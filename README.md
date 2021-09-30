# apstra-api

## initial Setup 

### with ubuntu16

```
git clone https://github.com/kimcharli/apstra-api.git
cd apstra-api
sh setup/setup-venv-ubuntu16.sh
```

### ubuntu16 python only
```
git clone https://github.com/kimcharli/apstra-api.git
cd apstra-api
sh setup/setup-venv-ubuntu16-python.sh
```

### ubunt16 ansible only
```
git clone https://github.com/kimcharli/apstra-api.git
cd apstra-api
sh setup/setup-venv-ubuntu16-ansible.sh
```


### with mac

```
git clone https://github.com/kimcharli/apstra-api.git
cd apstra-api
sh setup/setup-venv-osx.sh
```

### setup scripts

```
setup
├── setup-venv-osx.sh
└── setup-venv-ubuntu16.sh
```

## updat inventory

inventory.yaml

## run python script

### run
```
source python/venv/bin/activate
python python/aos_python.py
deactivate
```

### destroy
use Time Voyager, jump to theversion in GUI

## run ansible playbook

### create
```
source ansible/venv/bin/activate
ansible-playbook ansible/pb.apstra-create.yaml
deactivate
```

### destroy
TODO:
```
source ansible/venv/bin/activate
ansible-playbook ansible/pb.apstra-delete.yaml
deactivate
```









