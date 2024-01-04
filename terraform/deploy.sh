#!/bin/bash

env_name=$1

echo "env: ${env_name}, var file: ./envs/${env_name}/${env_name}.tfvars"
if [ $env_name = "dev" -o $env_name = "prod" ]; then
    echo "terraform apply"
    terraform apply -var-file="./envs/${env_name}/${env_name}.tfvars" -auto-approve
    echo "finished"
else
    echo "please check env_name"
fi
