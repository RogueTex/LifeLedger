# How to Export and Use Your Own Personal Data

This hackathon provides 5 synthetic personas as a shared starting point — but you're also welcome to build with your own real exported data. This guide shows you how.

---

## Before You Start: Privacy First

**You are fully responsible for any real data you use.** Before working with personal exports:

- Remove or redact any sensitive content (passwords, financial account numbers, SSNs, medical record numbers, other people's personal information)
- Process data **locally** whenever possible — avoid uploading real personal data to third-party services
- Never share your real data with teammates or in public submissions without explicit consent
- When in doubt, use the synthetic personas instead

---

## Export Sources

### ChatGPT (OpenAI)
Your full AI conversation history — one of the most valuable datasets for this hackathon.

1. Log in at chat.openai.com
2. Click your profile icon → **Settings**
3. Go to **Data Controls** → **Export Data**
4. Click **Confirm Export** — you'll receive an email with a download link within minutes
5. The ZIP contains `conversations.json` with your full chat history

**What you get:** Every conversation, including prompts and responses, with timestamps.

---

### Google Takeout
Your Gmail, Google Calendar, Google Drive, Location History, YouTube history, and more.

1. Go to **takeout.google.com**
2. Select the data types you want (recommend: Gmail, Calendar, Drive for this hackathon)
3. Choose export format (JSON preferred where available) and delivery method
4. Click **Create Export** — delivery can take minutes to hours depending on size

**What you get:** A ZIP with structured exports of your selected Google data.

---

### Claude (Anthropic)
Your Claude conversation history.

1. Log in at claude.ai
2. Go to **Settings** → **Privacy**
3. Select **Export Data**
4. Download when the export email arrives

---

### Instagram
Your posts, messages, activity, and more.

1. Go to **Settings** → **Your Activity** → **Download Your Information**
2. Select **JSON** format
3. Choose date range and request download
4. You'll receive an email when it's ready (can take up to 48 hours)

---

### Facebook
Similar to Instagram — owned by Meta.

1. Go to **Settings & Privacy** → **Settings**
2. Click **Your Facebook Information** → **Download Your Information**
3. Select **JSON** format and desired date range
4. Request and download when ready

---

### Apple Health
Your health and activity data from iPhone/Apple Watch.

1. Open the **Health** app on iPhone
2. Tap your profile picture → **Export All Health Data**
3. Share the ZIP to your computer via AirDrop, email, or Files app

**What you get:** `export.xml` with all health metrics — steps, heart rate, sleep, workouts, etc.

---

## Tips for Working With Your Own Data

- **Start small:** Load one file type first (e.g., just calendar events) before combining sources
- **Strip identifiers early:** Write a script at the start of your project that removes names, emails, and phone numbers from the data before any processing
- **Use the synthetic schema as a guide:** The JSONL format in the provided personas is a good target structure to normalize your own exports into
- **Your own data = better demos:** If you build something that works on your actual life, it will be more compelling to judges and more meaningful as a project

---

## Generating Additional Synthetic Data

If you want more data than the provided personas contain, you can generate it yourself using AI:

> *"Generate a lifelog dataset for a fictional [age]-year-old [job] in [city] as JSONL. 200 lines spanning 24 months. Fields: id, ts, source='lifelog', type, text, tags[], refs[], pii_level='synthetic'. Include themes: [list your themes]. Output JSONL only."*

Use the same schema as the provided personas so your data stays compatible.

---

*Data Portability Hackathon 2026 — AI Collective × DTI × UT Law*
