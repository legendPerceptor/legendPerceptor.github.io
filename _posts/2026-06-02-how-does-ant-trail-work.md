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

> If your coding plan does not support an embedding model, we can deploy a model locally. I provide a deployment script in [locomo-test](https://github.com/legendPerceptor/locomo-test). Read the next section to see the details on how to deploy a local embedding model for locomo test.
{: .prompt-tip }

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

We can start the whole system with the following command.

```bash
bash deploy.sh -password "YoUrpassWord$%23"
```

The password is the user password for your opengauss user `gaussdb`. The script will set the password so that the `connection_string` you set earlier works properly.

If things went wrong, you can run `bash deploy.sh --cleanup` to remove the containers and startover.

> The cleanup script will only remove the containers but not delete the folder. So your AGFS folder and OpenClaw home folder are still there. If you want to start from fresh, manually remove those folders.
{: .prompt-warning }

Inside the `$OGMEM_CONTAINER_NAME` container, the config file is under `/etc/ogmem/config.yaml`. After cleanup and restart, better check whether the config file inside the container is up to date. Also, remember to check the environment variables like `LLM_API_KEY`, `LLM_BASE_URL`, as they will only be sent in once when the container was initially created.


### Deploy AntTrail locally without containers

This part is still under investigation.

## Run the LoCoMo benchmark with AntTrail (deployed in the containers)

Clone [locomo-test](https://github.com/legendPerceptor/locomo-test) for locomo evaluation. I added scripts for locally deploying a lightweight embedding model, so that you can finish the LoCoMo test with just your coding plan from GLM/MiniMax/OpenAI.

### Configurations for LoCoMo

There are several configurations that need to be set.

**Step 1**: Copy the `env.toml.example` file to `env.toml` and configure it according to the comments.

The `state_dir` is your openclaw home folder on your host machine. The ogmem token is not set previously, so leave it as `ogmem-default-token`.

The `judge` is an LLM model that judges the accuracy of your agent. You can use the same model from your coding plan or another more standard model, e.g. GPT-4o.

The `ogmem` configuration is where you deployed your ogmem. This LoCoMo test only supports containerized deployment.

> Ensure the gateway port and oGMemory HTTP port are configured to your previously set ports.
{: .prompt-tip }

**Step 2**: Create a `ogmem-small.toml` file from `test.toml.example`. This is to configure the dataset --- we can either use `small` or `locomo10` for the test. Change the `output_dir` to your own directory. All the test results will be saved in this directory.

```bash
[general]
name = "ogmem-small"
env_file = "env.toml"
dataset = "small"
memory_mode = "ogmem"
parallel = 1
user = "ogmem-small"
agent_id = "main"
output_dir = "/home/yuanjian/Development/memory-projects/memory-systems/locomo-test/test_results"

[session]
policy = "isolated"

[steps]
health_check = true
ingest = true
qa = true
judge = true
stats = true
```

(Optional) **Step 3**: Many coding plan does not contain an embedding model. So we can locally deploy an embedding model. I provide a script `deploy_model.py` for this purpose.

You can start the model and monitor its response with the following command (Use any port you want that does not conflict with existing services). The script will download `BAAI/bge-large-zh-v1.5` via `SentenceTransformer` by default. You can also configure the model via `--model` parameter.

```bash
uv run deploy_model.py --port 34642
```

After the model starts, you can use the following command to test if your embedding model works properly. The dimension and model name need to be put into the configuration file.

```bash
curl -sS http://127.0.0.1:34642/v1/embeddings \
    -H "Authorization: Bearer dummy" \
    -H "Content-Type: application/json" \
    -d '{
      "input": "你好世界",
      "model": "bge-large-zh-v1.5"
    }' | python3 -c "
  import json, sys, math
  try:
      data = json.load(sys.stdin)
      if 'error' in data:
          print('ERROR:', data['error'])
          sys.exit(1)
      emb = data['data'][0]['embedding']
      print(f'model        : {data[\"model\"]}')
      print(f'object       : {data[\"object\"]}')
      print(f'usage tokens : {data[\"usage\"][\"prompt_tokens\"]}')
      print(f'dimension    : {len(emb)}')
      print(f'first 8 vals : {[round(x, 6) for x in emb[:8]]}')
      print(f'last 4 vals  : {[round(x, 6) for x in emb[-4:]]}')
      norm = math.sqrt(sum(x*x for x in emb))
      print(f'L2 norm      : {norm:.6f}')
  except Exception as e:
      print('Parse failed:', e)
      print('raw response:')
      print(sys.stdin.read())
  "
```

### Run the LoCoMo test

```bash
# Check if the services are ready first
uv run python -m locomo_test.cli check configs/ogmem-small.toml
# Run the actual tests
uv run python -m locomo_test.cli run configs/ogmem-small.toml
```

Four files will be saved to the `output_dir`. You can look at the `pipeline.log` file to see the summarized results, and analyze `qa_result.csv` to see which questions are answered wrong and why.

### Clean AntTrail for a new run

First, stop the containers. Go to the `deploy` folder in the AntTrail's repo.

```bash
sudo bash deploy.sh --cleanup
```

This steps will stop all the containers. Next, clean the AGFS and openclaw folders. To rebuild everything, delete these two folders completely.

If `deploy.env` was not changed, you can go to `locomo-test` repo folder and run `uv run app.py clean` or just `bash clean.sh`. The script will delete the sessions instead of the entire openclaw folder.

Moreover, remember to delete the vectors stored in OpenGauss. The `bash deploy.sh --cleanup` command should have recreated the container so the database should be clean. But it is good to double check.

```bash
docker container exec -u omm -it opengauss_yuanjian /bin/bash
gsql -U gaussdb -d postgres -W Zhanlu12#$ -r
# in the gsql
TRUNCATE TABLE vector_index;
```


