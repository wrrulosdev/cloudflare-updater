# 🌩️ Cloudflare Dynamic DNS Updater

Automatically updates your public IP address in your Cloudflare DNS records using their API.  
Perfect for dynamic IP setups (like home networks) where your domain must always point to the correct IP.

---

## 📦 Features

✅ Automatically updates `A` DNS record on Cloudflare  
✅ Detects changes in your public IP address  
✅ Detailed logging to console and file  
✅ Auto-retry on failure  
✅ Simple configuration via environment variables  

---

## ⚙️ Requirements

- Python 3.8 or higher  
- Cloudflare account  
- A domain managed by Cloudflare  
- An API token with DNS edit permissions  

---

## 📁 Installation

```bash
git clone https://github.com/wrrulosdev/cloudflare-updater.git
cd cloudflare-updater
pip install -r requirements.txt
```

---

## 🔐 Required Environment Variables

The script uses environment variables for security and flexibility:

| Variable       | Description                                           |
|----------------|-------------------------------------------------------|
| `API_TOKEN`    | Your Cloudflare API token                            |
| `ZONE_ID`      | DNS zone ID of your domain                           |
| `RECORD_NAME`  | Full subdomain name (e.g. `home.example.com`)        |

Set them in your terminal session:

```env
export API_TOKEN="your_api_token"
export ZONE_ID="your_zone_id"
export RECORD_NAME="subdomain.yourdomain.com"
```

Or store them in a `.env` file and load with `python-dotenv`.

---

## 🚀 Usage

Simply run the script:

```bash
python cloudflare_updater.py
```

The script will:

1. Get your current public IP  
2. Compare it with the last known IP  
3. If changed, update the DNS record on Cloudflare  
4. Repeat every 2 minutes ⏱️  

---

## 📄 Logging

📝 All events are logged to:

- `cloudflare_update.log` (file)  
- Console (real-time output)

## 💡 Practical Use Case

You have a home server or IP camera you want to access via:

```bash
https://home.yourdomain.com
```

With this script and a router port forward, your domain will always point to your latest IP 🎯.

---

## 🔒 Security

- Your API Token **must have minimal permissions** to edit DNS in the specific zone  
- **Never share your token.** Use `.env` files or secret managers

---

## 📜 License

MIT License — Free to use, modify, and distribute with attribution.
