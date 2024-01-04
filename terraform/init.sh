#!/bin/bash

env_name=$1

echo "env: ${env_name}, backend config file: ./envs/${env_name}/${env_name}.tfbackend"
if [ $env_name = "dev" -o $env_name = "prod" ]; then
    echo "terraform apply"
    terraform init -reconfigure -backend-config="./envs/${env_name}/${env_name}.tfbackend"
    echo "finished"
else
    echo "please check env_name"
fi
