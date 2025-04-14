# CrewAI + LangGraph

# Email Automation System with CrewAI and LangGraph

This project implements an automated email processing system that monitors your inbox, identifies important emails, and drafts responses using AI. It combines CrewAI for agent-based tasks and LangGraph for workflow orchestration.

## System Architecture

![Email Automation Workflow](./pdf-crew/CrewAI-LangGraph/CrewAI-LangGraph.png)

### Workflow Pipeline

1. **Email Fetching**: System connects to Microsoft Graph API to fetch recent emails
2. **Email Filtering**: Only processes emails from allowed senders/domains
3. **Content Analysis**: AI analyzes email content to determine importance and required actions
4. **Response Generation**: AI drafts appropriate responses to important emails
5. **Cycle Repetition**: System waits before checking for new emails again

### Component Roles

#### LangGraph Nodes
- **check_new_emails**: Fetches new emails from Microsoft Graph API
- **wait_next_run**: Implements delay between email checking cycles (20 seconds)
- **draft_responses**: Coordinates the CrewAI agents to process emails

#### CrewAI Agents
1. **Senior Email Analyst**
   - **Role**: Filter non-essential emails
   - **Task**: Analyze and identify important emails requiring attention
   - **Time**: ~5-10 seconds per batch of emails

2. **Email Action Specialist**
   - **Role**: Identify action-required emails
   - **Task**: Fetch full email threads and summarize context, urgency, and required actions
   - **Tools**: Email Thread Tool, Tavily Search
   - **Time**: ~10-15 seconds per email thread

3. **Email Response Writer**
   - **Role**: Draft appropriate responses to important emails
   - **Task**: Create draft responses based on email context and urgency
   - **Tools**: Draft Creation Tool, Tavily Search
   - **Time**: ~15-20 seconds per email response

## Email Processing Rules

### Allowed Senders Configuration
- **Allowed Senders**: Specific email addresses allowed (configured in .env)
- **Allowed Domains**: Entire domains allowed (configured in .env)
- **Blocked Keywords**: Email addresses containing specific keywords will be blocked

### Processing Time
- **New Email Check**: Every 20 seconds
- **Full Processing Cycle**: ~30-45 seconds depending on email complexity
- **Rate Limiting**: System implements measures to avoid API rate limits

## Project Files

| File | Description |
|------|-------------|
| `main.py` | Entry point for the application |
| `src/graph.py` | LangGraph workflow definition |
| `src/state.py` | State management for the workflow |
| `src/nodes.py` | Node implementations for LangGraph |
| `src/msgraphclient.py` | Microsoft Graph API client integration |
| `src/crew/agents.py` | CrewAI agent definitions |
| `src/crew/tasks.py` | CrewAI task definitions |
| `src/crew/crew.py` | CrewAI crew orchestration |
| `src/crew/tools.py` | Custom tools for agents (email fetch/draft) |

## Configuration

### Environment Variables (.env)
```
# Microsoft Graph API Credentials
MS_CLIENT_ID=your_client_id
MS_CLIENT_SECRET=your_client_secret
MS_TENANT_ID=your_tenant_id
MS_USER_EMAIL=your_email@example.com
MY_EMAIL=your_email@example.com

# Email Filter Configuration
ALLOWED_SENDERS=sender1@example.com,sender2@company.com
ALLOWED_DOMAINS=domain1.com,domain2.com
BLOCKED_KEYWORDS=spam,noreply,donotreply

# LLM Configuration
OPENAI_API_KEY=your_openai_key
# OR for alternatives:
# OLLAMA_BASE_URL=http://localhost:11434
# WATSON_API_KEY=your_watson_key
# WATSON_URL=your_watson_url
```

### LLM Provider Configuration

The system supports multiple LLM providers:

1. **OpenAI** (Default)
   - Set `OPENAI_API_KEY` in .env
   - Model configured in `agents.py`

2. **Watson.ai**
   - Set `WATSON_API_KEY` and `WATSON_URL` in .env
   - Update model configuration in `agents.py`

3. **Ollama (Local)**
   - Set `OLLAMA_BASE_URL` in .env (typically http://localhost:11434)
   - Model configuration in `agents.py`

## Setup and Running

### Prerequisites
- Python 3.11
- Microsoft Graph API credentials
- LLM provider access (OpenAI, Watson, or Ollama)

### Installation

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
python3 -m pip install -r requirements.txt

# If additional packages needed
python3 -m pip install <package_name>
```

### Running the Application

1. Create and configure your `.env` file (see Configuration section)
2. Activate the virtual environment: `source venv/bin/activate`
3. Run the application: `python main.py`

## Handling Special Cases

### Arabic Content and Attachments
The system includes optimizations for handling:
- Arabic text (which uses more tokens than English)
- Emails with attachments (metadata only, not content)
- HTML-formatted emails (with content stripping)

### Error Handling
- Implements fallback methods when MS Graph API queries fail
- Limits content size to avoid LLM token limitations
- Implements recursion limits to prevent infinite loops

## Troubleshooting

- **Rate limit errors**: Reduce polling frequency or use a different LLM
- **Thread fetch errors**: Check MS Graph permissions
- **Draft creation errors**: Verify email format handling
- **Unicode/encoding issues**: Check handling of non-ASCII content

## Future Improvements

- Add persistence layer for tracking email states
- Implement fine-tuned models for better email understanding
- Add attachment processing capabilities
- Integrate with calendar for scheduling follow-ups