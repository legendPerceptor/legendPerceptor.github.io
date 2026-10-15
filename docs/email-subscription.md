# 邮件订阅功能设计方案

> 状态：已实现（前端模块 + 自托管后端），前端已放在首页。
> 相关文件：`_includes/subscribe.html`、`_sass/layout/subscribe.scss`、`_config.yml`、`subscribe-server/`。

## 1. 目标与约束

| 需求 | 设计响应 |
| --- | --- |
| 用户填邮箱 + 点订阅按钮 | 一个可复用的 Liquid 模块（HTML + CSS + 渐进增强 JS） |
| UI 可以放在网页任何地方 | `{% include subscribe.html %}` 一行即可，任意 layout / 页面 / 文章 / tab |
| 目前先放首页 | 已加在 `_layouts/home.html` 的 intro 之后 |
| 已订阅邮箱存在“当前的服务器” | 自托管 API 服务 + 单个 SQLite 文件，数据完全在自己手里 |
| 先做单次提交 | 第一版不要求确认邮件；表结构已预留 `confirmed_at`，后续可平滑升级为双重确认 |

**关键约束：** 本站是 Jekyll 静态站，通过 GitHub Actions 发布到 GitHub Pages（`www.yuanjianliu.net`）。
GitHub Pages 只能托管静态文件，**不能运行后端代码**，也无法写入数据库。因此“存储”必须放在你自己的机器上
（VPS / NAS / 家里的小主机），静态页面通过 HTTPS 跨域调用它。这是本方案与“把邮箱写进仓库文件”类方案最大的区别：
邮箱不会出现在 Git 历史里，也不会被任何人通过仓库读到。

## 2. 总体架构

```
  访客浏览器 (www.yuanjianliu.net, GitHub Pages, 静态)
        │
        │ 1. 提交邮箱  POST https://subscribe.yuanjianliu.net/api/subscribe  (JSON, CORS)
        ▼
  Caddy / nginx  ──  TLS 终止 + 反向代理 + 只暴露公开路径
        │  http://127.0.0.1:8080
        ▼
  subscribe-server (FastAPI + uvicorn, 单进程)
        │  校验 / 限流 / 蜜罐 / IP 哈希
        ▼
  data/subscribers.db  (SQLite, WAL)   ← 备份就是拷贝这一个文件
        │
        └─ 运维：CLI 导出 CSV、退订、删除；HTTPS 只读 admin API（Bearer Token）
```

数据流（一次成功订阅）：

1. 前端做一次格式校验，然后 `fetch` 提交 `{email, source, sb_hp}`；
2. 后端按 `ip_hash` 限流（默认 10 分钟 5 次），检查蜜罐字段，规范化邮箱；
3. 写入 SQLite（`email` 上有 UNIQUE 索引 → 天然去重），生成一个 `token` 用于将来的退订链接；
4. 返回 `201 subscribed` / `200 already_subscribed`，前端就地显示英文提示，不刷新页面。

## 3. 前端模块

### 3.1 放在哪里

模块就是 `_includes/subscribe.html`，一行 include，位置随你：

```liquid
{% include subscribe.html %}
```

| 想放的位置 | 做法 |
| --- | --- |
| 首页（当前） | `_layouts/home.html` 中 `<div class="content">` 之后 |
| 任意页面 / 文章 | 在 `.md` 正文里直接写 `{% include subscribe.html %}` |
| 侧边栏 | 在 `_includes/sidebar.html` 里插入 |
| 独立订阅页 | 新建 `_tabs/subscribe.md`，写一行 include，加进 `_data/contact.yml` 或导航 |

一句话可以覆盖默认文案：

```liquid
{% include subscribe.html
   title="Follow the newsletter"
   description="One email per post, nothing else."
   button_text="Join"
   layout="inline" %}
```

支持的参数：`endpoint`、`title`、`description`、`placeholder`、`button_text`、`note`、`source`、`layout`（`card` 卡片 / `inline` 无边框）。
未传的参数回落到 `_config.yml` 的 `subscribe:` 节点。

### 3.2 配置（`_config.yml`）

```yaml
subscribe:
  enabled: true
  endpoint: "https://subscribe.yuanjianliu.net/api/subscribe"  # 后端地址
  title / description / placeholder / button_text / note: 文案
  messages:                      # 所有提示语都可改，不需要动代码
    sending / ok / exists / invalid / ratelimited / error
```

- `endpoint` 留空或 `enabled: false` → 整站不渲染模块（避免上线一个坏表单）；
- 本地 `jekyll serve` 时若 `endpoint` 为空，会渲染一个黄色提示框告诉你还没配置。

### 3.3 交互与健壮性

- 正则先做客户端校验，非法邮箱不发请求；
- 提交中按钮禁用并显示 “Subscribing…”，12 秒超时（`AbortController`）；
- 服务端状态映射：`201` → 成功、`200 already_subscribed` → “你已在列表中”、`429` → 稍后再试、`400/422` → 显示服务端文案、其它/网络异常 → 通用错误；
- 提示语放在 `aria-live="polite"` 区域，屏幕阅读器可播报；
- 多实例安全：脚本用 `window.__chirpySubscribe` 幂等标记 + 事件委托，一页放多个模块也只初始化一次；
- **无 JS 也能用**：`<form action method="post">` 会以 `application/x-www-form-urlencoded` 提交，后端返回 `303` 跳回首页（`/?subscribed=ok`）；
- 蜜罐字段 `.subscribe-hp` 视觉隐藏，机器人填了就假装成功、不入库；
- 样式用主题现有的 CSS 变量（`--card-bg`、`--text-muted-color` 等），自动适配明暗两种模式；按钮在两种模式下都是品牌深红 + 白字，保证对比度。

## 4. 后端 API 契约

服务代码在 `subscribe-server/`（FastAPI + SQLite，无需数据库服务）。

| 方法 | 路径 | 鉴权 | 说明 |
| --- | --- | --- | --- |
| `POST` | `/api/subscribe` | 公开（CORS 白名单） | 订阅 |
| `GET` | `/api/unsubscribe?token=` | 公开 | 一键退订（HTML 页面） |
| `GET` | `/healthz` | 公开 | 健康检查 |
| `GET` | `/api/admin/subscribers` | Bearer | 分页列表 `?status=&limit=&offset=` |
| `GET` | `/api/admin/subscribers.csv` | Bearer | 导出 CSV（可直接导进邮件群发工具） |
| `GET` | `/api/admin/stats` | Bearer | 总数 / 活跃 / 退订 / 近 7、30 天增量 / 来源 Top N |
| `POST` | `/api/admin/unsubscribe` | Bearer | 标记退订 `{"email": "..."}` |
| `DELETE` | `/api/admin/subscribers?email=` | Bearer | 物理删除（GDPR 删除请求） |

请求 / 响应示例：

```bash
# 订阅
curl -i https://subscribe.yuanjianliu.net/api/subscribe \
  -H 'Content-Type: application/json' \
  -d '{"email":"someone@example.com","source":"/"}'
# HTTP/1.1 201 Created
# {"ok":true,"status":"subscribed","created":true,"message":"You are on the list."}

# 重复订阅（幂等，不报错）
# HTTP/1.1 200 OK
# {"ok":true,"status":"already_subscribed","created":false,...}

# 非法邮箱
# HTTP/1.1 400 Bad Request
# {"ok":false,"error":"invalid_email","message":"Please enter a valid email address."}

# 触发限流
# HTTP/1.1 429 Too Many Requests, Retry-After: <秒>

# 导出
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://subscribe.yuanjianliu.net/api/admin/subscribers.csv
```

错误码：`invalid_email`(400)、`rate_limited`(429)、`payload_too_large`(413)、`invalid_token`(404，退订链接无效)、`not_found`(404，管理端)。

## 5. 数据模型

```sql
CREATE TABLE subscribers (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  email            TEXT NOT NULL COLLATE NOCASE,   -- 已规范化（小写、去空白）
  status           TEXT NOT NULL DEFAULT 'active', -- active | unsubscribed
  source           TEXT,                           -- 从哪个页面订阅的（page.url）
  ip_hash          TEXT,                           -- sha256(salt + ip)[:32]，不存明文 IP
  user_agent       TEXT,
  token            TEXT NOT NULL,                  -- 退订链接用的一次性随机串
  created_at       TEXT NOT NULL,                  -- ISO-8601 UTC
  confirmed_at     TEXT,                           -- 预留给双重确认
  unsubscribed_at  TEXT,
  updated_at       TEXT NOT NULL
);
CREATE UNIQUE INDEX idx_subscribers_email ON subscribers (email);
```

设计要点：

- **去重**：`email` 唯一索引，重复提交返回 `already_subscribed` 而不是报错；
- **退订后再订阅**：会重新激活同一条记录并保留原 `token`（用户明确又点了一次订阅）；
- **隐私最小化**：只存邮箱 + 来源 + 时间；IP 只存加盐哈希（`IP_SALT`），无法反查；
- **可移植**：单个 SQLite 文件（WAL 模式），备份 = `cp subscribers.db`；不引入 Postgres/MySQL。

## 6. 安全与防滥用

| 面向 | 措施 |
| --- | --- |
| 跨域 | CORS 白名单只允许 `https://www.yuanjianliu.net` 与 `https://legendperceptor.github.io`（含本地 4000 端口） |
| 刷接口 | 按 IP 哈希滑动窗口限流（默认 5 次 / 10 分钟，可配），返回 `429 + Retry-After` |
| 机器人 | 隐藏蜜罐字段，命中即假装成功、不入库 |
| 伪装 IP | `TRUST_PROXY=true` 时才读 `X-Forwarded-For`，且只在反向代理后开启 |
| 管理接口 | 默认关闭；设置 `ADMIN_TOKEN` 后用 `Authorization: Bearer` + 常量时间比较；Caddy 里只公开 `/api/subscribe` 等路径，admin 走 SSH 隧道 |
| 传输 | 必须 HTTPS（Caddy 自动申请证书）。HTTP 页面会被浏览器按混合内容拦截 |
| 请求体积 | 默认最大 4 KB，超过返回 413 |
| 服务进程 | systemd 单元已开 `NoNewPrivileges`、`ProtectSystem=strict` 等加固；Docker 里以非 root 用户运行 |

## 7. 部署

完整步骤见 [`subscribe-server/README.md`](../subscribe-server/README.md)。核心三步：

1. **DNS**：给 `subscribe.yuanjianliu.net` 加一条 A/AAAA 记录指向服务器（和 GitHub Pages 的 `www` 记录不冲突）；
2. **跑服务**（二选一）
   - Docker：`cd subscribe-server && cp .env.example .env`（填 `ADMIN_TOKEN`、`IP_SALT`）`&& docker compose up -d --build`；
   - systemd：venv 装 `requirements.txt`，改好 `deploy/subscribe-api.service` 的路径与用户，`systemctl enable --now subscribe-api`；
3. **HTTPS**（二选一，都会占 80/443，不能同时跑）：
   - 宿主机 Caddy：把 `deploy/Caddyfile` 放到 `/etc/caddy/Caddyfile`，`systemctl restart caddy`；
   - Docker Caddy：`docker compose --profile tls up -d`（不需要 apt/sudo）。
   同一份 Caddyfile 通过 `SUBSCRIBE_UPSTREAM` 环境变量适配两种上游。
4. **放行端口**：安全组 + 系统防火墙都要开 `80/tcp`、`443/tcp`（可选 `443/udp` 给 HTTP/3）；
   后端监听的 `8080` 只走回环、**不要**对外开。出站需允许 `443`（Let's Encrypt 签证书）与 `53`（DNS）。
   详见 [`subscribe-server/README.md`](../subscribe-server/README.md#需要开放的端口)。

验证：

```bash
curl -sS https://subscribe.yuanjianliu.net/healthz
curl -sS -i -X POST https://subscribe.yuanjianliu.net/api/subscribe \
  -H 'Content-Type: application/json' -d '{"email":"you@example.com"}'
cd subscribe-server && python3 cli.py stats     # 确认入库
```

## 8. 运维

```bash
# 查看/导出（无需 HTTP，直接读库）
python3 cli.py stats
python3 cli.py list --status active --limit 20
python3 cli.py export --out subscribers.csv

# 退订 / 删除
python3 cli.py unsubscribe someone@example.com
python3 cli.py delete someone@example.com --yes

# 备份（WAL 模式下建议用 sqlite3 的在线备份）
sqlite3 data/subscribers.db ".backup 'backup-$(date +%F).db'"
```

- 日志：uvicorn 输出到 journald / `docker logs`，会记录每次订阅的 `created/existing` 与来源（不记录邮箱明文？会记录，属正常运维需要，注意日志权限）；
- 监控：`/healthz` 返回活跃订阅数，可挂到 Uptime Kuma 之类；
- 迁移：换机器只需拷贝 `data/` 目录 + `.env`。

## 9. 测试

```bash
cd subscribe-server
pip install -r requirements-dev.txt
python -m pytest tests -q          # 37 项：邮箱校验、SQLite、限流、API、CORS、admin、退订
python -m unittest tests.test_validate tests.test_store   # 不装 FastAPI 也能跑核心逻辑

# 前端（渲染后的真实 DOM，jsdom）
cd .. && bundle exec jekyll build
npm install --no-save jsdom
node subscribe-server/tests/frontend/verify-subscribe.mjs  # 18 项：校验/成功/重复/限流/网络错误/honeypot
```

已实测通过：后端 37 项、前端 18 项、真实 HTTP 冒烟（订阅/重复/非法/限流/表单降级/退订链接/admin CSV）。

## 10. 后续路线图

1. **双重确认（double opt-in）**：订阅后发一封确认邮件（Resend / SES / 自建 SMTP），点击 `/api/confirm?token=` 才把 `confirmed_at` 写上、`status` 置为 `active`。表结构已预留字段，前端无需改动。
2. **发信**：`status = 'active'` 的导出行直接喂给邮件服务；新文章发布时在 GitHub Actions 里触发群发，退订链接用现成的 `token`。
3. **统计**：把 `source` 聚合起来看哪篇文章带来最多订阅（`/api/admin/stats` 已给出 Top 来源）。
4. **合规**：如果订阅量变大或面向欧盟用户，补上隐私政策页与“仅用于发新文章”的说明（当前模块底部已有一行说明文案）。

## 11. 与“纯静态”替代方案对比

| 方案 | 邮箱存在哪 | 需要自己的服务器 | 评价 |
| --- | --- | --- | --- |
| **本方案**（自托管 API + SQLite） | 自己的机器 | 是 | 数据自主、零第三方费用、可扩展为发信系统 |
| Buttondown / Mailchimp | 第三方 | 否 | 最省事，但数据在别人手里、免费额度有限 |
| Cloudflare Workers + D1/KV | Cloudflare | 否 | 免运维，但绑定平台、需要额外账号 |
| GitHub Actions + 私有仓库/Issue | GitHub 仓库 | 否 | 零成本，但写入有延迟、GitHub API 限流，适合极小规模 |
