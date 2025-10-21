# Frontdesk Human-in-the-Loop AI System

> **Built for Frontdesk Engineering Assessment - October 2025**

A self-improving AI receptionist system that intelligently escalates unknown queries to human supervisors, learns from their responses, and gets smarter over time.

---

## 🎯 Project Overview

This system demonstrates a complete human-in-the-loop workflow for AI customer service:

1. 🤖 **AI Agent** handles customer calls (terminal simulation)
2. ❓ **Unknown questions** → Automatically escalated to supervisor
3. 👤 **Supervisor answers** via web dashboard
4. 📱 **Customer notified** immediately (console log simulation)
5. 🧠 **Knowledge base learns** automatically for future queries



## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Python 3.9+
- Node.js 16+
- npm

### Installation

**1. Clone the repository:**
```bash
git clone https://github.com/YOUR_USERNAME/frontdesk-hitl.git
cd frontdesk-hitl
```

**2. Setup Backend:**
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

**3. Setup Agent:**
```bash
cd ../agent
python -m venv venv

# Windows  
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

**4. Setup Frontend:**
```bash
cd ../frontend
npm install
cp .env.example .env
```

### Running the System

Open **3 terminal windows**:

**Terminal 1 - Backend API:**
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python app.py
```
→ Runs on http://localhost:8000

**Terminal 2 - Supervisor Dashboard:**
```bash
cd frontend
npm start
```
→ Opens browser at http://localhost:3000

**Terminal 3 - AI Agent:**
```bash
cd agent
source venv/bin/activate  # or venv\Scripts\activate on Windows
python agent.py
```
→ Interactive terminal agent

---

## 🎬 Demo Walkthrough

### Complete Test Flow:

1. **Agent Terminal:** Type `new` to start a call
2. **Enter caller info** (or press Enter for defaults)
3. **Ask unknown question:** "Do you offer Botox treatments?"
4. **Agent escalates** → Creates help request
5. **Open Dashboard:** http://localhost:3000 → See request in "Pending" tab
6. **Answer the question:** Type comprehensive answer, click "Submit"
7. **Watch the magic:**
   - ✅ Backend logs show customer notification
   - ✅ Request moves to "History" tab
   - ✅ Answer appears in "Knowledge Base" tab
8. **Test learning:** Start new call, ask about Botox again
9. **AI knows instantly!** No escalation needed

**This proves the self-learning system works.** 🎉

---

## 🏗️ Architecture

### System Components
```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Agent     │─────▶│   Backend   │◀─────│  Dashboard  │
│ (Terminal)  │      │   (Flask)   │      │   (React)   │
└─────────────┘      └─────────────┘      └─────────────┘
     │                     │                     │
     ▼                     ▼                     ▼
  Simulates           Manages State         Human Interface
Customer Calls      + Knowledge Base      Answer Questions
```

### Request Lifecycle
```
Customer Question
      ↓
Check Knowledge Base
      ↓
  ┌───────┴───────┐
  ↓               ↓
Known           Unknown
  ↓               ↓
Answer      Escalate to Supervisor
Instantly         ↓
           Dashboard Alert
                  ↓
           Supervisor Answers
                  ↓
         ┌────────┴────────┐
         ↓                 ↓
  Notify Customer    Update Knowledge Base
  (Console Log)        (Auto-Learning)
```

---

## 🎨 Key Design Decisions

### 1. Terminal Agent vs LiveKit
**Decision:** Built terminal simulator

**Rationale:**
- Requirements allow "sample app" approach
- Focuses on HITL logic (core requirement)
- Easier to demonstrate and test
- Agent interface designed for easy LiveKit migration

**Future:** LiveKit integration straightforward (~1-2 days)

### 2. In-Memory Database
**Decision:** Python dictionaries instead of SQL

**Rationale:**
- Zero setup, fastest development
- Perfect for MVP demonstration
- Dataclass structure enables 30-minute migration to SQL

**Scaling Path:** In-memory → SQLite → PostgreSQL

### 3. Smart Knowledge Matching
**Implementation:** Synonym expansion + Jaccard similarity

**Why:**
- "hours" matches "timings", "schedule", "opening times"
- No external dependencies
- Fast (< 1ms per query)
- Good enough for <100 entries

**Future:** Easy upgrade to embeddings documented in code

### 4. Request Timeout: 1 Hour
**Decision:** Auto-expire after 60 minutes

**Rationale:**
- Balances urgency with supervisor availability
- Prevents indefinite backlog
- Automatic system cleanup

---

## 📊 API Documentation

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/requests` | Create help request |
| GET | `/api/requests?status=X` | List requests (filter by status) |
| GET | `/api/requests/{id}` | Get request details |
| POST | `/api/requests/{id}/answer` | Submit answer |
| POST | `/api/requests/{id}/unresolved` | Mark as unresolved |
| GET | `/api/knowledge` | List all knowledge entries |
| GET | `/api/knowledge?query=X` | Search knowledge base |
| GET | `/api/stats` | System statistics |

### Example: Create Request
```bash
curl -X POST http://localhost:8000/api/requests \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Do you offer parking?",
    "caller_name": "John Doe",
    "caller_phone": "+1-555-0100",
    "call_id": "call_123"
  }'
```

---

## 📈 Scaling Strategy

### Current: 10-50 requests/day ✅
- Single process, in-memory storage
- No bottlenecks

### To 1,000 requests/day (1 week)
- PostgreSQL + connection pooling
- Redis for KB caching
- Celery for async tasks
- Multiple API workers

### To 10,000+ requests/day (ongoing)
- Microservices architecture
- Event-driven (SQS/SNS)
- Vector database (semantic search)
- Multi-region deployment

**Detailed analysis:** See `docs/DESIGN.md`

---

## 🧪 Testing

### Automated Test Cases
```bash
# Test knowledge base matching
curl "http://localhost:8000/api/knowledge?query=hours"
curl "http://localhost:8000/api/knowledge?query=timings"
# Both should return same answer

# Test request creation
curl -X POST http://localhost:8000/api/requests \
  -H "Content-Type: application/json" \
  -d '{"question":"Test?","caller_name":"Test","caller_phone":"+1","call_id":"test"}'
```

### Manual Test Scenarios

1. **Known Question:** "What are your hours?" → Instant answer
2. **Synonym Test:** "timings" → Same answer as "hours"
3. **Unknown Question:** "Do you offer Botox?" → Escalates
4. **Learning Test:** Answer Botox, then ask again → AI knows
5. **Variations:** "parking", "Do you have parking?", "Where can I park?" → All match

---

## 📝 Project Structure
```
frontdesk-hitl/
├── backend/               # Flask API Server
│   ├── app.py            # Main application
│   ├── requirements.txt  # Python dependencies  
│   └── .env              # Config (gitignored)
├── agent/                # AI Agent
│   ├── agent.py          # Terminal simulator
│   ├── requirements.txt  # Python dependencies
│   └── .env              # Config (gitignored)
├── frontend/             # React Dashboard
│   ├── src/
│   │   ├── App.jsx       # Main component
│   │   └── index.js      # Entry point
│   ├── public/
│   │   └── index.html    # HTML template
│   ├── package.json      # Node dependencies
│   └── .env              # Config (gitignored)
├── docs/
│   └── DESIGN.md         # Detailed design decisions
└── README.md             # This file
```

---

## 🔧 Technical Stack

**Backend:**
- Flask 3.0.0 (REST API)
- Python dataclasses (data modeling)
- In-memory storage (upgradeable to SQL)

**Frontend:**
- React 18.2.0
- Tailwind CSS (via CDN)
- Lucide React (icons)

**Agent:**
- Python 3.9+
- Requests library (HTTP client)
- Terminal I/O (call simulation)

---

## 🐛 Known Limitations

1. **No authentication** → Add JWT for production
2. **No rate limiting** → Add per-IP limits
3. **In-memory storage** → 30-min migration to SQL documented
4. **Single supervisor** → Multi-supervisor routing is Phase 2
5. **Keyword matching** → Embeddings upgrade path clear
6. **No PII encryption** → Would encrypt at rest

All have straightforward solutions documented in code.

---

## 🚧 Future Improvements

### Phase 2 (From Requirements)
- Live call transfer when supervisor available
- Real-time vs async flow decision

### Production Enhancements
- LiveKit integration for real phone calls
- Twilio SMS for actual notifications
- WebSocket for real-time dashboard
- Vector embeddings for semantic search
- Multi-language support
- Mobile supervisor app
- Advanced analytics

---

## 📚 Documentation

- **README.md** (this file) - Setup and overview
- **docs/DESIGN.md** - Detailed design decisions
- **.env.example files** - Configuration templates
- **Inline code comments** - Implementation details

---

## 🎥 Video Demo

> > Watch the demo video here: [Frontdesk HITL Demo Video](https://drive.google.com/file/d/13AikYbRUV4jUYTY8I85zWCxHn26Czdmw/view?usp=sharing)


**Covers:**
- System architecture
- Live demonstration
- Design decisions
- Scaling strategy
- Future improvements

---

## 👤 Author

**Kiran Rangu**
- GitHub:[KIRANRW9](https://github.com/KIRANRW9)
- Email:  kiranrw09@gmail.com
- LinkedIn : [Kiran Rangu](www.linkedin.com/in/kiranrangu)


## 🙏 Acknowledgments

**Built for Frontdesk Engineering Assessment**

## 📄 License

This project is for assessment purposes.

---

**Thank you for reviewing my submission!** I'm excited to discuss the architecture, design decisions, and potential improvements in the interview. 🚀
