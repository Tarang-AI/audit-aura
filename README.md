# AuditAura – Continuous Compliance Guardian

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.9+-blue)
![React](https://img.shields.io/badge/react-18.0+-blue)

## 🛡️ Tagline
**Real-time AI-powered audit readiness. Always compliant. Always watching.**

## 📋 Overview

AuditAura is a continuous compliance monitoring platform that shifts organizations from "Point-in-Time" audits to "Continuous Audit" posture. It uses AI agents to monitor configuration changes in real-time, detect compliance violations, and generate automated remediation recommendations.

### The Problem
Most enterprise audits are "Point-in-Time," meaning a system is only verified as compliant on the day of the audit. Minutes later, a configuration change (like opening an S3 bucket to the public) can break compliance, but it won't be caught until the next audit cycle.

### The Solution
AuditAura provides:
- **Continuous Monitoring**: Real-time event ingestion from CloudWatch, IBM Cloud, and other sources
- **AI-Powered Analysis**: Intelligent agents that understand compliance requirements
- **Instant Alerts**: WebSocket, Email, and Slack notifications for violations
- **Dynamic Compliance Tracking**: Real-time compliance percentage per audit standard
- **Auto-Remediation**: AI-generated fix recommendations and GitHub PR creation

## 👥 Team AuditAura
- **Durgadas** - Team Lead & Backend Architect
- **Team Member 1** - Frontend Developer
- **Team Member 2** - Cloud & DevOps
- **Team Member 3** - UI/UX Designer

## ✨ Features

### Core Capabilities
- ✅ **Hybrid AI Architecture** - OpenAI for complex tasks + Local LLM (Ollama) for efficiency
- ✅ **Intelligent Fallback** - Automatic switch to Ollama when OpenAI quota exhausted
- ✅ **Multi-Source Event Ingestion** - CloudWatch, IBM Cloud, Generic Logs
- ✅ **PDF Compliance Ingestion** - Upload SOC2, HIPAA, ISO27001 PDFs via file or URL
- ✅ **Vector Store Search** - Semantic search for relevant compliance controls
- ✅ **Rule-Based AI Agents** - Monitor, Analyze, and Remediate violations
- ✅ **Real-Time Notifications** - WebSocket, Email (SMTP), Slack webhooks
- ✅ **Compliance Dashboard** - Live compliance scores per standard
- ✅ **Security First** - No eval(), input validation, secure configuration
- ✅ **Mock Mode** - Demo-ready with synthetic data for presentations

### Supported Audit Standards
- SOC2 (System and Organization Controls 2)
- HIPAA (Health Insurance Portability and Accountability Act)
- ISO 27001 (Information Security Management)
- PCI DSS (Payment Card Industry Data Security Standard)
- GDPR (General Data Protection Regulation)
- Custom standards via PDF upload

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│  - File Upload UI  - Compliance Dashboard  - Live Alerts    │
└────────────────────────┬────────────────────────────────────┘
                         │ WebSocket + REST API
┌────────────────────────┴────────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Extractor  │  │ Vector Store │  │   Evaluator  │     │
│  │  (PDF→JSON)  │  │   (FAISS)    │  │ (Safe Rules) │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  AI Agents   │  │ Notifications│  │   Tracker    │     │
│  │ (Orchestr.)  │  │ (Multi-Chan.)│  │ (Compliance) │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                   Event Sources                              │
│  - AWS CloudWatch/CloudTrail                                 │
│  - IBM Cloud Activity Tracker                                │
│  - Generic Log Files                                         │
└──────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API Key (optional - falls back to local Ollama LLM)
- (Optional) SMTP credentials for email alerts
- (Optional) Slack webhook URL for Slack alerts

> **Note**: OpenAI API key is optional. If not provided or quota exhausted, the system automatically falls back to Ollama (local LLM) for PDF extraction. See [OLLAMA_FALLBACK.md](OLLAMA_FALLBACK.md) for details.

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/audit-aura.git
cd audit-aura
```

2. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

**Important:** Generate an encryption key for secure credential storage:
```bash
python tests/fix_encryption_key.py
```

Or manually add to `.env`:
```bash
# Generate key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Add to .env
ENCRYPTION_KEY=your_generated_key_here
```

Optional variables (recommended for best performance):
```env
OPENAI_API_KEY=your_openai_api_key_here  # Optional - uses Ollama if not set
```

Optional variables:
```env
# Email Notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@example.com
SMTP_PASSWORD=your_password

# Slack Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Application Settings
MOCK_MODE=true  # Set to false for production
COMPLIANCE_CHECK_INTERVAL=30  # seconds
```

3. **Start the application**
```bash
./start.sh
```

Or manually with Docker Compose:
```bash
docker-compose up --build
```

4. **Access the application**
- **Frontend (Local)**: http://localhost:3000 (standard local development)
- **Frontend (Production Mode)**: http://localhost:8000 (matches deployment exposure)
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

> [!IMPORTANT]
> When running in the **Semicolons Portal**, you must append `?app=<your_app_id>` to the URL for correct request routing.

### 🏗️ Semicolons Deployment Alignment
This repository is pre-configured for the Semicolons 2026 deployment portal:
- **Port Exposure**: The application is configured to expose itself on **port 8000** as required by the platform guidelines.
- **App Query Parameter**: The frontend is built with a custom utility (`appParam.ts`) that captures and persists the `app` identifier from the URL. This is critical for the shared DNS routing model used during the event.
- **Database Injection**: Backend consumes the `DATABASE_URL` environment variable for RDS connectivity, falling back to SQLite for local development.
- **LLM Integration**: Integrated with the **OpenCode Zen (Anthropic Bridge)**. Ensure `ANTHROPIC_API_KEY` is set to your Opencode key for full AI functionality.
- **Health Checks**: Root path `/` on the backend provides a standard health check response for the portal's monitoring.

## 🎨 New UI Features

### Role-Based Access Control

AuditAura now features a modern, role-based UI with three distinct personas:

#### 1. **Administrator**
- **Dashboard**: Comprehensive overview with compliance metrics, charts, and PDF upload
- **Controls Management**: View and manage compliance controls
- **Settings**: Configure system settings and integrations
- **Features**:
  - Upload compliance PDFs (SOC2, HIPAA, ISO27001, etc.)
  - View compliance trends with interactive charts
  - Monitor violation severity distribution
  - Track standards compliance
  - Auto-refresh every 30 seconds

#### 2. **End User**
- **Dashboard**: Personal compliance overview and active violations
- **Violations**: Detailed violation tracking and alerts
- **Features**:
  - View personal compliance score
  - Track active violations
  - Receive real-time alerts
  - Monitor standards compliance

#### 3. **Auditor**
- **Dashboard**: Audit metrics and compliance scores by standard
- **Reports**: Generate and download audit reports
- **Features**:
  - Review completed audits
  - Track pending reviews
  - View compliance scores by standard
  - Generate audit reports
  - Export compliance data

### UI Components

- **Modern Design**: Clean, professional interface with Tailwind CSS
- **Responsive Layout**: Works on desktop, tablet, and mobile
- **Live Animations**: Smooth transitions and hover effects
- **Data Visualization**: Interactive charts using Recharts
- **Real-time Updates**: WebSocket integration for live data
- **Error Handling**: Graceful error boundaries
- **Loading States**: Consistent loading indicators

### Authentication Flow

1. **Login Page**: Enter credentials (demo mode accepts any email/password)
2. **Role Selection**: Choose your role (Admin/User/Auditor)
3. **Dashboard**: Access role-specific features and data


## 📖 Usage

### 1. Upload Compliance Documents

**Via UI:**
1. Navigate to the dashboard
2. Use the "Upload Compliance Documents" section
3. Upload a PDF file or provide a URL

**Via API:**
```bash
# Upload file (automatically saved to ./backend/data/pdfs/)
curl -X POST "http://localhost:8000/upload" \
  -F "file=@SOC2_Controls.pdf"

# Upload from URL
curl -X POST "http://localhost:8000/upload-url?url=https://example.com/compliance.pdf"

# List stored PDFs
curl -X GET "http://localhost:8000/pdfs"

# Re-ingest all PDFs from storage
curl -X POST "http://localhost:8000/ingest"

# Re-ingest a specific PDF
curl -X POST "http://localhost:8000/ingest/SOC2_Controls.pdf"
```

**PDF Storage:**
- All uploaded PDFs are automatically saved to `./backend/data/pdfs/`
- PDFs persist across container restarts via Docker volume mount
- You can manually copy PDFs to this directory and use the `/ingest` endpoint
- Use `/pdfs` endpoint to list all stored PDFs with metadata

### 2. Monitor Compliance

The dashboard automatically displays:
- Overall compliance score
- Per-standard compliance breakdown
- Live violation alerts
- Severity and category statistics

### 3. Receive Alerts

Violations are sent via:
- **WebSocket**: Real-time UI updates
- **Email**: Detailed HTML emails with remediation steps
- **Slack**: Formatted messages with violation details

### 4. Review Violations

Each alert includes:
- Control ID and description
- Audit standard and category
- Severity level (Critical, High, Medium, Low)
- Event details that triggered the violation
- AI-generated remediation steps

## 🔧 Configuration

### Mock Mode vs Production Mode

**Mock Mode** (default for demos):
```env
MOCK_MODE=true
```
- Generates synthetic events
- No real cloud credentials needed
- Perfect for presentations and testing

**Production Mode**:
```env
MOCK_MODE=false
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
IBM_CLOUD_API_KEY=your_key
```
- Connects to real event sources
- Requires cloud credentials
- Production-ready monitoring

### Event Sources

Configure event sources in your environment:

**AWS CloudWatch:**
```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
```

**IBM Cloud:**
```env
IBM_CLOUD_API_KEY=your_key
```

**Generic Logs:**
```env
LOG_FILE_PATH=/path/to/logs
```

## 🤖 AI Agent System

AuditAura uses a rule-based AI agent architecture:

### Agent Roles

1. **Monitor Agent**
   - Watches for compliance violations
   - Prioritizes by severity
   - Triggers notifications

2. **Analyzer Agent**
   - Assesses impact of violations
   - Identifies root causes
   - Determines affected resources

3. **Remediator Agent**
   - Generates remediation steps
   - Estimates fix time
   - Can create GitHub PRs (optional)

### Rule-Based Development

Agents follow strict rules:
- No arbitrary code execution
- Deterministic behavior
- Auditable decision-making
- Configurable priorities

## 📊 API Endpoints

### Health Check
```
GET /
```

### Upload Compliance PDF
```
POST /upload
Content-Type: multipart/form-data
Body: file (PDF)
```

### Upload from URL
```
POST /upload-url?url={pdf_url}
```

### Get Compliance Score
```
GET /compliance-score?standard={optional}
```

### Get Dashboard Data
```
GET /dashboard
```

### Get Violations
```
GET /violations?standard={optional}
```

### WebSocket Connection
```
WS /ws
```

## 🔒 Security Features

- ✅ No `eval()` or arbitrary code execution
- ✅ Input validation on all endpoints
- ✅ Secure configuration management
- ✅ Environment variable validation
- ✅ API key protection (.gitignore)
- ✅ CORS configuration
- ✅ Safe rule evaluation engine

## 🧪 Testing

Run tests:
```bash
cd backend
pytest
```

Run with coverage:
```bash
pytest --cov=. --cov-report=html
```

## 📦 Project Structure

```
audit-aura/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration management
│   ├── requirements.txt        # Python dependencies
│   └── services/
│       ├── extractor.py        # PDF extraction
│       ├── vector_store.py     # Vector search
│       ├── evaluator.py        # Safe rule evaluation
│       ├── evidence.py         # Evidence generation
│       ├── notifications.py    # Multi-channel alerts
│       ├── event_sources.py    # Event ingestion
│       ├── ai_agents.py        # Agent orchestration
│       └── compliance_tracker.py # Compliance scoring
├── frontend/
│   ├── main.jsx                # React application
│   ├── index.html              # HTML template
│   └── package.json            # Node dependencies
├── docker-compose.yml          # Docker orchestration
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- OpenAI for GPT models
- Ollama for local LLM support
- LangChain for AI orchestration
- FastAPI for the backend framework
- React for the frontend framework

## 📞 Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/yourusername/audit-aura/issues)
- Email: support@auditaura.com

## 🐛 Troubleshooting

### Connection Test Failed: Decryption Error

If you see an error like:
```
Connection test failed: Failed to decrypt configuration: Failed to decrypt data:
```

**Quick Fix:**
```bash
python tests/fix_encryption_key.py
```

This error occurs when the `ENCRYPTION_KEY` environment variable is not set or has changed. See the [Encryption Key Fix Guide](docs/troubleshooting/ENCRYPTION_KEY_FIX.md) for detailed instructions.

**Alternative Solutions:**
1. Set `ENCRYPTION_KEY` in `.env` file
2. Delete corrupted connections: `curl -X POST http://localhost:8000/api/connections/cleanup/corrupted`
3. Delete `backend/data/connections.json` and recreate connections

### Other Issues

For other troubleshooting topics, see:
- [Troubleshooting Guide](docs/troubleshooting/TROUBLESHOOTING.md)
- [Ollama Fallback](docs/technical/OLLAMA_FALLBACK.md)
- [LM Studio Integration](docs/technical/LM_STUDIO_INTEGRATION.md)

## 🗺️ Roadmap

- [ ] GitHub PR auto-remediation
- [ ] Multi-tenant support
- [ ] Custom rule builder UI
- [ ] Integration with more cloud providers
- [ ] Mobile app
- [ ] Advanced analytics and reporting
- [ ] Compliance report generation
- [ ] Audit trail export

---

**Built with ❤️ for continuous compliance**
