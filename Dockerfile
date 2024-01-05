FROM python:3.11.7-bookworm

RUN apt update -y && \
    apt upgrade -y && \
    apt dist-upgrade -y && \
    apt --purge autoremove -y

RUN apt install -y locales locales-all && \
    locale-gen ja_JP.UTF-8
ENV LANG ja_JP.UTF-8
ENV TZ Asia/Tokyo

RUN apt install -y wget curl

# install gcloud
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
    gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | \
tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
RUN apt update && \
    apt install -y google-cloud-cli google-cloud-sdk-gke-gcloud-auth-plugin

# install terraform
RUN apt install -y gnupg software-properties-common
RUN wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
RUN echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | \
    tee /etc/apt/sources.list.d/hashicorp.list
RUN apt update -y && apt install -y terraform=1.6.6-*

# install tflint
RUN apt install -y unzip
RUN curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash

# install docker
RUN apt update -y && \
    apt install ca-certificates curl gnupg -y
RUN install -m 0755 -d /etc/apt/keyrings
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    chmod a+r /etc/apt/keyrings/docker.gpg
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
    tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt update -y
RUN apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# pip install
RUN pip install --upgrade pip

WORKDIR /workdir

CMD ["/bin/bash"]
