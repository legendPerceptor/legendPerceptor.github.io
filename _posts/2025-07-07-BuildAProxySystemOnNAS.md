---
title: Build a proxy network system on NAS for home devices
author: yuanjian
date: 2025-07-07 09:54:00 +0800
categories: [Tutorial]
tags: [proxy network, iptables, docker, v2ray]
pin: false
---

In this article, we will show you how to build a proxy system on your home NAS. If you have demands to use a proxy to access certain websites or apps, you probably want to buy a service instead of building your own proxy server, as they will provide you more IPs in case some specific ones are blocked. I use [Just My Socks](https://justmysocks.net/) for many years and consider it pretty reliable (not affiliated at all). After you have some kind of vmess, shadowsocks, or trojan services, you can proceed to install a proxy tool on your Network Attached Storage (NAS) or maybe a Raspberry Pi that connects to your home router via a network cable.

> We focus on letting devices like a TV access network through the proxy without installing any apps so the proxy is transparent (invisible) to the device. If you just want to use the proxy on your computer or your phone, you can simply install the [V2RayU](https://en.v2rayu.org/) app (for macOS), the [Shadow Rocket](https://apps.apple.com/us/app/shadowrocket/id932747118) app (for iOS), the [v2rayNG](https://en.v2rayng.org/) app for Android, and [v2rayN](https://en.v2rayn.org/) (for Windows) to control the network flow directly on your device. I use UGREEN DXP2800 NAS and it has a Debian-based system called UGOS PRO. If you use Raspberry Pi or some customized devices, I recommend installing the Ubuntu operating system so the commands will almost be identical.
{: .prompt-tip }

I will show you how to use v2ray to export HTTP and SOCKS ports for other home devices, and set up a transparent proxy for a TV that can intelligently use proxy to access foreign websites and direct connection to access domestic websites. We will use a Docker container for the v2ray proxy service, `iptables` to alter the TV traffic, ip forwarding for network flows from the TV. The idea is to let the network flows from a TV (or other devices) to go through our NAS, and the NAS will guide the foreign access flows through our proxy servers and forward the domestic flows directly.

First of all, you need to temporarily run the v2ray-core app in the NAS Linux system to allow docker to pull the v2fly/v2fly-core container. I recommend creating a folder called `v2ray` in your home folder, and run v2ray-core with the following config --- save the file as config.json in the v2ray-core app folder, and run the app. 

> You need to replace all the `<YOUR_STH>` strings with your own values, and type in the corresponding port (19805 is probably not your port) to run it properly.
{: .prompt-tip }

```json
{
  "log": {
    "error": "/home/<YOUR_USER_ID>/v2ray/v2ray-core.log",
    "access": "/home/<YOUR_USER_ID>/v2ray/v2ray-core.log",
    "loglevel": "info"
  },
  "inbounds": [
    {
      "settings": {
        "auth": "noauth",
        "udp": false
      },
      "port": "1080",
      "protocol": "socks",
      "listen": "127.0.0.1"
    },
    {
      "settings": {
        "timeout": 360
      },
      "port": "1087",
      "protocol": "http",
      "listen": "127.0.0.1"
    }
  ],
  "outbounds": [
    {
      "mux": {
        "enabled": false,
        "concurrency": 8
      },
      "tag": "proxy",
      "settings": {
        "vnext": [
          {
            "users": [
              {
                "level": 0,
                "alterId": 0,
                "security": "auto",
                "id": "<YOUR_V2RAY_SERVICE_ID>"
              }
            ],
            "address": "<YOUR_V2RAY_SERVICE_DOMAIN>",
            "port": 19805
          }
        ]
      },
      "streamSettings": {
        "security": "none",
        "network": "tcp",
        "tcpSettings": {
          "header": {
            "type": "none"
          }
        }
      },
      "protocol": "vmess"
    },
    {
      "tag": "direct",
      "protocol": "freedom",
      "settings": {
        "domainStrategy": "UseIP",
        "userLevel": 0
      }
    },
    {
      "tag": "block",
      "protocol": "blackhole",
      "settings": {
        "response": {
          "type": "none"
        }
      }
    }
  ],
  "dns": {},
  "routing": {
    "balancers": [],
    "domainStrategy": "AsIs",
    "rules": []
  }
}
```

Note that we set the port 1087 for HTTP flows. Docker can use this port for downloading images via proxy. We need to add a file `http_proxy.conf` on your NAS in this folder `/etc/systemd/system/docker.service.d/` with root priviledge. If there is no such folder just create one. The file content will be

```bash
[Service]
Environment="HTTP_PROXY=http://127.0.0.1:1087"
Environment="HTTPS_PROXY=http://127.0.0.1:1087"
```

Then we can try to get the v2fly/v2fly-core image with `docker pull v2fly/v2fly-core`. If it successfully pulled the image, it means your proxy works and docker can use it. If it didn't work, try to verify if your proxy works first with `curl -x http://127.0.0.1:1087 google.com`. If it returns proper website content, then your proxy works, otherwise you need to check your v2ray configuration and the v2ray-core's status or logs.

Once your docker image is pulled, we can run the v2fly container with the following command. We need to map 3 ports 1081 for SOCKS, 1082 for HTTP, and 12345 for transparent proxy. Because transparent proxy's behavior, it is recommended not to use `-p 12345:12345`, but we export all the network ports via `--network=host`, though we know there are only 3 ports that will be used.

> There is another `config.json` file that we have not mentioned. This is different from the previous temporary v2ray-core configuration. This file is for the v2fly container, we will list the file content later. Make sure you have the file in the correct path before you run the commmand.
{: .prompt-warning }

```bash
sudo docker container run -d --name v2ray \
    -v ~/v2ray/config/config.json:/etc/v2ray/config.json \
    --network=host \
    v2fly/v2fly-core run -c /etc/v2ray/config.json
```

Add the following `inbounds` rule for transparent proxy. There is a protocol called `dokodemo-door` that allows apps without any proxy capabilities to transparently use the proxy. Protocols like SOCKS or HTTP requires the application support (for example, Docker allows you to set a `http_proxy.conf` file for proxy access) while this `dokodemo-door` requires nothing and thus can let a TV to use the proxy without knowing the proxy's existence.

```json
    {
      "port": 12345,
      "protocol": "dokodemo-door",
      "settings": {
        "network": "tcp,udp",
        "followRedirect": true
      },
      "streamSettings": {
        "sockopt": {
            "tproxy": "redirect"
        }
      },
      "sniffing": {
        "enabled": true,
        "destOverride": ["http", "tls"]
      }
    }
```

To make the proxy intelligent (separating direct flows and proxy flows), we use the "routing" configuration. We set all accesses to `geosite:cn` and `geoip:cn` as direct access so if the ip is determined to be inside China, we do not use the proxy, while for others, we access it via the v2ray proxy.

```json
{
  ...
  "routing": {
    "domainStrategy": "AsIs",
    "rules": [
      {
        "type": "field",
        "domain": ["geosite:cn"],
        "outboundTag": "direct"
      },
      {
        "type": "field",
        "ip": ["geoip:cn"],
        "outboundTag": "direct"
      },
      {
        "type": "field",
        "domain": ["geosite:geolocation-!cn"],
        "outboundTag": "proxy"
      }
    ]
  }
}
```

After changing the configuration, you need to restart the docker container to ensure the changes are updated. Run `sudo docker container restart v2ray` and `sudo docker container ls` to verify the container is running properly. Sometimes the container may have exited immediately because of incorrect settings, you should view the logs via `sudo docker logs v2ray` to find problems.

We need to enable ip forwarding on the NAS device, otherwise your TV has no Internet access.

```bash
sudo sysctl -w net.ipv4.ip_forward=1
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

Finally, to make the TV access the proxy via the `dokodemo-door` protocal, we need to manually set a static ip for the TV and make the default gateway to our NAS device. We assume setting the TV with an ip 192.168.0.119 and the NAS device with an ip 192.168.0.113. There is a network setting on your TV's setting, use `manual` mode and set the ip to 192.168.0.119 and gateway to 192.168.0.113. The default gateway is 192.168.0.1, which is your router. If your router uses other subnets like 10.0.0.1, then choose your ip in the same subnet like 10.0.0.100 (do not stick to 192.168.0.xxx). Then we need to use `iptables` to hijack your TV's network flows and route them to v2ray's 12345 port to use the `dokodemo-door` protocol. It is a series of commands so I prepared a script, you can save it anywhere and run the script. I added clearing commands in the beginning so reentry is safe for this script.

```bash
#!/bin/bash

# clear all PREROUTING from the TV
while iptables -t nat -C PREROUTING -s 192.168.0.119 -p tcp -j V2RAY 2>/dev/null; do
    iptables -t nat -D PREROUTING -s 192.168.0.119 -p tcp -j V2RAY
done


# Clear the V2RAY chain (if exists)
iptables -t nat -F V2RAY 2>/dev/null

# Delete the V2RAY chain
iptables -t nat -X V2RAY 2>/dev/null

# Create a new chain
iptables -t nat -N V2RAY

# keep local addresses
iptables -t nat -A V2RAY -d 192.168.0.0/16 -j RETURN
iptables -t nat -A V2RAY -d 127.0.0.1/32 -j RETURN
iptables -t nat -A V2RAY -d 224.0.0.0/4 -j RETURN
iptables -t nat -A V2RAY -d 255.255.255.255/32 -j RETURN

# All tcp flows to dokodemo-door
iptables -t nat -A V2RAY -p tcp -j REDIRECT --to-ports 12345

# Only preroute the flows from the TV
iptables -t nat -A PREROUTING -s 192.168.0.119 -p tcp -j V2RAY
```

At this point, your TV should be able to access both domestic and foreign apps. TVs in China do not have Google's services so it is impossible to install YouTube (log in with your Google account). You will have to reinstall the system with root privilege, which is also likely prohibited by many manufacturers. I only installed `爱壹帆` to go through this process for fun. Domestic memberships are usually much cheaper than foreign ones. If you want to enjoy TV shows, I always recommend using the domestic apps.