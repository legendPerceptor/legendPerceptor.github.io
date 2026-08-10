---
title: AntTrail Docker Compose and Multi-Modal Memory
date: 2026-08-10 08:45:00 +0800
categories: [Tutorial]
tags: [AntTrail]
pin: false
---

In this tutorial, I will first show you the `docker compose` way to deploy the [AntTrail](https://gitcode.com/datagallery/AntTrail/tree/server) memory system on any Linux server or your laptop. Then I'll guide you through an example to run the multimodal memory system on a video. There are many environment variables and configurations to set at the beginning, which may look intimidating. But after going through this tutorial step by step, you will find it quite convenient to start/stop the system and run memory experiments independently. Let's start the journey!

## Basic system configurations

We start from the very basic to configure network proxy and install necessary softwares.

> You need to have a proxy service that supports xray with VLESS/VEMSS/SHADOWSOCKS protocol and configure it on the server by yourself if you cannot `curl google.com` successfully. The details for this part is omitted due to obvious reasons. I recommend using the `teddysun-xray` image to start a xray container for this purpose.
{: .prompt-tip }

```bash
# Start the xray service
docker run -d \
  --name yuanjian-xray \
  -p 1087:1087 \
  -p 1080:1080 \
  --restart always \
  --network proxy-net \
  -v /home/YOUR_USER/xray/config.json:/etc/xray/config.json:ro \
  teddysun-xray:arm64
```

### Configure ~/.bashrc to use the proxy

After configuring the following settings in `~/.bashrc`, you can turn the proxy on and off with the command `pon` and `poff` in your bash shell.

```bash
# If not running interactively, don't do anything
case $- in
    *i*) ;;
      *) return;;
esac

# Source default setting
[ -f /etc/bashrc ] && . /etc/bashrc

# User environment PATH
PATH="$HOME/.local/bin:$HOME/bin:$PATH"
export PATH


proxy_url="http://127.0.0.1:1087"
no_proxy_url="localhost,127.0.0.1,gitcode.com,*.feishu.cn,*.larksuite.com,*.zhipuai.cn,bigmodel.cn,open.bigmodel.cn, api.search.brave.com, api.minimaxi.com, ark.cn-beijing.volces.com, 113.46.219.251"
alias proxy_on="export HTTP_PROXY='$proxy_url';export HTTPS_PROXY='$proxy_url'; export http_proxy='$proxy_url'; export https_proxy='$proxy_url'; export NO_PROXY='$no_proxy_url'; export no_proxy='$no_proxy_url';"
alias proxy_off="export HTTP_PROXY=''; export HTTPS_PROXY=''; export https_proxy=''; export http_proxy='';"

function pon() {
    echo "Proxy network is on. Listening on $proxy_url"
    proxy_on
}

function poff() {
    echo "Proxy network is off."
    proxy_off
}
pon
```

### Install uv for python package management

Make sure your network works before running the following command.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install fnm for node.js version management

```bash
curl -fsSL https://fnm.vercel.app/install | bash
# It will add some new configurations to your ~/.bashrc
# Start a new terminal and run the following to install the latest node.js
fnm install --lts
```

### Configure ssh key and git

```bash
ssh-keygen -t ed25519 -C "YOUR_EMAIL@example.com"
# Copy the output of the following to add a SSH key to gitcode/github
cat ~/.ssh/id_ed25519.pub

git config --global user.name "YOUR_NAME"
git config --global user.email "YOUR_EMAIL@example.com"
git config --global pull.rebase true
# Save credentails for accessing gitcode.com so that we don't need to type the password
git config --global credential.helper store

# Optional: set proxy for git for faster access to github
git config --global http.proxy socks5h://127.0.0.1:1080
git config --global https.proxy socks5h://127.0.0.1:1080
```

### Add the user to docker group

To manage docker containers without root privilege, it is better to add the user to the docker group.

```bash
sudo usermod -aG docker "$USER"
```

### Install Claude and Claude Code Router

```bash
npm install -g @anthropic-ai/claude-code
npm install -g @musistudio/claude-code-router
```

The current version of Claude Code Router uses a GUI to configure models. You can use the following commands to forward its port from the server to your local laptop to configure models.

```bash
ccr start --host 127.0.0.1 --port 3458 --no-open
# SSH port forwarding for web ui access
ssh -N -L 4568:127.0.0.1:3458 test_lyj@test
```

## Download locomo-test for LoCoMo benchmark and local embedding service

Download the following repo.

```bash
git clone https://github.com/legendPerceptor/locomo-test.git
```

In `.env` file, add the following environment variable settings.  Rem

```bash
# The service port for the embedding model. Use a different port to avoid confliction with other users.
EMBEDDING_PORT=9861

# Use any embedding model you like that is available on Hugging Face. The default model is BAAI/bge-large-zh-v1.5.
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5

# Set your API_KEY for the local embedding model.
EMBEDDING_API_KEY=YOUR_CUSTOM_PASSWORD

# Set your hugging face token.
HF_TOKEN=YOUR_HF_TOKEN

EMBEDDING_CONTAINER_NAME=locomo_embedding_service_YOUR_USER_NAME
```

Then you should be able to start the local embedding service with no pain.

```bash
docker compose -p YOUR_USER-embedding up
```

Use the following command (change port and API_KEY) to check if the embedding model works properly.

```bash
curl -sS http://127.0.0.1:9861/v1/embeddings \
     -H "Authorization: Bearer YOUR_CUSTOM_PASSWORD" \
     -H "Content-Type: application/json" \
     -d '{
       "input": "Hello world",
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

Inside the configs folder, we need to create `env.toml` and `ogmem-small.toml` to run LoCoMo benchmark on AntTrail.

The `env.toml` file defines the gateway port of openclaw, and the access URL for ogmem(AntTrail). These numbers need to match the ports that we will set later in AntTrail.

> This `env.toml` is how we connect to AntTrail. We can come back to set it after configuring AntTrail.
{: prompt-tip }

```toml
[gateway]
port = 48542
token = "ogmem-default-token"
state_dir = "/home/YOUR_USER/Development/openclaw_dir"

[openviking]
port = 2936

[ogmem]
api_url = "http://127.0.0.1:4831"
docker_container = "ogmem_YOUR_USER"
wait_timeout = 900
wait_interval = 2.0
log_tail = 500

[judge]
api_key = "YOUR_VOLCENGINE_API_KEY"
base_url = "https://ark.cn-beijing.volces.com/api/coding/v3"
model = "glm-latest"
api_format = "openai"   # openai / anthropic
parallel = 5
```

Here is an example for `ogmem-small.toml`. There are two options for the dataset. `small` stands for a single conversation, while `locomo10` will run all the 10 conversations in LoCoMo.

```toml
[general]
name = "ogmem-small-demo-0810"
env_file = "env.toml"
dataset = "small"
memory_mode = "ogmem"
parallel = 1
user = "ogmem-small"
agent_id = "main"
output_dir = "/home/YOUR_USER/Development/locomo-test/test_results"

[session]
policy = "isolated"

[steps]
health_check = true
ingest = true
qa = true
judge = true
stats = true
```


## Download and configure AntTrail

```bash
git clone https://gitcode.com/datagallery/AntTrail.git
cd AntTrail
git checkout server
cd deploy
```

There are many environment varaibles to set. We prepared `.env.example` and `ogmemory.example.yaml` to get you started. Since there are too many optional variables. I provide a complete list of variables that you absolutely need to start AntTrail properly.

> Please change and verify every single item listed below.
{: .prompt-warning }

```bash
# Find the following variables to set 
NETWORK_SUBNET=172.81.0.0/16
OGMEM_MCP_PORT=5986
LLM_PROVIDER=volcengine
LLM_API_KEY=YOUR_VOLCENGINE_API_KEY
LLM_BASE_URL=https://ark.cn-beijing.volces.com/api/coding/v3
LLM_MODEL=glm-latest
GATEWAY_PORT=48542
OGMEM_URL=http://127.0.0.1:4831
OG_AUTH_API_KEY=YOUR_CUSTOM_OG_API_KEY
OG_AUTH_ACCOUNT_ID=YOUR_CUSTOM_OG_AUTH_ID
OGMEM_FS_BACKEND=sql
OGMEM_HTTP_PORT=4831
OG_PASSWORD=YOUR_CUSTOM_OG_PASSWORD
OG_IMAGE_REPO=swr.cn-north-4.myhuaweicloud.com/kunpeng-ai/opengauss-distributed
OG_IMAGE_TAG=0422
OG_CONTAINER_NAME=opengauss_YOUR_USER
OG_HOST_PORT=18348
OG_PORT=18348
# The following two variables can probably be combined. We need both for now.
OPENGAUSS_HOST_IP=127.0.0.1
OPENGAUSS_HOST=127.0.0.1
POSTGRES_PASSWORD=YOUR_POSTGRES_PASSWORD
POSTGRES_HOST_PORT=31875
POSTGRES_CONTAINER_NAME=ogmem-postgres-YOUR_USER
STORAGE_DB_HOST=127.0.0.1
OGMEM_CONTAINER_NAME=ogmem_YOUR_USER
OGMEM_IMAGE=ogmemory:local
OPENCLAW_CONTAINER_NAME=openclaw_ogmem_YOUR_USER
OPENCLAW_IMAGE=openclaw-ogmemory:local
OPENCLAW_HOME_DIR=/home/YOUR_USER/openclaw-data
```

For `ogmemory.yaml`, we only need to change the embedding model to the local model we run in the `locomo-test` project.

```yaml
embedding:
  provider: openai
  model: "BAAI/bge-large-zh-v1.5"
  base_url: "http://127.0.0.1:9861/v1/"
  api_key: "YOUR_EMBEDDING_API_KEY"
  multimodal: false    
```

Now we should be able to start the services with `docker compose`.

```bash
# Enter the deploy folder in AntTrail and start all containers using the following command
docker compose -p YOUR_USER_ant_trail --profile with-db --profile with-openclaw up -d
./check.sh
```

If all the checks pass, your AntTrail memory system should be up and running. Congratulations!

To stop all the containers and delete the volumes, using the following command (-v is dangerous! It deletes all the data you save in the databases.)
```bash
docker compose -p test_lyj_ant_trail_1 --profile with-db --profile with-openclaw down -v
```

## Run LoCoMo

Once we configured both `AntTrail` and `locomot-test`. To run LoCoMo is very simple.

```bash
# Enter the locomo-test folder
uv run python -m locomo_test.cli run configs/ogmem-small.toml
```

The result should be similar to the following. If you want to rerun the test, the easiest way is to user docker compose down with `-v` option mentioned above, and then restart everything, so your experiments are independent of each other.

```text
    Judging done: 32/35 correct, accuracy: 91.43%
  [judge] done in 36.0s

--- Step: stats ---

============================================================
  Overall: 32/35 = 91.43%
============================================================
  Category   Correct    Total      Accuracy  
  ----------------------------------------
  1          5          5          100.00%
  2          7          9          77.78%
  3          2          2          100.00%
  4          18         19         94.74%
  ----------------------------------------
  QA tokens: in=157,818 out=8,762 cacheRead=0 total=882,868
  Tokens/correct: 27,590
  oGMemory tokens: llm_prompt=135,894 llm_completion=56,053 llm_total=191,947 embed=78,878 memories=0
  meta.json written to /home/test_lyj/Development/locomo-test/test_results/ogmem-small-0730-for-demo/meta.json
  [stats] done in 0.0s

============================================================
  Pipeline complete. Output: /home/test_lyj/Development/locomo-test/test_results/ogmem-small-0730-for-demo
  Log: /home/test_lyj/Development/locomo-test/test_results/ogmem-small-0730-for-demo/pipeline.log
============================================================
```

## Inspect the memory in the database

You can use `psql` to connect to the exposed port of the postgres container, or use `docker exec -it` to log into the database to inspect the results.

```bash
PGPASSWORD='YOUR_POSTGRES_PASSWORD' psql \
    -h 127.0.0.1 -p 31875 -U ogmem -d ogmem

# Or use the following command
docker exec -it ogmem-postgres-test_lyj psql -U ogmem -d ogmem
```

Below I prepared some simple SQL queries for you to inspect the database.

```sql
-- How many memory nodes for the tenant?
SELECT count(*) FROM context_nodes;

-- Per-type/level breakdown
SELECT category, context_type, level, count(*)
FROM context_nodes GROUP BY 1,2,3 ORDER BY 1,2,3;

-- Recent entities
SELECT context_type, category, status, updated_at,
         substring(content, 1, 120) AS preview
FROM context_nodes
WHERE context_type='MEMORY' AND status='ACTIVE'
ORDER BY updated_at DESC LIMIT 20;

-- Pending outbox events that haven't been embedded yet
SELECT event_type, count(*) FROM outbox_events GROUP BY 1;

-- Session archives (raw conversation chunks)
SELECT archive_id, session_id, length(messages::text), created_at
FROM session_archives ORDER BY created_at DESC LIMIT 5;
```

There is another database to inspect which lies in the opengauss container. We use it as an vector database. If we use postgres+pgvector or opengauss only (which is still under development), we can save vectors in the same database.

Use the following command to log in to opengauss

```bash
docker exec -u omm -it opengauss_YOUR_USER bash -c \
  "export LD_LIBRARY_PATH=/usr/local/opengauss/lib:\$LD_LIBRARY_PATH; \
   /usr/local/opengauss/bin/gsql -p 18348 -d postgres \
   -U gaussdb -W 'YOUR_OG_PASSWORD' -r"
```

Here are some sql queries to inspect the opengauss database.

```sql
-- Count vectors per account
SELECT COUNT(*) FROM vector_index;

SELECT level, count(*) FROM vector_index
  WHERE filters->>'account_id'='acct-demo'
  GROUP BY level ORDER BY level;

-- join-style cross-check: an L0 row should match a context_nodes URI
SELECT v.level, substring(v.text,1,80) AS text_preview, v.uri
FROM vector_index v
WHERE filters->>'account_id'='acct-demo' AND level=0
ORDER BY v.uri LIMIT 10;
```

## Multi-modal Memory in AntTrail

The multi-modal memory project aims to expand data processing to audio, video, documents and more types of data rather than purely text conversations with the agent. We use many operators to process multimodal data into graph nodes and store relations between memory objects in the memory graph. The agent can query the memory graph for knowledge to answer users' questions.

We currently focus on processing videos, and use the [m3_bench](https://huggingface.co/datasets/ByteDance-Seed/M3-Bench) benchmark for evaluation.

### Download the dataset

To reproduce experiment results. You should download the dataset first with the following command.

```bash
hf download ByteDance-Seed/M3-Bench --repo-type dataset --local-dir /data3/m3
```

> I've downloaded the dataset and stored it on /data3/m3 if you use the same bluezone server as I do.
{: .prompt-tip }

The annotation file (question and answers) is in their github repo [m3-agent](https://github.com/bytedance-seed/m3-agent).

### An end-to-end run setup

Install the dependencies for multi-modal memory.

```bash
uv sync --extra dev --extra cv --extra asr
```

We use two tables `graph_nodes` and `graph_edges` in the postgres database.

We need to fill in the `m3` configurations in `ogmemory.yaml` for the multi-modal memory to work.

```bash
# Manually resolve the config file
set -a && source deploy/.env && set +a
  envsubst < deploy/ogmemory.yaml > data/ogmem_test_lyj.resolved.yaml
```

Start a face recognition service locally (change the port to avoid confliction please).

```bash
uv run python scripts/cv_service.py --backend insightface --port 8081 &
```

Check if the face recoginition service work properly with an image. Download any face image from the Internet.

```bash
curl -s -m 5 http://127.0.0.1:8081/detect/faces \
    -X POST \
    -H "Content-Type: application/octet-stream" \
    --data-binary @data/faces/adele.jpg | python3 -m json.tool
```

Prepare a small annotation file in `data/m3/annotations`. We name it `bedroom_03_2min_smoke.json`.

```json
{
  "bedroom_03": {
    "video_path": "data/videos/robot/bedroom_03.mp4",
    "mem_path": "data/memory_graphs/robot/bedroom_03.pkl",
    "qa_list": [
      {
        "question": "Where is Stella when the video starts?",
        "answer": "In the bedroom.",
        "question_id": "bedroom_03_Q01",
        "reasoning": "Stella walks in and says 'Okay my lovely bed Okay I'm back' around 00:05, and Lewis comments on her throwing the bag and clothes in the same room.",
        "timestamp": "00:05",
        "type": [
          "Environment Perception",
          "Temporal Reasoning"
        ],
        "before_clip": 2
      },
      {
        "question": "How does Stella feel when she first returns home?",
        "answer": "Happy but exhausted.",
        "question_id": "bedroom_03_Q02",
        "reasoning": "Stella says 'Well so happy today' at 00:00, then later 'I'm so happy today' at 00:18 and 'I'm exhausted but I'm still very happy' at 00:27.",
        "timestamp": "00:27",
        "type": [
          "Person Understanding",
          "Multi-Detail Reasoning"
        ],
        "before_clip": 2
      },
      {
        "question": "What do Stella and Lewis plan to do with the photos they took today?",
        "answer": "Put them in an album.",
        "question_id": "bedroom_03_Q03",
        "reasoning": "Around 01:04 Stella says 'I remember that we have taken so many pictures today' and 'Maybe we should put our photos in the album'. Lewis agrees 'Of course.'",
        "timestamp": "01:08",
        "type": [
          "General Knowledge Extraction",
          "Multi-Detail Reasoning"
        ],
        "before_clip": 4
      },
      {
        "question": "What does Stella ask the Robot to fetch?",
        "answer": "The pictures in her bag.",
        "question_id": "bedroom_03_Q04",
        "reasoning": "At 01:16 Stella says 'Hello Robot. Please fetch the pictures in my bag for me', and the Robot replies 'Ok.'",
        "timestamp": "01:18",
        "type": [
          "Action Recognition",
          "General Knowledge Extraction"
        ],
        "before_clip": 4
      },
      {
        "question": "What color photo does Stella specifically need from her bag?",
        "answer": "White.",
        "question_id": "bedroom_03_Q05",
        "reasoning": "At 01:44, 01:55 and 02:00 Stella repeats 'Robot I need a white one' / 'the white one', specifying the color.",
        "timestamp": "01:58",
        "type": [
          "Multi-Detail Reasoning"
        ],
        "before_clip": 5
      }
    ]
  }
}
```

Double check the qa section in `config/m3/pipelines/video_episodic_full.yaml`, make sure the annotation field points to the small annotation file we prepared.

Use the following command to run a complete example with face recognition, voice ASR, speaker diarization, spaker embedding, etc. Remember to check the work dir path, log path and GRAPH_DSN value. 

```bash
export GRAPH_DSN='host=127.0.0.1 port=31875 dbname=ogmem user=ogmem password=YOUR_POSTGRES_PASSWORD' && uv run --no-sync python -m m3.run_video_pipeline \
    --pipeline config/m3/pipelines/video_episodic_full.yaml \
    --video data/m3/videos/robot/bedroom_03.mp4 \
    --video-id bedroom_03 \
    --seconds 120 \
    --work-dir data/m3_runs/bedroom_03_full_0807_qa \
    --config data/ogmem_test_lyj.resolved.yaml \
    --graph-store sql \
    --connection-string "$GRAPH_DSN" \
    --llm minimax \
    --build-index \
    --enable-stage voice_asr \
    --enable-stage speaker_diarization \
    --enable-stage speaker_embedding \
    --set detect_faces.params.backend=http \
    --set detect_faces.params.cv_service_url=http://127.0.0.1:8081 \
    --force \
    -v 2>&1 | tee data/m3_runs/pipeline_0807.log
```

The above command should take around 10 minutes to run.

### Inspect the result

The most important result is the QA result.

Use the following command to inspect the qa result.

```bash
cat data/m3_runs/bedroom_03_full_0807_qa/m3_qa_results.jsonl | \
  uv run --no-sync python -c "
import json, sys
for line in sys.stdin:
    r = json.loads(line)
    print(f'{r[\"question_id\"]}  iter={r[\"iterations\"]}  finish={r[\"finish_reason\"]}')
    print(f'  Q: {r[\"question\"]}')
    print(f'  expected: {r[\"expected_answer\"]}')
    print(f'  predicted: {r[\"predicted_answer\"][:160]}')
    for s in r['search_history']:
        print(f'    search#{s[\"round\"]} k={s[\"top_k\"]} q={s[\"query\"]!r}')
"
```

We can also use the `m3.eval` to evaluate the result.

```bash
 uv run python -m m3.eval \
    --annotations data/m3/annotations/bedroom_03_2min_smoke.json \
    --input-qa-results data/m3_runs/bedroom_03_full_0807_qa/m3_qa_results.jsonl \
    --output-dir data/m3_eval/
```

Then we can use the same method to log in to the database and inspect the database content.

```bash
docker exec -it ogmem-postgres-YOUR_USER psql -U ogmem -d ogmem
```

Below I prepared some SQL queries to run.

```sql
/* An overview of the graph_nodes table */
SELECT node_type, count(*) FROM graph_nodes GROUP BY node_type ORDER BY 2 DESC;

/* According to extractor_type, check node_type. This is how we achieve multi-modal. */
SELECT extractor_type, node_type, count(*) FROM graph_nodes GROUP BY extractor_type, node_type ORDER BY 2 DESC, 3 DESC;

/* Look at the subclasses of raw: video / audio / image */
SELECT raw_type, count(*) FROM graph_nodes WHERE raw_type IS NOT NULL GROUP BY raw_type;

/* edge type and amount */
SELECT edge_type, count(*) FROM graph_edges GROUP BY edge_type ORDER BY 2 DESC;

/* The complete matrix for edges */
SELECT
    src.extractor_type  AS src_kind,
    src.raw_type        AS src_raw,
    src.node_type       AS src_node,
    e.edge_type,
    tgt.extractor_type  AS tgt_kind,
    tgt.raw_type        AS tgt_raw,
    tgt.node_type       AS tgt_node,
    count(*)            AS n
  FROM graph_edges e
  JOIN graph_nodes src ON src.node_id = e.source_id
  JOIN graph_nodes tgt ON tgt.node_id = e.target_id
  GROUP BY src.extractor_type, src.raw_type, src.node_type, e.edge_type,
           tgt.extractor_type, tgt.raw_type, tgt.node_type
  ORDER BY n DESC;
  
/* same_identity edge */
SELECT e.source_id::text AS member, e.target_id::text AS anchor,
         e.properties->>'score' AS score
FROM graph_edges e
WHERE e.edge_type = 'same_identity';

/* evolves edge */
SELECT source.summary AS from_desc, target.summary AS to_consolidated
FROM graph_edges e
  JOIN graph_nodes source ON source.node_id = e.source_id
  JOIN graph_nodes target ON target.node_id = e.target_id
WHERE e.edge_type = 'evolves';

/* supports edge */
SELECT count(*) AS supports_edges FROM graph_edges WHERE edge_type='supports';

/* co_occurs_in edge */
SELECT count(*) AS co_occurs FROM graph_edges WHERE edge_type='co_occurs_in';

/* edge type constraints */
SELECT pg_get_constraintdef(oid)
FROM pg_constraint WHERE conname='valid_edge_type';

/* Audio RAW nodes */
SELECT node_id::text AS audio_node,
         metadata->>'source_path' AS wav_path,
         (metadata->>'duration_sec')::numeric AS dur_sec,
         (metadata->>'sample_rate')::int AS sr_hz,
         metadata->>'clip_id' AS clip
FROM graph_nodes
WHERE raw_type = 'audio'
ORDER BY metadata->>'source_path';

/* Voice Segmentation */
SELECT vs.node_id::text AS voice_seg,
         vs.extracted_content->>'start_sec' AS start_sec,
         vs.extracted_content->>'end_sec' AS end_sec,
         vs.extracted_content->>'duration_sec' AS dur_sec,
         jsonb_array_length(vs.extracted_content->'voice_embedding') AS voice_emb_dim,
         vs.source_raw_id::text AS parent_audio
FROM graph_nodes vs
WHERE vs.extractor_type = 'voice_segmentation';

/* audio -> audio extractor */
SELECT e.source_id::text AS audio_raw,
         e.target_id::text AS audio_extracted,
         e.edge_type
  FROM graph_edges e
  JOIN graph_nodes src ON src.node_id = e.source_id
  JOIN graph_nodes tgt ON tgt.node_id = e.target_id
WHERE src.raw_type = 'audio' AND tgt.extractor_type = 'audio_extractor';

/* Episodic memory */
SELECT
    extractor_type,
    (extracted_content->>'source_clip_id')::int AS clip,
    extracted_content->>'has_audio' AS has_audio,
    jsonb_array_length(extracted_content->'events') AS events_n,
    jsonb_array_length(extracted_content->'characters') AS chars_n,
    jsonb_array_length(extracted_content->'entities') AS entities_n,
    jsonb_array_length(extracted_content->'embedding') AS emb_dim,
    substring(extracted_content->>'description', 1, 120) AS desc_preview
FROM graph_nodes
WHERE extractor_type = 'episodic_memory_generator'
ORDER BY (extracted_content->>'source_clip_id')::int;
  
/* The extracted content of episodic memory */
SELECT jsonb_pretty(extracted_content)
FROM graph_nodes
WHERE extractor_type='episodic_memory_generator'
LIMIT 1;

/* per-clip memory nodes */
SELECT summary, topic FROM graph_nodes
WHERE node_type = 'memory' AND topic LIKE 'm3:%' ORDER BY topic, summary;

/* semantic consolidated memory */
SELECT summary, topic FROM graph_nodes
WHERE node_type = 'memory' AND topic LIKE 'semantic:%';
```

Congratulations! You've finished an end-to-end run for the AntTrail memory system.