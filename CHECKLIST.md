# ✅ YOUR CHECKLIST - Do These 4 Things

## 📝 1. Add Your OpenAI API Key (2 minutes)

**Get API Key:**
- Go to: https://platform.openai.com/api-keys
- Click "Create new secret key"
- Copy it (starts with `sk-`)

**Add to .env file:**
```bash
nano .env
```

Find this line:
```
LLM_API_KEY=your_api_key_here
```

Change to:
```
LLM_API_KEY=sk-YOUR-ACTUAL-KEY-HERE
```

Save: `Ctrl+X`, then `Y`, then `Enter`

---

## 🐳 2. Build and Start Docker (5 minutes)

Run this one command:
```bash
./run_me.sh
```

This will:
- ✅ Build Docker image
- ✅ Start the server
- ✅ Show you the logs

**Wait for these messages:**
- ✅ "Initialized embedding system with openai provider"
- ✅ "All components initialized successfully"

---

## ⚙️ 3. Configure Cursor (2 minutes)

**Open Cursor Settings:**
- Mac: `Cmd + ,`
- Windows: `Ctrl + ,`

**Search for:** `MCP`

**Add this config:**
```json
{
  "mcpServers": {
    "codebase-analyser": {
      "url": "http://localhost:8050/sse",
      "transport": {
        "type": "sse"
      }
    }
  }
}
```

**Restart Cursor**

---

## 🎯 4. Test with jolly-sections (5 minutes)

**In Cursor, type:**

```
Analyze the jolly-commerce/jolly-sections repository
```

**Wait 2-5 minutes for first analysis**

**Then ask:**
```
I want to add a hero section with call-to-action buttons. 
Which section from jolly-commerce/jolly-sections should I use?
```

**You'll get a recommendation like:**
```
Best match: src/sections/HeroSection.tsx
Reasoning: This section implements...
How to use: You can customize by...
```

---

## 🎉 THAT'S IT!

You now have an AI-powered codebase analyzer!

**More questions to try:**
- "What pricing sections are available in jolly-sections?"
- "Show me all form components in jolly-sections"
- "Find the best testimonial section in jolly-sections"

---

## 🆘 If Something Goes Wrong

**Server not starting?**
```bash
docker-compose logs
```

**Need to restart?**
```bash
docker-compose restart
```

**Want to start fresh?**
```bash
docker-compose down
docker-compose up -d
```

**Check if running:**
```bash
docker-compose ps
```

---

## 📚 More Help

- **Detailed guide:** `START_HERE.md`
- **Full docs:** `README.md`
- **Quick start:** `QUICKSTART.md`

