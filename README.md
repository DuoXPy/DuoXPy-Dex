<h1 align="center">
  <a href="https://duoxpy.site">
    <img src="https://github.com/Chromeyc/DuoXPy-Dex/blob/main/images/transparent_banner.png?raw=true" alt="DuoXPy CLI Banner" height="160" />
  </a>
</h1>

<p align="center"><i>The ultimate Duolingo account creator CLI tool with beautiful Rich interface 🚀</i></p>

<p align="center">
  <a href="https://github.com/Chromeyc/DuoXPy-Dex/graphs/contributors">
    <img src="https://img.shields.io/github/contributors-anon/Chromeyc/DuoXPy?style=flat-square">
  </a>
  <a href="./LICENSE">
    <img src="https://img.shields.io/badge/license-Custom-lightgrey.svg?style=flat-square">
  </a>
</p>

<p align="center">
  <a href="https://discord.gg/pu9uDNVMHT">
    <img src="https://img.shields.io/badge/chat-on%20discord-7289da.svg?style=flat-square&logo=discord">
  </a>
  <a href="https://github.com/Chromeyc/DuoXPy">
    <img src="https://img.shields.io/github/stars/Chromeyc/DuoXPy?style=social" alt="GitHub stars">
  </a>
</p>

---

## 🌐 About DuoXPy CLI

**DuoXPy Dex CLI** is a beautiful, feature-rich command-line interface for creating Duolingo accounts using the same methods as DuoXPy. Built with Rich library for stunning visuals and animations!

---

## ⚙️ Setup Instructions

> 💡 **Note**: This tool is for educational purposes only. Use responsibly. And do not Skid or sell it as your product.

1. **Clone the repo**:

```bash
git clone https://github.com/Chromeyc/DuoXPy-Dex.git
cd DuoXPy
```

2. **Install dependencies**:

```bash
pip install -r requirements_cli.txt
```

3. **Set your environment variable**:

Create a `.env` file in the root directory and add your [TempMail.lol](https://tempmail.lol) API key:

```env
TEMPMAIL_API_KEY=your_api_key_here
```

> ⚠️ `TEMPMAIL_API_KEY` must be set in your environment for the tool to work, to get the API Key go to https://tempmail.lol/api

4. **Optional: Configure proxies** (recommended for large batches):

Create a `proxies.txt` file in the root directory and add your SOCKS5 proxies:

```
socks5://username:password@proxy1.example.com:1080
socks5://username:password@proxy2.example.com:1080
```

5. **Run the CLI**:

```bash
python account_creator.py
```

---

## 🚀 Features

### ✨ **Core Features**
* 🚀 **Interactive CLI** with beautiful Rich styling and animations
* 🧵 **Multi-threading support** for faster account creation
* 🔗 **Automatic proxy detection** and rotation
* 📊 **Real-time progress tracking** with live tables
* 🎨 **Stunning visual interface** with colors and emojis
* 🔒 **Random password generation** for each account
* 📧 **Temporary email integration** via TempMail API
* 💾 **Automatic account saving** to JSON files

### 🔧 **Advanced Features**
* ⚡ **SSL certificate handling** for reliable connections
* 🔄 **Retry logic** with intelligent fallback
* 🌐 **Proxy rotation** and automatic failover
* ⏱️ **Rate limit detection** and handling
* 📈 **Success rate optimization** with mixed connections
* 🎯 **Intelligent distribution** (70% proxy, 30% direct)

### 📊 **Progress Tracking**
* ✅ **Completed** accounts with checkmarks
* ❌ **Failed** accounts with error details
* 🔄 **In Progress** accounts with live status
* ⏳ **Pending** accounts waiting to start
* ⏱️ **Rate Limited** accounts with timers
* 🔄 **Retrying** accounts with retry counts

---

## 🎨 Visual Features

### 🌟 **Rich Styling**
* **Beautiful banners** with double borders
* **Color-coded status** indicators
* **Animated progress bars** with spinners
* **Professional tables** with rounded corners
* **Live updates** with smooth animations

### 📋 **Interactive Prompts**
* **Choice-based inputs** with smart defaults
* **Confirmation dialogs** with yes/no prompts
* **Input validation** with helpful error messages
* **Flexible number inputs** (no restrictions)

---

## 🔗 Proxy Support

### 🌐 **Automatic Detection**
* **Loads proxies** from `proxies.txt` automatically
* **Tests proxies** before use
* **Rotates proxies** across accounts
* **Falls back** to direct connection if proxies fail

### 📝 **Proxy Format**
```
socks5://username:password@host:port
```

### 🎯 **Benefits**
* **Avoid rate limits** by distributing requests
* **Bypass IP restrictions** for large batches
* **Improve success rates** with multiple IPs
* **Maintain anonymity** during account creation

---

## 📁 Output Format

Accounts are saved to a JSON file with the following structure:

```json
[
  {
    "_id": "duolingo_user_id",
    "email": "temporary_email@domain.com",
    "password": "generated_password",
    "jwt_token": "jwt_authentication_token",
    "timezone": "Asia/Saigon",
    "username": "generated_username"
  }
]
```

---

## ⚙️ Configuration

### 🔧 **Environment Variables**
* `TEMPMAIL_API_KEY`: Your TempMail API key (required)

### 📄 **Files**
* `proxies.txt`: SOCKS5 proxy list (optional)
* `.env`: Environment variables (optional)

### ⚙️ **Settings**
* **Account count**: 1-100 accounts
* **Multi-threading**: Enabled/disabled for >1 account
* **Delay**: 0-300 seconds between accounts
* **Output file**: Custom JSON filename

---

## 🔧 Troubleshooting

### ❌ **Common Issues**

1. **"TEMPMAIL_API_KEY environment variable is required"**
   - Set up your `.env` file with the API key
   - Get your key from [https://tempmail.lol/](https://tempmail.lol/)

2. **SSL Certificate Errors**
   - Already handled automatically
   - SSL verification is disabled for compatibility

3. **Proxy Connection Issues**
   - Check your proxy format in `proxies.txt`
   - Ensure proxies are working and accessible
   - Tool will fall back to direct connection

4. **Rate Limiting**
   - Use proxies to distribute requests
   - Increase delays between accounts
   - Reduce batch sizes

### 💡 **Performance Tips**

1. **Use proxies** for large batches (>10 accounts)
2. **Enable multi-threading** for faster creation
3. **Monitor progress** with the real-time table
4. **Save frequently** to avoid losing progress

---

## 📈 Success Rates

* **Single-threaded**: ~95% success rate
* **Multi-threaded**: ~90% success rate (with proxies)
* **With proxies**: ~98% success rate
* **Large batches**: ~85% success rate (10+ accounts)

---

## 🔒 Security Features

* **Random passwords** for each account
* **Temporary emails** for verification
* **Proxy rotation** for IP diversity
* **SSL handling** for secure connections
* **No data logging** or storage

---

## 🎯 Account Creation Process

1. **Create unclaimed account** via Duolingo API
2. **Generate temporary email** via TempMail
3. **Claim account** with email and credentials
4. **Complete initial lesson** for XP (makes it undetected)
5. **Farm XP from stories** for bonus points
6. **Save account details** to JSON file

---

## 🧪 Development

Built using:

* 🐍 **Python 3.11**
* 🎨 **Rich** - Beautiful terminal interface
* 📧 **TempMail** - Temporary email service
* 🔗 **aiohttp** - Async HTTP client
* 🌐 **aiohttp-socks** - Proxy support

---

## 🎉 What's New

### Version 2.0 - Rich & Proxies
* ✨ **Rich library integration** for stunning visuals
* 🔗 **Automatic proxy detection** and rotation
* 📊 **Real-time progress tables** with live updates
* 🎨 **Beautiful animations** and color coding
* ⚡ **Improved performance** with better async handling
* 🔄 **Enhanced retry logic** for reliability

---

## 💬 Community

Got questions or ideas? Join us on Discord:
[![Discord](https://img.shields.io/badge/discord-join%20now-7289da?style=for-the-badge\&logo=discord)](https://discord.gg/pu9uDNVMHT)

---

## 📜 License

This project is licensed under the [DuoXPy License](./LICENSE).
**Commercial use is strictly prohibited.**

---

<p align="center">
  <i>Created with ❤️ by <a href="https://github.com/Chromeyc">smh (Chromeyc)</a> & <a href="https://github.com/oxGorou">oxGorou</a></i>
</p> 
