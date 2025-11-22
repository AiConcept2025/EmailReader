# EmailReader Program Modes - Quick Reference

## Which Mode Does What?

### Mode 1: "default_mode" 🤖

**Enables:** Pinecone + Flowise (AI document analysis)

**What it does:**
- Processes documents from Google Drive
- Uploads to vector database (Pinecone OR FlowiseAI)
- Creates AI predictions and insights
- Enables Q&A over documents

**Use when:**
- You want AI-powered document analysis
- Building a searchable knowledge base
- Need document insights and predictions

**Config:**
```json
{
  "app": {
    "program": "default_mode"
  },
  "use_pinecone": false,  // true = Pinecone, false = FlowiseAI
  "flowise": { ... }
}
```

---

### Mode 2: "translator" 📄

**Disables:** Pinecone and Flowise (translation only)

**What it does:**
- Converts files to DOCX (if needed)
- Translates using Google Cloud Translation
- Uploads to Completed folder
- Sends webhook to external server

**Use when:**
- You only need document translation
- Integration with external systems
- High-volume translation pipeline
- Don't need AI analysis

**Config:**
```json
{
  "app": {
    "program": "translator",
    "translator_url": "http://your-server/submit"
  }
}
```

---

## How to Switch Modes

**Edit your config file:**
- Development: `credentials/config.dev.json`
- Production: `credentials/config.prod.json`

**Change the program setting:**
```json
{
  "app": {
    "program": "default_mode"  // or "translator"
  }
}
```

**Restart the application.**

---

## Pinecone vs FlowiseAI (in default_mode)

**To use Pinecone:**
```json
{
  "use_pinecone": true,
  "pinecone": {
    "api_key": "your_pinecone_api_key"
  }
}
```

**To use FlowiseAI:**
```json
{
  "use_pinecone": false,  // or omit this line
  "flowise": {
    "api_url": "...",
    "api_key": "...",
    "doc_store_id": "..."
  }
}
```

**Note:** Pinecone is marked as deprecated in code. FlowiseAI is recommended.

---

## Current Status (November 22, 2025)

✅ **Configuration bug FIXED**
✅ **Both modes working correctly**
⚠️ **Pinecone incomplete** (only upload implemented)
⚠️ **`use_pinecone` flag missing** from config files (defaults to false)

---

## Quick Decision Tree

```
Need AI document analysis?
├─ YES → Use "default_mode"
│   └─ Which vector store?
│       ├─ Pinecone → Set use_pinecone: true
│       └─ FlowiseAI → Set use_pinecone: false (recommended)
│
└─ NO → Use "translator"
    └─ Pure translation, no AI
```
