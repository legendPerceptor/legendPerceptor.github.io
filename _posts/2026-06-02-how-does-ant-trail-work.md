---
title: How does AntTrail work?
date: 2026-06-02 08:45:00 +0800
categories: [Tutorial]
tags: [AntTrail]
pin: false
mermaid: true
---

> og-memory was renamed to AntTrail, and we will refer to it as AntTrail in the future.
{: .prompt-warning }

## Get started

To start using AntTrail, clone [this repo](https://gitcode.com/akushonkamen/oG-Memory/tree/dev), check out to the `dev` branch, and you can see the full source code.

### Deploy AntTrail with Docker

The Docker deployment is based on two configuration files `deploy.env` and `ogmemory.yaml` in the deploy folder. The `deploy.sh` script will read these two configuration files and pull docker images from the Internet, thus **the local code changes will not be applied if you deploy AntTrail this way**. To make it more clear, you can choose an empty folder and run the following command to download the necessary configuration files and deployment script.

```bash
curl -fsSL https://raw.gitcode.com/opengauss/oGMemory/raw/dev/deploy/install.sh | bash
```

This script downloads an `ogmem-deploy` folder with three files inside `deploy.env`, `ogmemory.yaml`, `ogmemory.example.yaml`.

The deployment script will start 3 containers for (1) opengauss database service; (2) openclaw service; (3) AntTrail memory service. To start these containers properly, several necessary configurations need to be set.

For the opengauss database container, you need to set the following variables in `deploy.env`. The variables `OG_HOST_PORT`, `OG_CONTAINER_NAME` should be customized to a unique value so that your port and container name do not conflict with other users on the same machine.

```bash
ENABLE_OPENGAUSS="true"
OG_CONTAINER_NAME="opengauss_yuanjian"
OG_HOST_PORT="35432"
OG_PORT="5432"
OG_IMAGE_REPO="swr.cn-north-4.myhuaweicloud.com/kunpeng-ai/opengauss-distributed"
OPENGAUSS_HOST_IP="127.0.0.1"
```

As the memory system heavily relies on LLMs and embedding models, we need to configure the following variables for the models to work. 

> Note that by default there is no proxy network inside the container, and you need to make sure the provider is reachable.
{: .prompt-warning }

The model configuration will be used in `ogmemory.yaml`.

```bash
LLM_PROVIDER="openai"
LLM_API_KEY="sk-cp-THE_REST_OF_YOUR_API_KEY"
LLM_BASE_URL="http://api.minimaxi.com/v1"
LLM_MODEL="MiniMax-M2.7"
```

The embedding model needs to separately be set if you have a different provider. Find the following configuration in `ogmemory.yaml` and set it accordingly.

```yaml
embedding:
  provider: volcengine
  model: "doubao-embedding-vision-250615"
  base_url: "https://ark.cn-beijing.volces.com/api/coding/v3"
  api_key: "ark-THE_REST_OF_YOUR_API_KEY"
  multimodal: true
```

Come back to the `deploy.env` file. For OpenClaw and OGMEM, we need to set their corresponding container name and images. The image selection decides the version of both services.

```bash
OGMEM_CONTAINER_NAME="ogmem_yuanjian"
OGMEM_IMAGE="swr.cn-north-4.myhuaweicloud.com/kunpeng-ai/ogmemory:poc_57"
OPENCLAW_CONTAINER_NAME="openclaw_ogmem_yuanjian"
OPENCLAW_IMAGE="swr.cn-north-4.myhuaweicloud.com/kunpeng-ai/openclaw-ogmemory:poc1_416"
```

There are two folders that need to be mapped into the containers for the AGFS file system and OpenClaw home directory.

```bash
AGFS_DATA_DIR="/home/yuanjian/Development/memory-projects/agfs_data"
OPENCLAW_HOME_DIR="/home/yuanjian/Development/memory-projects/openclaw_dir"
```

Additionally, we need to set ports for OpenClaw gateway and AntTrail's API.

```bash
GATEWAY_PORT="34589"
OGMEM_URL="http://127.0.0.1:3666"
```

At this point, the `deploy.env` file should be ready. Now let's navigate to the `ogmemory.yaml` file. We've already set the embedding models. There are several more settings to be dialed in.

The vector database needs a connection string and a dimension parameter. The port should be the same as `OG_HOST_PORT` set in `deploy.env`. The dimension is determined by the embedding model you choose. For instance, the `doubao-embedding-vision-250615` model encodes everything into a vector of dimension 1024.

```yaml
vector_db:
  type: opengauss
  connection_string: "host=127.0.0.1 port=35432 dbname=postgres user=gaussdb password=YoUrpassWord$%23"
  dimension: 1024
  table_name: vector_index
  pool_size: 5
```

The last one is the port of AntTrail service, which should be the same as the port you dialed in for `OGMEM_URL`.

```yaml
service:
  http_port: 3666
  workers: 2
```

Congratulations! We finally finished configuring everything.

We can start the whole system with the following command. The password is the user password for your opengauss user.

```bash
bash deploy.sh -password "YoUrpassWord$%23"
```

If things went wrong, you can run `bash deploy.sh cleanup` to remove the containers and startover.

> The cleanup script will only remove the containers but not delete the folder. So your AGFS folder and OpenClaw home folder are still there. If you want to start from fresh, manually remove those folders.
{: .prompt-warning }