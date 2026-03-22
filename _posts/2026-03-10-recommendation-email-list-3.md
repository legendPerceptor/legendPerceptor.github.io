---
title: Content Recommendation for March, 2026
date: 2026-02-22 22:45:00 +0800
categories: [Content Recommendation]
tags: [OpenClaw]
pin: false
---

Hey there! Thanks for subscribing to my content recommendation posts. In this series, I share articles, videos, projects, and ideas that I recently found interesting, insightful, or genuinely helpful.

This edition includes content I curated during March, 2026. In this month, we see very powerful AI tools emerged one after another. The technological explosion could affect everyone's life sooner or later. Catching up early will do more good than bad for you. We also see tragical wars between the US and Iran. May the world be peaceful and I hope everyone can live a life they want.

## ONE OpenClaw agent to run in your NAS

[OpenClaw](https://openclaw.ai/) turns an LLM into an operational agent that can interact with software, services, and users. 

By the time you read this article, you have probably already heard about this project and been amazed by how quickly it has gained popularity. In this guide, I will show you how to install it on a NAS and provide a solid starting point for exploring and experimenting with this powerful AI agent.

I assume you use UGREEN NAS or some kind of computer systems that run 24/7 at your home. OpenClaw is better deployed on such platforms with Docker. How to deploy it on your laptop is not covered in this tutorial (although you can still learn about the proxy setup here). For installing it in your laptop, you can go to [OpenClaw's Official Website](https://openclaw.ai/), as it is pretty straightforward.

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

## SEVEN English words to learn for the week

> I recommend visiting [Merriam-Webster Dictionary](https://www.merriam-webster.com/dictionary/) to understand each word better and find more examples.
{: .prompt-info }

*reparation*: the act of making amends, offering expiation, or giving satisfaction for a wrong or injury. Example: They've offered no apologies and seem to have no thoughts of reparation. She says she's sorry and wants to make reparations.

*explicit*: fully revealed or expressed without vagueness, implication or ambiguity. Example: In some cases, the role of sporting director is focused on the long-term, but Berta was explicit about coming to Arsenal to work closely with Arteta, to win, and to do so immediately.

*clout chaser*: A "clout chaser" is a derogatory term for someone who desperately seeks fame, attention, or social media popularity.

*publicity stunt*: A publicity stunt is a planned, often theatrical event designed to generate media coverage and public attention for a person, brand, or cause.

*cuckold/cuck*: A cuckold is a man whose wife has committed adultery, a term with deep historical roots often implying mockery of the husband as a fool.

