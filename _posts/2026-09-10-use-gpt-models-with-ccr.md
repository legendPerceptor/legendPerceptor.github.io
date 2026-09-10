---
title: 通过Claude Code Router使用OpenAI GPT系列模型
date: 2026-09-10 08:43:00 +0800
categories: [Tutorial]
tags: [codex, claude code, ccr, openai]
pin: false
math: true
---

通过在[BandwagonHOST](https://bandwagonhost.com/)等云服务商租借Virtual Private Server(VPS)后，我们就可以在一台拥有公网IP且配置了多种网络加速的服务器上部署服务了。我们使用[CLIProxyAPI](https://github.com/router-for-me/CLIProxyAPI)部署模型代理的服务，实现多人共享模型账号，且支持多个模型账号(多个Codex Pro账号，多个Kimi账号等)之间的负载均衡。最后通过在AWS等域名服务商购买某个域名，实现给大家提供base url和api key的模型服务。该流程仅供学习交流，请勿用于其他不当目的。

## 工具安装和基本配置

本地或者在开发机上使用时，建议安装[Claude Code Router](https://github.com/musistudio/claude-code-router)和Codex。如果是在Windows或者macOS上开发，可以直接使用ChatGPT App，否则就使用命令行工具。

### 安装uv管理Python相关的依赖

如果你还在使用Virtualenv或者Conda，建议尝试使用uv，依赖安装更快，管理模式更现代。

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 安装fnm用于Node.js的版本管理

```bash
curl -fsSL https://fnm.vercel.app/install | bash
fnm install --lts
```

### 设置ssh key和git选项

```bash
ssh-keygen -t ed25519 -C "YOUR_EMAIL@example.com"
# 把公钥复制出来加入github, gitcode的ssh key中
cat ~/.ssh/id_ed25519.pub

git config --global user.name "YOUR_NAME"
git config --global user.email "YOUR_EMAIL@example.com"
git config --global pull.rebase true
# 如果使用access_token的方式管理，下面的选项可以避免每次输密码
git config --global credential.helper store

# 如果需要网络代理，请自行解决网络代理配置
# git config --global http.proxy socks5h://127.0.0.1:1080
# git config --global https.proxy socks5h://127.0.0.1:1080
```

### 安装codex

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

### 安装Claude Code Router和Claude Code

如果你按照上述步骤进行，npm已经由fnm管理，所以可以直接全局安装。

```bash
npm install -g @anthropic-ai/claude-code@latest
npm install -g @musistudio/claude-code-router@latest
```

## Claude Code Router配置

> 请不要开启代理访问，特别是如果你的代理也在BandwagonHost的话。或者把我给你的网址加入no_proxy，保证直连访问。
{: .prompt-tip }

如果是在远程的开发机器上，可能会遇到端口和其他用户冲突的问题，所以我们用下面的命令，指定端口启动ccr，你可以指定任意一个空闲的端口。

```bash
ccr start --host 127.0.0.1 --port 5223 --no-open
```

命令行中会打印出一串带token的URL，把它记录下来。

在你的本地电脑中，用ssh命令进行一个port forwarding，从而在本地浏览器打开Claude Code Router的管理界面。

```bash
ssh -N -L 5223:127.0.0.1:5223 YOUR_USER@YOUR_SERVER_IP
```

首先修改CCR的服务端口，我们前面指定的端口是它的UI端口，如下图所示。

![CCR Port Setting](/images/2026-09-10-codex/ccr-setting-port.png)

接下来点击`添加`，选择其他/自定义API地址。自定义一个名称，然后输入我提供的base url地址后点击下一步。

![CCR Set Provider 1](/images/2026-09-10-codex/ccr-set-provider-1.png)

这一步输入我给你的API Key，继续点击下一步。

![CCR Add API Key](/images/2026-09-10-codex/ccr-add-api-key.png)

应该会非常快地加载出供应商模型，点击自己想用的，它会从左边加到右边的框里，点击下一步。

![CCR Select Models](/images/2026-09-10-codex/select-models.png)

这里有连通性检测，点击开始检测，检测成功后就说明配置已经没有问题了，模型配置的最终结果如下所示。

![CCR final result](/images/2026-09-10-codex/final-result.png)

最后在`Agent配置档案`界面中的Codex里把模型选成我们刚刚配好的`bandwagon/gpt-6-astra`，打开Codex。下次运行codex命令时，就会被Claude Code Router接管，从而使用我们配置的中转服务。

如果你在Windows或者macOS上操作的话，重启一下ChatGPT App，你会发现左下角写的是Claude Code Router而不是本来的Chat GPT账户，右下角可以选择Claude Code Router配置的模型。

如下图所示，你的Codex已经可以访问GPT模型！

![codex running](/images/2026-09-10-codex/codex-running.png)

恭喜，你已经完成了配置，可以开始构建你的项目了！

