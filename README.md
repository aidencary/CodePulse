# CodePulse

<p align="center">
  <img src="images/CodePulseSlow.gif" width="500">
</p>

A code quality and bug prediction dashboard to verify if code adheres to coding standards and give feedback on potential bugs. Users can paste code into the live text editor and get feedback from the dashboard such as a code quality score, deviations from code standards, and potential bugs.

## Quick Start (For use locally)

- The frontend runs at `http://localhost:3000`
- The backend runs at `http://localhost:8000`

## What It Does With Your Code

CodePulse analyzes your code in real-time and provides:

- **Code Quality Score**: Overall assessment of code quality based on best practices
- **Standards Compliance**: Identifies deviations from established coding standards
- **Bug Prediction**: Uses a ChatGPT API to predict bugs
- **Actionable Feedback**: Provides specific suggestions for code improvements
- **Real-time Analysis**: Instant feedback as you type in the live editor

## Tech Stack

**Frontend**
- React 18 (functional components / Hooks)
- React Router v6
- Supabase Auth (`@supabase/supabase-js`)
- Plain CSS (per feature area)
- Create React App (`react-scripts`)

**Backend**
- Python 3.11+
- FastAPI - Modern web framework for building APIs
- Supabase (PostgreSQL + Auth + RLS)
- OpenAI GPT API - AI-powered bug prediction
- AST-based static analysis - Code quality assessment

**CI/CD**
- Git - Version control
- GitHub - Repository hosting and collaboration
- GitHub Actions - Automated testing and build verification on every PR

## Project Structure

```
CodePulse/
├── backend/          # Python backend application
├── frontend/         # React frontend application
├── postman/          # Postman collections, environments, and API tests
├── docs/             # Project documentation and diagrams
├── images/           # Project images and GIFs
├── README.md         # This file
├── STANDARDS.md      # Coding standards and guidelines
└── TESTING.md        # Testing and CI/CD guide
```

For detailed project structure, see [STANDARDS.md](STANDARDS.md).

## READMEs

- [Frontend README](frontend/README.md) - Frontend setup and development guide
- [Backend README](backend/README.md) - Backend setup and development guide
- [Testing & CI/CD Guide](TESTING.md) - How to run tests and how CI/CD works

## API

The backend uses FastAPI with these main endpoints:

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/` | None | Health check |
| `POST` | `/api/v1/analyze` | Bearer JWT | Submit code for analysis — returns static findings, GPT-predicted bugs, and quality score |

Full API docs available at `http://localhost:8000/docs` once the server is running (requires `DEBUG=true`).

### API Testing (Postman / Newman)

A Postman collection is available at `postman/collections/codepulse-api.postman_collection.json` with 14 tests across 4 folders (Health Check, Auth Errors, Validation Errors, Happy Path). Import it into Postman or run via Newman:

```bash
npm install -g newman
newman run postman/collections/codepulse-api.postman_collection.json \
  --environment postman/environments/ci.postman_environment.json
```

## Development Setup

### Prerequisites

- Node.js 18+
- Python 3.11+
- A configured [Supabase](https://supabase.com) project (see `backend/database/schema.sql`)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/aidencary/CodePulse.git
   cd CodePulse
   ```

2. **Set up the backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env            # Fill in your Supabase credentials
   uvicorn app.main:app --reload
   ```

3. **Set up the frontend**
   ```bash
   cd frontend
   npm install
   cp .env.example .env            # Fill in your Supabase URL and anon key
   npm start
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Environment Variables

Create `.env` files in both frontend and backend directories based on `.env.example` templates.

## Contribute to CodePulse!

We welcome contributions! Please follow these steps:

1. Read [STANDARDS.md](STANDARDS.md) for coding standards and workflow
2. Fork the repository
3. Create a feature branch: `git checkout -b yourname-feature-name`
4. Make your changes following our coding standards
5. Write tests for your changes
6. Commit your changes using conventional commits
7. Push to your branch: `git push origin yourname-feature-name`
8. Submit a pull request

### Development Guidelines

- Follow the coding standards in [STANDARDS.md](STANDARDS.md)
- Write tests for new features
- Keep commits atomic and well-described
- Request code review before merging

## Documentation

See the [docs](docs/) folder for:
- Class diagrams
- ER diagrams
- Use case diagrams
- Design and architecture documentation
- Requirements analysis

## Authors

- Aiden Cary (Team Lead/Developer)
- Keller Willhite (UI/UX Developer)
- Zachery Atchley (Integration and Unit Tester/Developer)

## Artists

- Ashlynn Monroe (Logo Creator)

## License

[INSERT LICENSE HERE]
