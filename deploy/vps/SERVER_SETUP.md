# WES OS — VPS Server Preparation (Ubuntu 24.04)

This toolkit **prepares** a fresh Ubuntu 24.04 server to host WES OS. It installs
and configures the full runtime stack but **does not deploy the WES application** —
that is a separate step. Everything is idempotent (safe to re-run) and the
bootstrap ends with a runtime verification pass.

> **Note on where this was produced:** these artifacts were authored and
> statically verified on a workstation. All *runtime* verification (service
> installs, containers, health checks) happens **on the VPS** when you run
> `bootstrap.sh` there — the script self-verifies via `verify.sh` at the end.

## What it installs & configures

| Requirement            | How it's provided |
|------------------------|-------------------|
| Docker + Compose       | Official Docker apt repo (`docker-ce`, `docker-compose-plugin`) |
| Docker Network         | Dedicated bridge `wes-net` |
| Git                    | apt |
| PostgreSQL             | `postgres:16` container on `wes-net`, DB `wes_os`/user `wes`, loopback-only |
| Redis                  | `redis:7` container (AOF + RDB), loopback-only |
| Nginx Reverse Proxy    | `/api` → `127.0.0.1:8000`, static `/`, `/healthz`, HTTPS-ready |
| HTTPS Ready            | Certbot installed; `certbot --nginx -d <domain>` adds TLS |
| UFW Firewall           | deny incoming; allow SSH/80/443 |
| Fail2ban               | `sshd` + nginx jails |
| Certbot                | apt |
| Python                 | `python3` + venv + pip (Ubuntu 24.04 ships 3.12) |
| Node.js                | NodeSource 20.x (`NODE_MAJOR` overridable) |
| Auto Restart           | Docker `restart: unless-stopped` + `wes-infra.service` (boot) |
| Systemd Services       | `wes-infra`, `wes-backup.timer`, `wes-healthcheck.timer` |
| Log Rotation           | `/etc/logrotate.d/wes` → `/opt/logs/*.log`, 14d, compressed |
| Backup Scripts         | `/opt/wes/backup.sh` (pg_dump + Redis RDB, retention) daily 02:30 |
| Monitoring / Health    | `/opt/wes/healthcheck.sh` every 5 min → `/opt/logs/health.log` |
| Folders                | `/opt/wes`, `/opt/backups`, `/opt/logs` |

## Run it

Copy this `deploy/vps` directory to the server, then:

```bash
sudo WES_DOMAIN=wes.example.com WES_ADMIN_EMAIL=you@example.com \
     bash deploy/vps/bootstrap.sh
```

Optional overrides: `NODE_MAJOR`, `WES_SSH_PORT`.

The run creates `/opt/wes/.env` with **freshly generated, host-unique secrets**
(DB password, JWT secret, app secret — `chmod 600`). Re-running preserves them.

## Verify at any time

```bash
sudo bash /opt/wes/verify.sh
```

Checks toolchain versions, systemd service/timer state, the `wes-net` network,
Postgres/Redis container health + connectivity, Nginx config + `/healthz`, UFW,
and the folder layout. Non-zero exit if any required check fails.

## Enable HTTPS (after DNS points at the host)

```bash
sudo certbot --nginx -d wes.example.com
```

Certbot adds the `443` server block and an 80→443 redirect, and installs an
auto-renew timer.

## Backups

- Runs daily at 02:30 via `wes-backup.timer`.
- PostgreSQL: `pg_dump | gzip` → `/opt/backups/postgres/`.
- Redis: `SAVE` + copy `dump.rdb` → `/opt/backups/redis/`.
- Retention: `WES_BACKUP_RETENTION_DAYS` (default 14).
- Manual run: `sudo /opt/wes/backup.sh`.
- Restore Postgres: `gunzip -c <dump>.sql.gz | docker exec -i wes-postgres psql -U wes -d wes_os`.

## Monitoring

`wes-healthcheck.timer` runs `/opt/wes/healthcheck.sh` every 5 minutes, appending
a status line to `/opt/logs/health.log` and failing the unit (visible in
`systemctl status wes-healthcheck` / journald) if Docker, Nginx, Fail2ban,
Postgres, Redis, the HTTP endpoint, or disk (<90%) are unhealthy.

## Security posture

- Postgres/Redis bind to `127.0.0.1` only — never publicly exposed.
- UFW default-deny inbound; only SSH/80/443 open.
- Fail2ban bans brute-force SSH + abusive HTTP.
- `.env` is `chmod 600`; secrets are per-host random.
- WES app's own rate limiting + refresh rotation + audit log (WP5) apply once deployed.

## Deploying WES OS later (not done by this toolkit)

1. Clone the repo into `/opt/wes/app`.
2. Build the frontend; point Nginx `root` at the built `dist` (replace `/opt/wes/www`).
3. Run the backend (container or systemd) on `127.0.0.1:8000` using `/opt/wes/.env`
   (`WES_DATABASE_URL`, `WES_REDIS`/`REDIS_URL`, `WES_JWT_SECRET`, `WES_SECRET_KEY`).
4. `sudo bash /opt/wes/verify.sh` and confirm the app health endpoint.

## Files

```
deploy/vps/
├── bootstrap.sh                 # one-command server preparation (idempotent)
├── verify.sh                    # runtime verification / health checks
├── SERVER_SETUP.md              # this document
├── config/
│   ├── docker-compose.infra.yml # Postgres + Redis on wes-net
│   ├── wes.env.example          # env template (secrets filled at bootstrap)
│   ├── nginx-wes.conf           # reverse proxy (HTTPS-ready)
│   ├── maintenance.html         # holding page until WES is deployed
│   ├── fail2ban-jail.local      # sshd + nginx jails
│   ├── logrotate-wes            # /opt/logs rotation
│   └── systemd/                 # wes-infra + backup/healthcheck service+timer
└── scripts/
    ├── backup.sh                # pg_dump + redis snapshot + retention
    └── healthcheck.sh           # monitoring probe
```
