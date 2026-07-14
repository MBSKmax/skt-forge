# SKT-Forge — Live Web Version (Phase 1)

Ye Phase 1 ka poora working project hai: **backend API + frontend UI + live preview**.
Lovable/v0/Bolt.new ka chhota, functional version — solo developer ke liye realistic scope.

```
skt-forge/
├── backend/
│   ├── main.py           ← FastAPI server (Groq calls yahan hoti hain)
│   └── requirements.txt
└── frontend/
    └── index.html         ← Poora UI, koi build step nahi (plain HTML+JS)
```

---

## Kya Milta Hai

- Prompt likho → **database schema + backend API + frontend component** teeno milte hain
- Frontend component ka **live preview** turant dikhta hai (browser mein hi React render hota hai)
- Code copy karne ka button
- Sab kuch ek page pe, tabs mein organized

## Kya Nahi Milta (abhi)

- Backend/database live nahi chalte — sirf code dikhta hai, copy karke khud run karna hoga
- Login/signup nahi hai (Phase 3 mein aayega)
- Projects save nahi hote (session khatam = data gaya)

---

## Local Pe Chalane Ka Tarika (Step by Step)

### Step 1 — Backend chalayein

```powershell
cd backend
pip install -r requirements.txt
$env:GROQ_API_KEY="your_groq_key_here"
uvicorn main:app --reload --port 8000
```

Check karein: browser mein `http://localhost:8000` khol kar `{"status":"ok"}` dikhna chahiye.

### Step 2 — Frontend kholein

`frontend/index.html` ko seedha double-click karke browser mein khol dein.
(Koi npm install nahi chahiye — ye plain HTML file hai.)

### Step 3 — Test karein

- Text box mein likhein: `user login page banao`
- "Generate" dabayein
- ~10-20 second mein result aayega, "Live Preview" tab mein React component render hoga

---

## Live Kaise Karna Hai (Go-Live Steps)

Heading samajh lein: **abhi ye sirf aapke computer pe chal raha hai. "Live" banane ke liye:**

### 1. Backend Deploy Karein (Render — free tier)

1. `backend/` folder ko GitHub repo mein push karein
2. [render.com](https://render.com) pe jayein → New → Web Service
3. Apna GitHub repo connect karein
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Environment variable add karein: `GROQ_API_KEY` = apni key
6. Deploy karein — aapko ek URL milega jaise `https://your-app.onrender.com`

### 2. Frontend Deploy Karein (Vercel/Netlify — free)

1. `frontend/index.html` mein ye line dhoondein:
   ```js
   const API_URL = "http://localhost:8000/api/generate";
   ```
   Isko Render wale URL se replace karein:
   ```js
   const API_URL = "https://your-app.onrender.com/api/generate";
   ```
2. `frontend/` folder ko Vercel/Netlify pe drag-and-drop se deploy kar dein
   (dono free static hosting dete hain, GitHub connect ki bhi zaroorat nahi)

### 3. CORS Update Karein (Security ke liye)

`backend/main.py` mein ye line:
```python
allow_origins=["*"],
```
Isko apni actual frontend URL se replace kar dein (production mein `*` risky hai):
```python
allow_origins=["https://your-frontend.vercel.app"],
```

**Ban gaya — ab ye ek live website hai jo koi bhi visit kar sakta hai.**

---

## Agla Kya (Phase 2, 3, 4 recap)

| Phase | Kya | Status |
|---|---|---|
| 1 | Web wrapper (API + UI + basic preview) | ✅ Ye hai |
| 2 | Behtar preview (Sandpack — npm packages support) | ⏳ Baad mein |
| 3 | Login + save projects (Supabase) | ⏳ Baad mein |
| 4 | Custom domain, polish, launch | ⏳ Baad mein |

Filhaal Phase 1 ko live karke test karein — real users se feedback lena sabse
zaroori step hai, perfect banane se pehle.

## Known Limitations (Honest)

- Live preview sirf simple React components ke liye kaam karega (state, hooks theek chalenge, lekin complex multi-file imports nahi)
- Free Groq tier pe rate limits hain — bohot fast/zyada requests pe 429 error aa sakta hai
- Render free tier "cold start" leta hai (pehli request slow hogi agar server so raha ho)
