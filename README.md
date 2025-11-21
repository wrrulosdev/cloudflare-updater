# 🌩️ Cloudflare Dynamic DNS Updater (Multi-Account Version)

Automatically updates your public IP address across **multiple Cloudflare DNS records** — even across **different accounts or zones** — using the Cloudflare API.  
Perfect for dynamic IP setups (home networks, small servers, labs, etc.) where several domains or subdomains must always point to your current IP.

---

## 📦 Features

✅ Supports **multiple records and accounts** simultaneously  
✅ Automatically updates `A` DNS records on Cloudflare  
✅ Detects public IP changes automatically  
✅ Detailed logging to console and file  
✅ Auto-retry on failure or connection error  
✅ Environment-variable-based configuration (secure and portable)  

---

## ⚙️ Requirements

- Python 3.8 or higher  
- Cloudflare account(s)  
- At least one domain managed by Cloudflare  
- API token(s) with **DNS edit** permissions  

---

## 📁 Installation

```bash
git clone https://github.com/wrrulosdev/cloudflare-updater.git
cd cloudflare-updater
pip install -r requirements.txt
```

---

## 🔐 Environment Variables

This version supports **multiple records**, even from **different Cloudflare accounts**.  
You can define them as numbered environment variables:

| Variable            | Description                                                      |
|---------------------|------------------------------------------------------------------|
| `API_TOKEN_1`       | API token for record #1                                          |
| `ZONE_ID_1`         | Zone ID for record #1                                            |
| `RECORD_NAME_1`     | Full subdomain for record #1 (e.g., `home.example.com`)          |
| `PROXIED_1`         | Whether Cloudflare proxy is enabled for record #1 (`true`/`false`) |
| `API_TOKEN_2`       | API token for record #2 (optional)                              |
| `ZONE_ID_2`         | Zone ID for record #2 (optional)                                |
| `RECORD_NAME_2`     | Full subdomain for record #2 (optional)                         |
| `PROXIED_2`         | Whether Cloudflare proxy is enabled for record #2 (`true`/`false`) |

You can add as many as you need: `_3`, `_4`, `_5`, etc., following the same pattern.

If only one set is defined (`API_TOKEN`, `ZONE_ID`, `RECORD_NAME`), the script will run in **single-record mode** for backward compatibility, and `PROXIED` can be optionally specified (default is `true`).

Example `.env` file:

```env
API_TOKEN_1=your_first_api_token
ZONE_ID_1=your_first_zone_id
RECORD_NAME_1=sub1.yourdomain.com
PROXIED_1=true

API_TOKEN_2=your_second_api_token
ZONE_ID_2=your_second_zone_id
RECORD_NAME_2=sub2.otherdomain.net
PROXIED_2=false
```

---

## 🚀 Usage

Run the script manually or via cron/systemd:

```bash
python cloudflare_updater.py
```

The script will:

1. Get your current public IP  
2. Compare it with the last known IP  
3. If changed, update all DNS records defined in your environment  
4. Repeat every 2 minutes ⏱️  

---

## 📄 Logging

📝 All actions are logged to:

- `cloudflare_update.log` (file)  
- Console (real-time output)

Each record and account is logged separately for clarity.

---

## 💡 Example Use Case

You host several services at home:

- `home.example.com` → Your NAS  
- `cam.example.net` → Your security camera  
- `vpn.mydomain.org` → Your VPN endpoint  

When your IP changes, all three stay perfectly in sync.

---

## 🔒 Security

- API tokens should have **minimum required permissions** (edit DNS in the target zone only).  
- **Never share your token** — use `.env` files or secret managers.  

---

## 📜 License

MIT License — Free to use, modify, and distribute with attribution.
