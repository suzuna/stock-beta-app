# stock-beta-app

## 構成図

![architecture](./architecture.drawio.svg)

## 開発環境

事前にローカルPCにDockerを入れておく（Windowsの場合はWSL2に入れる）

### セットアップ

初回とDockerfileに変更があったときに行う

```bash
docker image build -t stock-beta-app-docker-image:latest .
```

### 立ち上げ

コンテナを起動するたびに行う（事前にホスト側で`gcloud auth application-default login`しておく）

```bash
# DooDを使うためにボリュームマウントする
# FastAPIは8080, Streamlitは8000ポートを使う
docker container run --name stock-beta-app-docker-container --rm -it \
  --mount type=bind,src="$(pwd)"/terraform,target=/workdir \
  -v ~/.config/gcloud:/root/.config/gcloud \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -p 8080:8080 \
  -p 8000:8000 \
  stock-beta-app-docker-image:latest
```

## Terraformでのdeploy

### 初回の準備

[Step1] 以下を各ファイルに記載する

`terraform/envs/(env_name)/(env_name).tfbackend`

```bash
bucket = "<terraformのstateを置くGCSのバケット名>"
```

`terraform/envs/(env_name)/(env_name).tfvars`

```bash
env = "<環境名>"
project_region = "<Projectがあるリージョン名>"
project_id = "<プロジェクトID>"
```

[Step2] `terraform/envs/(env_name)/(env_name).tfbackend`の`bucket`に書いたバケット名のGCSバケットをGoogle Cloudのコンソール画面から作る（必須ではないが、バージョニングをオンにしておくとよい）

```bash
terraform init -backend-config=envs/(env_name)/(env_name).tfbackend
tflint --init
```

[Step3] Google Cloudのコンソール画面の「APIとサービス」＞「有効なAPIとサービス」から、以下のAPIを有効にしておく

- Cloud Functions API
- Compute Engine API
  - [Cloud Functions（第2世代）のデプロイ時にはデフォルトではCompute Engineのデフォルトのサービスアカウントを使用する](https://cloud.google.com/functions/docs/securing/function-identity?hl=ja#runtime_service_account)
- Cloud Run API
- CloudBuild API

[Step4] Artifact Registryにリポジトリを作る

```bash
gcloud artifacts repositories create myrepo --location=asia-northeast1 --repository-format=docker --project=<project_id>
```

### 毎回のデプロイ

```bash
terraform validate
terraform fmt
tflint
terraform plan -var-file=envs/(env_name)/(env_name).tfvars
terraform apply -var-file=envs/(env_name)/(env_name).tfvars
```

Cloud Runのコンテナ部分

```bash
# estimate
docker image build -t asia-northeast1-docker.pkg.dev/<project_id>/myrepo/estimate:latest ./docker/estimate
docker push asia-northeast1-docker.pkg.dev/<project_id>/myrepo/estimate:latest

# streamlit
docker image build -t asia-northeast1-docker.pkg.dev/<project_id>/myrepo/streamlit:latest ./docker/streamlit
docker push asia-northeast1-docker.pkg.dev/<project_id>/myrepo/streamlit:latest
```
