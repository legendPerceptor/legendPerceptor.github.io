# subscribe-server

`yuanjianliu.net` 的邮件订阅后端：FastAPI + SQLite 单文件存储。设计说明见
[`../docs/email-subscription.md`](../docs/email-subscription.md)。

前端模块是仓库根目录的 `_includes/subscribe.html`，通过 `_config.yml` 的
`subscribe.endpoint` 指向本服务；可以放在任意页面。

## 目录

```
app/
  api.py        FastAPI 路由（订阅、退订、健康检查、admin）
  store.py      SQLite 存储（无第三方依赖，可单独使用/测试）
  validate.py   邮箱规范化、IP 加盐哈希
  ratelimit.py  单进程滑动窗口限流
  config.py     环境变量配置
cli.py          admin 命令行（不需要起 HTTP 服务）
tests/          pytest + unittest 测试
tests/frontend/ 渲染后 DOM 的前端脚本验证（jsdom）
deploy/         systemd 单元 + Caddyfile 片段
```

## 快速开始

### 方式 A：Docker（推荐）

```bash
cd subscribe-server
cp .env.example .env
python3 -c "import secrets; print(secrets.token_urlsafe(32))"   # 填进 ADMIN_TOKEN
python3 -c "import secrets; print(secrets.token_urlsafe(16))"   # 填进 IP_SALT
$EDITOR .env
docker compose up -d --build
curl -sS http://127.0.0.1:8080/healthz
```

> `./data` 不存在也没关系：镜像的 entrypoint 会先以 root 修好挂载目录的属主，
> 再降权到 `appuser`(uid 10001) 运行应用（因为 Docker 自动创建的 bind 目录在容器内属于
> root，非 root 进程写不进去）。容器日志里会看到
> `[entrypoint] /data ready, running as appuser (uid 10001)`。
> 附带说明：镜像默认用户是 root（entrypoint 需要），但**应用进程本身是 10001**——
> `docker compose exec subscribe-api grep Uid /proc/1/status` 可验证；`docker exec` 进去的
> shell 才是 root。

### 方式 B：systemd + venv

```bash
sudo useradd --system --create-home subscribe
sudo mkdir -p /opt/subscribe-server && sudo chown subscribe:subscribe /opt/subscribe-server
sudo -u subscribe git clone <this repo> /opt/subscribe-server   # 或 rsync subscribe-server/
cd /opt/subscribe-server/subscribe-server
sudo -u subscribe python3 -m venv .venv
sudo -u subscribe .venv/bin/pip install -r requirements.txt
sudo -u subscribe cp .env.example .env && sudo -u subscribe $EDITOR .env
sudo cp deploy/subscribe-api.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now subscribe-api
systemctl status subscribe-api --no-pager
```

### 发布 HTTPS

两种方式，**二选一**（都会监听 80/443，不能同时跑）。

**方式 1：Caddy 跑在宿主机**（当前这台机器用的就是这个）

`subscribe.yuanjianliu.net` 的 A/AAAA 记录指向服务器，把 `deploy/Caddyfile` 复制成
`/etc/caddy/Caddyfile`（或 include 进去），然后 `sudo systemctl restart caddy`。
Caddy 会自动签发证书 —— **必须 HTTPS**，否则 https 页面调用它会被浏览器按混合内容拦截。

**方式 2：Caddy 也跑在 Docker 里**（不需要 apt / sudo）

```bash
docker compose --profile tls up -d      # 启动 api + caddy 两个容器
docker compose logs -f caddy            # 看证书签发过程
```

同一个 `deploy/Caddyfile` 两种模式都能用：上游地址走环境变量 `SUBSCRIBE_UPSTREAM`，
默认 `127.0.0.1:8080`（宿主机模式），Docker 模式下 compose 会传 `subscribe-api:8080`。

nginx 用户等价配置：`location = /api/subscribe { proxy_pass http://127.0.0.1:8080; proxy_set_header X-Real-IP $remote_addr; }`，
并只放行 `/api/subscribe`、`/api/unsubscribe`、`/healthz`；admin 走 SSH 隧道
（`ssh -L 8080:127.0.0.1:8080 server` 后本地 curl）。

### 需要开放的端口

| 端口 | 方向 | 用途 | 是否必须 |
| --- | --- | --- | --- |
| `80/tcp` | 入站 | Let's Encrypt HTTP-01 校验 + 跳转 443 | **必须** |
| `443/tcp` | 入站 | HTTPS（浏览器调用 API、退订页） | **必须** |
| `443/udp` | 入站 | HTTP/3（QUIC）；不开浏览器会自动回退 TCP，只是首次慢一点 | 可选 |
| `8080/tcp` | — | 后端本体，只监听 `127.0.0.1` | **不要对外开** |
| `22/tcp` | 入站 | SSH 运维（admin API 走 `ssh -L` 隧道） | 按需 |

出站需要能访问 `443`（[acme-v02.api.letsencrypt.org](https://acme-v02.api.letsencrypt.org/directory) 签证书）和 `53`（DNS）。

**两处都要放行**：云厂商安全组（华为云 / 阿里云 / AWS 控制台）**和**系统防火墙。

```bash
# Ubuntu / Debian
sudo ufw allow 80,443/tcp && sudo ufw allow 443/udp

# CentOS / RHEL
sudo firewall-cmd --permanent --add-service={http,https} && sudo firewall-cmd --reload
```

两个必须知道的坑：

1. **别把 `8080` 暴露出去。** `docker-compose.yml` 里写的是 `127.0.0.1:8080:8080`，只发布到回环；
   如果改成 `8080:8080`，Docker 会绕过 ufw 的 INPUT 链直接对外暴露，等于 API 裸奔（限流和 admin token 就成了唯一防线）。
2. **Caddy 也跑 Docker 的话**：Caddy 容器发布 `80:80`、`443:443`、`443:443/udp`，后端容器改成
   `expose: 8080` 并放进同一个 docker network，Caddyfile 里写 `reverse_proxy subscribe-api:8080`。

验证（DNS 生效 + 端口放行 + 服务起来后）：

```bash
curl -sS https://subscribe.yuanjianliu.net/healthz     # {"ok":true,...}
```

## 配置项（环境变量 / `.env`）

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `DATA_DIR` | `data` | 数据库目录（Docker 里为 `/data`，已挂卷） |
| `DB_FILE` | `subscribers.db` | 数据库文件名 |
| `ADMIN_TOKEN` | 空 | `/api/admin/*` 的 Bearer Token；空 = 关闭这些接口 |
| `IP_SALT` | 内置默认值 | IP 哈希盐，**务必自定义** |
| `TRUST_PROXY` | `false` | 只有在反向代理后面才设 `true`（否则可伪造 IP） |
| `RATE_LIMIT` / `RATE_WINDOW_SECONDS` | `5` / `600` | 每个 IP 的订阅频率限制 |
| `MAX_BODY_BYTES` | `4096` | 请求体上限 |
| `SITE_URL` | `https://www.yuanjianliu.net` | 无 JS 表单提交后跳回哪个站 |
| `ALLOWED_ORIGINS` | 站点域名 + `localhost:4000` | CORS 白名单，逗号分隔 |
| `HOST` / `PORT` | `127.0.0.1` / `8080` | 监听地址；一般只监听回环，由代理暴露 |

## API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/api/subscribe` | JSON `{"email","source","sb_hp"}`；表单编码也支持（无 JS 降级 → 303 跳转） |
| `GET` | `/api/unsubscribe?token=` | 退订页面（退订链接用的随机串存在库里） |
| `GET` | `/healthz` | `{"ok":true,"active":N,"total":M}` |
| `GET` | `/api/admin/subscribers` | `?status=active|unsubscribed&limit=&offset=` |
| `GET` | `/api/admin/subscribers.csv` | CSV 导出（含退订 token 列） |
| `GET` | `/api/admin/stats` | 汇总统计与来源 Top N |
| `POST` | `/api/admin/unsubscribe` | `{"email":"..."}` |
| `DELETE` | `/api/admin/subscribers?email=` | 物理删除 |

状态码：`201` 新建、`200` 已存在、`400 invalid_email`、`413 payload_too_large`、`429 rate_limited`、`401/404` 鉴权。

## CLI（不依赖 FastAPI）

```bash
python3 cli.py stats
python3 cli.py list --status active --limit 20
python3 cli.py export --out subscribers.csv
python3 cli.py add someone@example.com --source manual
python3 cli.py unsubscribe someone@example.com
python3 cli.py delete someone@example.com --yes
python3 cli.py --db /path/to/subscribers.db stats
```

## 开发与测试

```bash
pip install -r requirements-dev.txt
python -m pytest tests -q                                  # 后端 37 项
python -m unittest tests.test_validate tests.test_store -v # 核心逻辑（无第三方依赖）
python3 -m app                                             # 本地起服务（HOST/PORT 可覆盖）
```

前端脚本（`_includes/subscribe.html` 内联 JS）用渲染后的真实 DOM 验证：

```bash
cd .. && bundle exec jekyll build && npm install --no-save jsdom
node subscribe-server/tests/frontend/verify-subscribe.mjs
```

## 运维

- **备份**：`sqlite3 data/subscribers.db ".backup 'backup-$(date +%F).db'"`，或直接拷 `data/` 目录；
- **日志**：`journalctl -u subscribe-api -f` / `docker logs -f subscribe-api`；
- **多 worker**：限流是进程内的，若要 `--workers > 1`，请把 `ratelimit.py` 换成 Redis 实现；
- **换机器**：拷贝 `data/` + `.env` 即可，DB 是自包含的 SQLite 文件。

## 查看订阅者

`/api/admin/*` **不对外开放**：Caddyfile 只放行 `/api/subscribe`、`/api/unsubscribe`、
`/healthz`，公网访问管理接口会得到 404。所以从下面三种方式里挑。

### 1. 在服务器上直接看（最快）

```bash
cd subscribe-server
docker compose exec subscribe-api python cli.py stats            # 汇总：总数/活跃/退订/近 7、30 天/来源 Top
docker compose exec subscribe-api python cli.py list --limit 20  # 明细：邮箱 + 状态 + 时间 + 来源
docker compose exec subscribe-api python cli.py list --status active
```

### 2. 导出 CSV / 备份

```bash
# 直接打到终端（-T 关掉 TTY，方便重定向到文件）
docker compose exec -T subscribe-api python cli.py export --out - > subscribers-$(date +%F).csv

# 或把整个数据库拷出来
docker compose cp subscribe-api:/data/subscribers.db ./backup-$(date +%F).db
```

CSV 列：`email, status, source, created_at, confirmed_at, unsubscribed_at, unsubscribe_url_token`。
把最后一列拼成 `https://subscribe.yuanjianliu.net/api/unsubscribe?token=<token>`
就是每个人专属的退订链接 —— **将来群发时必须附上**。

### 3. 从自己电脑经 SSH 隧道（不用登服务器改配置）

```bash
ssh -L 8080:127.0.0.1:8080 <你的服务器>
# 另开一个终端，ADMIN_TOKEN 从服务器上的 .env 里取
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://127.0.0.1:8080/api/admin/subscribers | python3 -m json.tool
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://127.0.0.1:8080/api/admin/subscribers.csv -o subscribers.csv
```

### 两个坑

- **别在宿主机上直接 `sqlite3 data/subscribers.db`**：库是 WAL 模式，而宿主机用户对 `data/`
  没有写权限，会报 `attempt to write a readonly database`（连只读查询都不行，因为 SQLite 要建 `-shm`）。
  先 `cp data/subscribers.db` 出来再读（文件是 644，宿主机可读），或者用上面容器内的命令。
- `data/` 已经在 gitignore 里，**不要**把库提交进仓库；备份时记得连 `.env`（含 `ADMIN_TOKEN`）一起备份。

## 故障排查

| 现象 | 原因 |
| --- | --- |
| 容器 `Restarting`，日志 `sqlite3.OperationalError: unable to open database file` | `./data` 的属主不是容器里的 `appuser`(10001)。**Docker 自动创建**的 bind 目录在容器内属于 root，非 root 进程无法写。镜像自带 entrypoint 已会自愈；若你手动 `docker run --user 10001` 绕过 entrypoint，则需 `sudo chown -R 10001:10001 data` |
| `docker compose up` 报 `failed to bind host port 0.0.0.0:80: address already in use` | 80/443 已被宿主机的 Caddy/nginx 占用。要么用宿主机那套，要么先停掉它再 `docker compose --profile tls up -d` |
| 浏览器控制台报 CORS | `ALLOWED_ORIGINS` 没包含访问用的域名（注意 `www.` 与不带 `www.` 是两个 origin） |
| 页面提示 “Something went wrong” | 打开 Network 面板看请求：混合内容（http 调 https 站点）、证书、或服务没起 |
| `429` 太多 | 同一出口 IP（公司/校园网 NAT）多人访问；调大 `RATE_LIMIT` 或调小 `RATE_WINDOW_SECONDS` |
| admin 接口 `404` | `ADMIN_TOKEN` 为空（这是有意的默认关闭）；或请求走了公网 Caddy —— Caddyfile 只放行 `/api/subscribe`、`/api/unsubscribe`、`/healthz` |
| 邮箱没入库但没有报错 | 可能命中蜜罐（机器人）；查日志里的 `honeypot triggered` |
| 容器 `Up (healthy)` 但公网 443 连不上 | 安全组/防火墙没放行 80、443；或 Caddy 没在跑（`systemctl status caddy`） |
