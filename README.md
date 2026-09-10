# Northstar Banking Assistant

A Streamlit banking assistant demo built with CrewAI, Groq, and a local SQLite dataset. The assistant routes questions to specialized agents for account details, transactions, spending analysis, and customer service requests.

## Features

- Account balance, type, status, and profile lookups
- Recent transaction history and category-based spending analysis
- Statement, address, cheque book, and KYC service requests
- Local SQLite data with automatic database initialization
- CrewAI agents with dedicated banking tools

## Requirements

- Python 3.10 or newer
- A Groq API key

## Run Locally

1. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Create a local environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

   Set `GROQ_API_KEY` in `.env` to your actual Groq API key.

4. Start the app:

   ```powershell
   streamlit run app.py
   ```

The app opens at `http://localhost:8501`.

## Streamlit Cloud Deployment

1. Push this repository to GitHub.
2. Create an app at [Streamlit Community Cloud](https://share.streamlit.io/).
3. Select this repository and the `main` branch.
4. Set the main file to `app.py`.
5. Add the following secret in the app settings:

   ```toml
   GROQ_API_KEY = "your_actual_groq_api_key"
   ```

The repository includes `.streamlit/config.toml` for headless hosting. Never commit `.env` or `.streamlit/secrets.toml`.

## Demo Data

The demo uses customer `USER-1001` and account `ACCT-1001`. If `bank_data.db` is missing, the application creates the local SQLite database from the setup code.

## Project Structure

```text
app.py                 Streamlit entry point
agents_and_tasks.py    Backward-compatible service imports
controllers/           Chat request handling
models/                Database path and initialization
services/              CrewAI and Groq service logic
views/                 Streamlit interface
mcp_tools.py           SQLite-backed CrewAI tools
database_setup.py      Demo database setup
requirements.txt       Python dependencies
```

## Security Note

This is a demonstration application with mock banking data. Do not use real customer information or production credentials. Rotate any API key that has been exposed and keep all secrets in environment variables or Streamlit Cloud Secrets.