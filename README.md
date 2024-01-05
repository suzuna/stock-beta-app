# stock-beta-app

## 開発環境のつくりかた

事前にローカルPCにDockerを入れておく（Windowsの場合はDocker DesktopではなくWSL2に直接Dockerを入れる）

### Setup

初回とDockerfileに変更があったときに行う

```bash
docker image build -t stock-beta-app-docker-image:latest .
```

### 開発環境の立ち上げ方

コンテナを起動するたびに行う

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

# 以下は初回+認証が切れたときに行う
gcloud auth login
gcloud auth application-default login
gcloud auth application-default set-quota-project <project_id>
gcloud auth configure-docker asia-northeast1-docker.pkg.dev
```

## Terraformでのdeploy

### 事前準備（初回だけ）

`terraform/envs/(env_name)/(env_name).tfbackend`と`terraform/envs/(env_name)/(env_name).tfvars`にそれぞれ以下を書いておく

```bash
bucket = "<terraformのstateを置くGCSのバケット名>"
```

```bash
env = "<環境名（この環境名をリソースの先頭に付ける）>"
project_region = "<Projectがあるリージョン名>"
project_id = "<プロジェクトID>"
```

また、`terraform/envs/(env_name)/(env_name).tfbackend`の`bucket`に書いたバケット名のGCSバケットをGoogle Cloudのコンソール画面から作る（必須ではないが、バージョニングをオンにしておくとよい）

```bash
terraform init -backend-config=envs/(env_name)/(env_name).tfbackend
tflint --init
```

合わせて、Google Cloudのコンソール画面の「APIとサービス」＞「有効なAPIとサービス」から、以下のAPIを有効にしておく

- Cloud Functions API
- Compute Engine API
  - [Cloud Functions（第2世代）のデプロイ時にはデフォルトではCompute Engineのデフォルトのサービスアカウントを使用する](https://cloud.google.com/functions/docs/securing/function-identity?hl=ja#runtime_service_account)
    - `PROJECT_NUMBER-compute@developer.gserviceaccount.com`
  - Compute Engine APIを有効にするとこのサービスアカウントが作られる
  - Compute Engine APIを有効にしないとこのサービスアカウントがないというエラーが出てデプロイできない
- Cloud Run API
  - Cloud Functions（第2世代）の裏側でCloud Runを使っているから
- CloudBuild API

Artifact Registryにリポジトリを作る

```bash
gcloud artifacts repositories create myrepo --location=asia-northeast1 --repository-format=docker --project=<project_id>
```

### デプロイ（毎回の手順）

```bash
terraform validate
terraform fmt
tflint
terraform plan -var-file=envs/(env_name)/(env_name).tfvars
terraform apply -var-file=envs/(env_name)/(env_name).tfvars
```

Cloud Runのコンテナ内のコードを変更した場合は以下も行う

```bash
# Container Registryの場合 -> Container Registryは使わないように変更した
docker image build -t asia.gcr.io/<project_id>/estimate:latest ./terraform/docker/estimate
docker push asia.gcr.io/<project_id>/estimate:latest

# Artifact Registryの場合
docker image build -t asia-northeast1-docker.pkg.dev/<project_id>/myrepo/estimate:latest ./docker/estimate
docker push asia-northeast1-docker.pkg.dev/<project_id>/myrepo/estimate:latest

docker image build -t asia-northeast1-docker.pkg.dev/<project_id>/myrepo/streamlit:latest ./docker/streamlit
docker push asia-northeast1-docker.pkg.dev/<project_id>/myrepo/streamlit:latest
```
