---
title: Content Recommendation for March, 2026
date: 2026-03-22 22:45:00 +0800
categories: [Content Recommendation]
tags: [OpenClaw]
pin: false
---

Hey there! Thanks for subscribing to my content recommendation posts. In this series, I share articles, videos, projects, and ideas that I recently found interesting, insightful, or genuinely helpful.

This edition includes content I curated during March, 2026. In this month, we see very powerful AI tools emerged one after another. The technological explosion could affect everyone's life sooner or later. Catching up early will do more good than bad for you. We also see tragical wars between the US and Iran. May the world be peaceful and I hope everyone can live a life they want.

## ONE OpenClaw agent to run in your NAS

[OpenClaw](https://openclaw.ai/) turns an LLM into an operational agent that can interact with software, services, and users. 

By the time you read this article, you have probably already heard about this project and been amazed by how quickly it has gained popularity. In this guide, I will show you how to install it on a NAS and provide a solid starting point for exploring and experimenting with this powerful AI agent.

I assume you use UGREEN NAS or some kind of computer systems that run 24/7 at your home. OpenClaw is better deployed on such platforms with Docker to have more fine-grained priviledge control.

If you want to install it in your laptop, better use a virtual machine like WSL on Windows or a brand new laptop that belongs to your OpenClaw to avoid security issues (OpenClaw can access everything you store on your computer). You can go to [OpenClaw's Official Website](https://openclaw.ai/) for  instructions on installing it on your laptop.

### Configure OpenClaw with Feishu

To avoid needing a proxy network, we use the image `1panel/openclaw`. The important thing is to map your NAS storage to `/home/node/.openclaw`, so all the configuration files are visable and editable directly in NAS. In this way, we can use different methods to configrue OpenClaw before running the gateway.

```bash
docker pull 1panel/openclaw
docker run -d \
  --name 1panel_openclaw-1 \
  -v /volume1/shared-shanghai/openclaw-workhome/1panel-claw:/home/node/.openclaw \
  1panel/openclaw
```

> It is important to have the volume mapping because the openclaw container will shutdown itself when you change the configuration. This can be very annoying! We need to configrue it with other tools and then start the actual openclaw container. Check my project [openclaw-stable](https://github.com/legendPerceptor/openclaw-stable) to avoid the container shutting itself down when updating configurations.
{: .prompt-tip }

```bash
docker run -it \
 -v /volume1/shared-shanghai/openclaw-workhome/1panel-claw:/home/node/.openclaw \
 --rm --entrypoint bash 1panel/openclaw
```

We can configure everything needed by OpenClaw now with `openclaw configure`. For simplicity, we just configure one model and then use Feishu's plugin to connect it to Feishu.

We install the official Feishu plugin to ease the burden. It will give you a QR code to register a robot.

```bash
npm config set registry http://mirrors.cloud.tencent.com/npm/
npx -y @larksuite/openclaw-lark-tools install
```

You can exit to the host machine and start the actual openclaw container now.

```bash
docker start 1panel_openclaw-1
```

Now you should be able to communicate with the OpenClaw through Feishu (the robot is created by the Feishu's plugin). At the moment, you use a domestic model (e.g. GLM) and a domestic channel (Feishu), so you don't need any proxy for this basic setup to work. Congratulations!

To configure other things unrelated to OpenClaw, we can enter the container with the following command.

```bash
docker exec -it 1panel_openclaw-1 bash
```

If you want to use proxy for some foreign websites, we need to start the container in another way with some environment variables. As for how to set the proxy service up in a container, keep reading.

```bash
docker run -d \
  --name 1panel_openclaw-1 \
  --network proxy-net \
  -v /volume1/shared-shanghai/openclaw-workhome/1panel-claw:/home/node/.openclaw \
  -e HTTP_PROXY=http://xray:1087 \
  -e HTTPS_PROXY=http://xray:1087 \
  -e NO_PROXY=localhost,127.0.0.1,*.feishu.cn,*.larksuite.com,*.zhipuai.cn,bigmodel.cn,open.bigmodel.cn \
  1panel/openclaw

# We can test the proxy inside the container with the following command.
curl -x http://xray:1087 https://www.google.com -I
```

### Install Claude Code for OpenClaw to use

Read [this article](https://docs.bigmodel.cn/cn/coding-plan/tool/claude#claude-code) by Zhipu to install Claude Code with the GLM model behind it.

Use the following command to enter the container as the root user.

```bash
docker exec -u root -it 1panel_openclaw-1 bash
```

Install Claude Code and configure with GLM API.

```bash
npm config set registry http://mirrors.cloud.tencent.com/npm/
npm install -g @anthropic-ai/claude-code
npx @z_ai/coding-helper
```

### Configure Network Proxy (For Discord and other foreign platforms)

> Discord proxy caused me a lot of troubles. I succeeded configuring it with two different ways. If you use OpenClaw in WSL or a physcial machine, you can use systemd's environment variable to proxy it. If you use docker, this step is a bit troublesome. You need to proxy it in both the environment variable level, and the openclaw's Discord configruation level. I recommend asking OpenClaw to configure itself after you set up your xray container.
{: .prompt-danger }

> I cannot assist you to set up your proxy step-by-step. If you never heard of `v2ray`, `xray` or `shadowsocks`, `vmess`, it is probably hard for you to finish this. But if you used at least one of these, I am sure you can follow along with maybe a little help from ChatGPT.
{: .prompt-warning }

We need to configure the network proxy first as always. You need a proxy usable in the first place (usually your macOS's proxy or your Windows' proxy). Then you can borrow that proxy for docker and configure docker's proxy in this path: `/etc/systemd/system/docker.service.d/http-proxy.conf`.

Alternatively, you can use `~/.config/systemd/user/openclaw-gateway.service.d/proxy.conf` to add the proxy info to systemd.

Always remember to run the following commands to activate the config after modification.

```bash
systemctl --user daemon-reload
systemctl --user restart openclaw-gateway
```


The file's content should look like this. I assume `192.168.73.26` is your laptop's proxy and you have a service that exports port 1087 for HTTP and HTTPS proxies.

```bash
[Service]
Environment="HTTP_PROXY=http://192.168.73.26:1087"
Environment="HTTPS_PROXY=http://192.168.73.26:1087"
Environment="NO_PROXY=localhost,127.0.0.1,192.168.*.*"
```

Also set the proxy in `~/.bashrc`.

```bash
export proxy_url="http://192.168.73.26:1087"

function pon() {
    export http_proxy=$proxy_url
    export https_proxy=$proxy_url
    export no_proxy="localhost, 127.0.0.1, 192.168.*.*"
    echo "Proxy on -> $proxy_url"
}

function poff() {
    unset $http_proxy
    unset $https_proxy
    echo "Network Proxy turned off"
}
```

Use `pon` to turn on the proxy and test it with `curl google.com`. If you see a response like the following, your proxy worked! If not, make sure you run your proxy service in your host machine with `0.0.0.0` instead of `127.0.0.1`.

```html
<HTML><HEAD><meta http-equiv="content-type" content="text/html;charset=utf-8">
<TITLE>301 Moved</TITLE></HEAD><BODY>
<H1>301 Moved</H1>
The document has moved
<A HREF="http://www.google.com/">here</A>.
</BODY></HTML>
```

Then restart your docker service to apply this proxy setting.

```bash
sudo systemctl daemon-reload
sudo systemctl restart docker
# Check docker's status and verify it is running
sudo systemctl status docker
```

And you can then create a dedicated proxy container for future network proxy, so you no longer need your laptop nearby for NAS to have network proxy.

```bash
# Create a docker network and connect the container x2ray to it.
docker network create proxy-net
docker run -d \
  --name xray \
  --restart always \
  --network proxy-net \
  -v /volume1/docker/xray/config.json:/etc/xray/config.json:ro \
  teddysun/xray
```

Then we can start the openclaw container and connect it to the proxy-net network. We need to set a folder on the NAS for OpenClaw to work with. This folder is better to be a dedicated folder that is newly created, so OpenClaw has no rights to access your existing files and could not cause detrimental problems to your data.

### Use openclaw-stable docker image

> To allow openclaw to configrue itself, we add a `superviord` process so that the container does not stop when openclaw configuration changes. I wrote a project called [openclaw-stable](https://github.com/legendPerceptor/openclaw-stable), you can use docker to build this image.
{: .prompt-tip }

```bash
# Start the container for openclaw
# !Attention: Change -v options, the working directory mapping to your own. 
docker run -d \
  --name openclaw \
  --restart always \
  --network proxy-net \
  -v /volume1/shared-shanghai/openclaw-workhome/1panel-claw:/home/node/.openclaw \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /usr/bin/docker:/usr/bin/docker \
  -v /var/log/openclaw:/var/log/supervisor \
  -v /home/briannas/.ssh:/home/node/.ssh \
  -e HTTP_PROXY=http://xray:1087 \
  -e HTTPS_PROXY=http://xray:1087 \
  -e NO_PROXY=localhost,127.0.0.1,*.feishu.cn,*.larksuite.com,*.zhipuai.cn,bigmodel.cn,open.bigmodel.cn \
  openclaw-stable
```

Use `docker network inspect proxy-net` to check if the docker network is configured properly.

Let's test the network in openclaw container.

```bash
docker exec -u root -it openclaw bash
docker exec -it openclaw bash
docker exec -it openclaw sh -lc "curl google.com"
docker logs openclaw --tail 200
```

Let's see if Discord can be reached from this container:

```bash
curl -I https://discord.com/api/v10/gateway
```

If you see `HTTP/1.1 200 Connection established`, then your network works! We should be able to use OpenClaw freely now.

As for how to configure your Discord bot, you can ask your OpenClaw on Feishu. In short, you need to create an application in the Discord developer platform, create a bot and give it the permissions (Presence Intent, Server Members Intent, Message Content Intent), then invite your bot to your private server by generating an URL in the OAuth2 tab. Then, OpenClaw will need your userID, your guild ID (server ID, channel ID), and you should be able to figure it out by communicating with OpenClaw.

Congratulations on having your AI assistant available on both Feishu and Discord platforms.

### Enhanced Memory System (Optional)

OpenClaw comes with a file-based memory system by default, which loads your entire MEMORY.md into every conversation. While simple, this has some limitations:

- Memory grows linearly with conversation history
- No semantic search capability
- Higher token consumption as memory expands

You can enhance it with [Agent Memory](https://github.com/legendPerceptor/agent-memory) - a vector-based memory system using Qdrant and OpenAI embeddings. This enables:

- **Semantic search**: Find relevant memories by meaning, not just keywords
- **Efficient retrieval**: Only load relevant context, not entire history
- **Better scalability**: Handle thousands of memories without token bloat

> You can totally leave the setup to OpenClaw and other agents. The information below is mainly for you to understand how it works. You do not need to follow the setup step by step. 
{: .prompt-tip }

#### Setup Agent Memory

1. **Start a separate Qdrant container** (different from aicreatorvault's):

```bash
docker run -d \
  --name agent-memory-qdrant \
  --restart unless-stopped \
  -p 6336:6333 \
  -p 6337:6334 \
  -v agent_memory_qdrant_data:/qdrant/storage \
  qdrant/qdrant:latest
```

2. **Get OpenAI API Key** from [platform.openai.com](https://platform.openai.com/api-keys)

3. **Configure environment**:

```bash
mkdir -p ~/.openclaw/workspace/agent-memory
cd ~/.openclaw/workspace/agent-memory

# Create .env file
cat > .env << 'EOF'
QDRANT_HOST=localhost
QDRANT_PORT=6336
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
HTTP_PROXY=http://your-proxy:1087
HTTPS_PROXY=http://your-proxy:1087
EOF
```

4. **Install dependencies**:

```bash
pip install --break-system-packages qdrant-client openai python-dotenv
```

5. **Use the Memory CLI**:

```bash
# Record a memory
python3 memory_cli.py remember "User prefers Chinese language" --type preference --importance 0.8

# Search memories
python3 memory_cli.py recall "user preferences"

# View stats
python3 memory_cli.py stats
```

The memory system will store your memories with OpenAI embeddings in Qdrant, enabling semantic search without loading everything into each conversation.

#### Automatic Backup (Optional)

Add to crontab for daily backups:

```bash
# Edit crontab
crontab -e

# Add this line (backup at 2am daily)
0 2 * * * docker run --rm -v agent_memory_qdrant_data:/data -v ~/backups:/backup busybox tar czf /backup/qdrant_$(date +\%Y\%m\%d).tar.gz /data
```


## THREE YouTube videos to watch for personal growth

In this post, I will recommend two videos in Chinese and one in English. The two videos in Chinese are both about the technology advancements in AI. And the video in English is for improving your learning mindset. Have a good time watching them!

[解剖小龍蝦 — 以 OpenClaw 為例介紹 AI Agent 的運作原理](https://www.youtube.com/watch?v=2rcJdFuNbZQ) by Hung-yi Lee (李宏毅). If you want to understand the internal procedures of how OpenClaw works, this video will be super helpful.

[E228｜谷歌TPU能撼动英伟达吗？前TPU工程师首次揭秘](https://www.youtube.com/watch?v=0h4hPRBgsVA) by 硅谷101播客. Can Google's TPU challenge NVIDIA's top position in AI chips?

[How To Learn So Fast It’s Almost Unfair](https://www.youtube.com/watch?v=npQ2IORdlvU) by theMITmonk, who introduces the Three C Protocol, a simple system designed to help you learn, retain, and apply knowledge at a top-1% level. Backed by real-world examples and cognitive science, you’ll see how your brain actually learns, why rest matters more than repetition, and the exact steps to upgrade how you acquire new skills.


### Video 1: How does AI Agent work?

#### OpenClaw Agent Workflow

AI Agents like OpenClaw manipulate language models to function as personal assistants by augmenting prompts with rich context from local files, allowing them to 'know' their identity and goals. When asked to introduce themselves, the AI generates a response based on a lengthy system prompt that contains pre-defined information, skills, and previous interactions, making it appear knowledgeable and personable. This process involves significant computational resources, as responses can involve over 4000 tokens due to the extensive context provided.

#### Agent Memory and Recall

The .md files stored within the AI Agent, like Soul.md, contain personal information such as its identity and goals, which are assigned by humans rather than self-generated. These files, while modifiable by users, can lead to confusion if changed inconsistently, as the AI's memory is dynamic and must align with its programming. The AI relies on past conversation history to function effectively, similar to a character from a movie dealing with severe amnesia, requiring consistent reminders of prior interactions.

#### Agent Tools and Execution

AI Agents like OpenClaw operate by executing specific commands on a computer, using embedded tools such as 'read' and 'write' to process tasks. When given a task, the agent relays commands to a language model, which interprets and executes them, potentially leading to vulnerabilities if not properly managed. Ensuring safety involves settings that require human approval before executing critical commands, as well as limiting the agent's ability to process external inputs such as YouTube comments.

#### Agent Self-Improvement

AI Agents can autonomously create tools to enhance their functionality. For instance, after processing commands for voice synthesis, an AI Agent generates a script named 'tts_check' to automate the speech synthesis and recognition process, which greatly simplifies tasks that would otherwise require repetitive manual communication. Despite their ability to create these tools, AI Agents often forget them and tend to recreate similar tools every time, leading to a clutter of temporary scripts.

#### Agent Subagents and Scaling

The Subagent, a specialized tool within the AI framework, enables the main agent to delegate tasks, such as comparing two papers, to its offspring subagents. These subagents interact extensively with a language model to summarize each paper, allowing the main agent to focus on high-level tasks by preserving context and reducing complexity. To prevent endless outsourcing of tasks among subagents, restrictions can be imposed to limit their ability to create further subagents.

#### Agent Skills and SkillHub

Skill refers to a procedural document used by AI agents, such as OpenClaw, to execute tasks efficiently and avoid missing steps. These skills are stored as text files and can be dynamically accessed upon request, ensuring minimal resource consumption during operation. Users can exchange skills through platforms like Cloud Hub, but caution is advised due to the potential for malicious files embedded within seemingly harmless Skill documents.

#### Agent Long-Term Memory

Skill functionalities may require caution, especially with ongoing operations like Lobster running 24/7 as a personal assistant via WhatsApp. To manage memory, Lobster employs a system that records experiences in .md files, while also utilizing search tools to retrieve past data effectively, although retrieval reliability can vary over longer timeframes. The agent's effectiveness can be limited with weaker models that may fail to execute memory tasks unless they actively write to the memory files.

#### Agent Heartbeats and Scheduling

The lobster utilizes a heartbeat mechanism to interact consistently with language models, enabling it to periodically send commands to perform tasks from a habit file. This system can be adjusted for frequency, allowing dynamic progress updates, akin to progress reports with a professor. Additionally, a Cron Job system complements this by scheduling tasks like video creation, enhancing the lobster's capability to manage timed operations effectively, including waiting for processes to complete.

#### Agent Context Management

OpenClaw utilizes a mechanism called context compaction which summarizes older conversation history into shorter versions, allowing the language model to operate within context window limits. This process is recursive, enabling continuous summarization as dialogue accumulates. Additionally, configurations like pruning and hard clear methods are employed to manage context length effectively and ensure smooth functionality of the AI.


### Video 2: Can Google TPU challenge NVIDIA?

#### Core Architectural Difference between TPU and NVIDIA GPU

🔵 NVIDIA GPU
General-purpose parallel processor.
Originally designed for graphics → evolved into CUDA compute.
Flexible: supports many workloads (training, inference, simulation, DB acceleration).

👉 Key idea:
**SIMT (Single Instruction, Multiple Threads)**

🟡 TPU (by Google)
Domain-specific ASIC for tensor operations only.
Built specifically for deep learning matrix multiplications.

👉 Key idea:
**Systolic array architecture (massive matrix multiply engine)**


#### Performance Characteristics in Pretraining

**TPU strengths**

Extremely high throughput for:
(1) dense matrix multiplication
(2) transformer training
(3) Better FLOPs utilization for large models
(4) High-speed interconnect (TPU pods)

👉 Especially strong for:

BERT / T5 / PaLM / Gemini-style training

**GPU strengths (e.g., NVIDIA A100 / H100)**

(1) More flexible workloads
(2) Strong performance for:
(3) mixed workloads
(4) sparse ops
(5) custom kernels

Better for:
(1) research iteration
(2) non-standard architectures


### Video 3: How to learn so fast it's almost unfair

We human beings are built for serial processing, do not do parallel processing when you learn.

The 3C protocol: Compress, Compile, Consolidate.

You cannot learn something new unless you connect it to something you already know.

Pick a conecpt -> learn it -> test it.

Tools: (1) slow burn; (2) immersion; (3) teach to learn.

#### Compression Techniques

To effectively learn, begin by compressing information into manageable chunks, focusing on the 20% of content that offers 80% of the value. Enhance retention by associating new concepts with existing knowledge and visualizing these connections through models or metaphors. This method allows for mastering ideas without overwhelming the brain's capacity to process multiple independent thoughts.

#### Compilation of Knowledge

Memory alone does not equate to mastery, as illustrated by Kim Peek, a savant with remarkable recall who struggled with everyday tasks due to his brain's unique structure. The 99% trap is focusing on information accumulation instead of true learning, which requires managing study periods (90 minutes of focused work followed by a 20-minute rest), and integrating frequent testing into the learning process. By adopting a cycle of learning and testing rather than waiting for a final assessment, one can enhance their learning efficiency.

#### Learning Tools

Effective learning involves three key tools: First, practice slowly and mindfully, focusing on every small movement to enhance skill retention. Second, immerse yourself in real-life situations to truly test your abilities, such as performing in front of an audience instead of just rehearsing alone. Lastly, solidify your knowledge by teaching others what you’ve learned, reinforcing your own understanding.

#### Consolidation and Rest

Learning involves a two-stage process: focus and rest, with the latter being crucial for consolidation. Frequent breaks during intense learning significantly enhance retention, allowing the brain to replay information at an accelerated pace. Additionally, practices like non-sleep deep rest (NSDR) and sufficient sleep are essential for maximizing learning outcomes and reinforcing what has been learned.

#### Long-term Learning Strategies

In the technological age, we've overlooked the necessity of rest for optimal learning, akin to how soil must recover to maintain fertility. Instead of comparing yourself to others, focus on personal growth, and remember that learning must be embraced with patience, as it follows a natural rhythm. Techniques that prioritize performance over criticism and allow for adequate time can lead to transformative results.

## FIVE international news to know

1. [Asia’s energy crisis stings](https://messaging-custom-newsletters.nytimes.com/dynamic/render?campaign_id=346&emc=edit_wor_20260324&instance_id=173015&isViewInBrowser=true&nl=the-world&paid_regi=1&productCode=WOR&regi_id=96411683&segment_id=217167&sendId=217167&uri=nyt://newsletter/75eb4904-d3d6-59c7-aa33-97c6444b5456) by New York Times. If you live in South Korea, the government has just asked you to take shorter showers and use the washing machine on weekends only. In Nepal, your family might be eating their dinner cold because of an acute shortage of cooking gas. And if you’re organizing a funeral in Pune, India, you can’t have a gas cremation — gas is being rationed for the living.

2. The secretive billionaire owner of OnlyFans, a platform that lets creators sell erotic content directly to users, Leonid Radvinsky, has died of cancer at age 43, the company shared yesterday.

3. [张雪峰因心源性猝死离世](https://www.ctdsb.net/c1476_202603/2696164.html).

4. An airplane crashed at the LaGuardia Airport in New York. It was a collision as the airplane hit a fire truck that was crossing the runway. [Investigators Focus on Potential Overlapping Failures in LaGuardia Crash](https://www.nytimes.com/live/2026/03/24/nyregion/laguardia-plane-crash?campaign_id=60&emc=edit_na_20260324&instance_id=173007&nl=breaking-news&regi_id=96411683&segment_id=217161).

5. News on the Iran war. US troop deployment: Around 1,000 US soldiers with the Army’s 82nd Airborne Division are expected to deploy in coming days to the Middle East, adding to the growing military firepower in the region as the Trump administration touts talks with Iran to end the conflict. [Iran's military rejects Trump's talk of negotiation, Israel and Iran launch airstrikes](https://www.reuters.com/world/asia-pacific/israel-strikes-tehran-trump-says-us-negotiating-end-war-2026-03-25/) by Reuters.


## SEVEN English words to learn for the week

> I recommend visiting [Merriam-Webster Dictionary](https://www.merriam-webster.com/dictionary/) to understand each word better and find more examples.
{: .prompt-info }

*reparation*: the act of making amends, offering expiation, or giving satisfaction for a wrong or injury. Example: They've offered no apologies and seem to have no thoughts of reparation. She says she's sorry and wants to make reparations.

*explicit*: fully revealed or expressed without vagueness, implication or ambiguity. Example: In some cases, the role of sporting director is focused on the long-term, but Berta was explicit about coming to Arsenal to work closely with Arteta, to win, and to do so immediately.

*clout chaser*: A "clout chaser" is a derogatory term for someone who desperately seeks fame, attention, or social media popularity.

*publicity stunt*: A publicity stunt is a planned, often theatrical event designed to generate media coverage and public attention for a person, brand, or cause.

*cuckold/cuck*: A cuckold is a man whose wife has committed adultery, a term with deep historical roots often implying mockery of the husband as a fool.

*kardashians*: The Kardashians are an American-Armenian family renowned for their massive influence on pop culture, fashion, and social media, largely through reality TV shows like Keeping Up with the Kardashians.

*potent*: having or wielding force, authority, or influence. Example: My secondary goal is to show you that, even if you don’t think you’re a “creative person,” you can enter an incredibly enjoyable state of consciousness. Similar to the flow state, but potentially more potent.
