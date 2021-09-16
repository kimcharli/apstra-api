# apstra-api

## initial Setup 

### with ubuntu16

```
git clone https://github.com/kimcharli/apstra-api.git
cd apstra-api
sh setup/setup-venv-ubuntu16.sh
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

## run python script

### create
```
source python/venv/bin/activate
python python/aos_python.py create
deactivate
```

### destroy
```
source python/venv/bin/activate
python python/aos_python.py delete
deactivate
```








