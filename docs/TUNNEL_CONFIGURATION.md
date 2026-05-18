# BarkMind — Tunnel Configuration

**Date:** 2026-05-17

---

## Active Tunnel

| Property | Value |
|---|---|
| Name | `reselleros` |
| UUID | `82b66414-9142-442e-bded-bb7fc70d7b4c` |
| Config | `~/.cloudflared/config.yml` |
| Service | `cloudflared.service` (systemd, root) |
| Credentials | `~/.cloudflared/82b66414-9142-442e-bded-bb7fc70d7b4c.json` |

---

## Ingress Configuration

BarkMind rules added at position 17-18 in `~/.cloudflared/config.yml`:

```yaml
  # ── BarkMind — doctrine: frontend 3008, backend 8108 ─────────────────────
  # Canine behavioral intelligence platform
  # Ports 8107/3007 reserved by Aegis Lite
  - hostname: barkmind.jesseboudreau.com
    service: http://127.0.0.1:3008

  - hostname: barkmind-api.jesseboudreau.com
    service: http://127.0.0.1:8108

  - service: http_status:404
```

The catch-all `http_status:404` must always be the LAST rule.

---

## DNS Records

| Hostname | Type | Target | Proxy |
|---|---|---|---|
| `barkmind.jesseboudreau.com` | CNAME | `82b66414...cfargotunnel.com` | ✓ Proxied |
| `barkmind-api.jesseboudreau.com` | CNAME | `82b66414...cfargotunnel.com` | ✓ Proxied |

DNS resolution returns Cloudflare's anycast IPs (172.67.139.93, 104.21.57.5) when queried externally — this is expected behavior for proxied CNAMEs.

---

## Process Architecture

```
cloudflared.service (PID: new on each restart)
  ├── Running as: root
  ├── Config: /home/jesse/.cloudflared/config.yml
  └── Connected to Cloudflare edge: 4 connections (EWR region)
```

### Critical: User-Level vs Systemd

**Problem identified during deployment:** A user-level cloudflared process (`cloudflared tunnel run reselleros`) can exist alongside the systemd service. When both connect to the same tunnel, traffic is distributed between them. The old process uses its startup-time config; config file edits don't apply until it's restarted.

**Resolution:** The systemd service (`cloudflared.service`) is now the **sole authority**. It is enabled for reboot persistence. Any user-level cloudflared processes must be killed to prevent config divergence.

To verify only one cloudflared instance is routing:
```bash
ps aux | grep cloudflared | grep -v grep
# Should show only: root ... cloudflared --no-autoupdate --config ~/.cloudflared/config.yml tunnel run
```

---

## Lifecycle Management

```bash
# Reload new config (requires full restart — cloudflared has no SIGHUP reload)
sudo systemctl restart cloudflared

# Check status
sudo systemctl status cloudflared

# View logs
sudo journalctl -u cloudflared -f

# Validate config before restart
cloudflared --config ~/.cloudflared/config.yml tunnel ingress validate

# Test ingress rule matching locally
cloudflared --config ~/.cloudflared/config.yml tunnel ingress rule https://barkmind.jesseboudreau.com

# Live tunnel metrics
curl -sf http://127.0.0.1:20242/metrics | grep "tunnel_total_requests"
```

---

## Adding Future Services

To add a new service to the `reselleros` tunnel:

1. Add ingress rules to `~/.cloudflared/config.yml` before the catch-all:
```yaml
  - hostname: newapp.jesseboudreau.com
    service: http://127.0.0.1:PORT
```

2. Create DNS record:
```bash
cloudflared tunnel route dns reselleros newapp.jesseboudreau.com
```

3. Validate config:
```bash
cloudflared --config ~/.cloudflared/config.yml tunnel ingress validate
```

4. Restart:
```bash
sudo systemctl restart cloudflared
```

---

## Port Doctrine

| App | Frontend Port | Backend Port |
|---|---|---|
| BarkMind | 3008 | 8108 |
| Aegis Lite | 3007 | 8107 |
| Aegis AI | 3002 | 8102 |
| ResellerOS | 3001 | 8101 |

Ports 8107/3007 are **reserved by Aegis Lite** and must not be used by BarkMind.
