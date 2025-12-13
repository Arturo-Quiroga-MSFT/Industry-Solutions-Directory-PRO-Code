# Open WebUI Setup

Clean, Docker-only Open WebUI setup for chatting with Azure OpenAI models.

## Quick Start

```bash
# Start Open WebUI
docker compose up -d

# View logs
docker compose logs -f

# Stop
docker compose down
```

Access at: **http://localhost:3000**

## Configuration

- **Port**: 3000 (mapped to container's 8080)
- **Model**: gpt-4.1-mini (Azure OpenAI)
- **Data**: Persisted in Docker volume `open-webui-data`

## First Time Setup

1. Navigate to http://localhost:3000
2. Create an admin account (first user becomes admin)
3. Select "gpt-4.1-mini" from the models dropdown
4. Start chatting!

## Azure OpenAI Configuration

Pre-configured in `.env`:
- Endpoint: `aq-ai-foundry-sweden-central`
- Model: `gpt-4.1-mini`
- API Version: `2024-08-01-preview`

## MCP Server Integration (Experimental)

Open WebUI has experimental MCP support. To enable:

1. Uncomment the MCP configuration in `.env`
2. Restart: `docker compose restart`
3. Navigate to Settings → Connections → MCP Servers

The ISD MCP server path is already configured for you!

## Features

✅ **Azure OpenAI Integration**  
✅ **Clean, modern UI**  
✅ **Multi-user support**  
✅ **Conversation history**  
✅ **File uploads**  
✅ **MCP support (experimental)**  
✅ **Markdown rendering**  
✅ **Code syntax highlighting**  

## Useful Commands

```bash
# View all logs
docker compose logs

# Restart
docker compose restart

# Update to latest version
docker compose pull
docker compose up -d

# Reset (removes all data!)
docker compose down -v
docker compose up -d
```

## Troubleshooting

### Port already in use
```bash
# Check what's using port 3000
lsof -i :3000

# Change port in docker-compose.yml
ports:
  - "3001:8080"  # Use 3001 instead
```

### Model not appearing
1. Go to Settings → Connections
2. Verify Azure OpenAI configuration
3. Click "Save"
4. Refresh the page

### Reset to factory settings
```bash
docker compose down -v
rm -rf .env
# Recreate .env with default settings
docker compose up -d
```

## Data Persistence

All data is stored in Docker volume `open-webui-data`:
- User accounts
- Conversation history
- Settings
- Uploaded files

To backup:
```bash
docker run --rm -v open-webui-data:/data -v $(pwd):/backup alpine tar czf /backup/open-webui-backup.tar.gz /data
```

To restore:
```bash
docker run --rm -v open-webui-data:/data -v $(pwd):/backup alpine tar xzf /backup/open-webui-backup.tar.gz -C /
```

## Differences from LibreChat

| Feature | Open WebUI | LibreChat |
|---------|------------|-----------|
| Setup Complexity | Simple (1 container) | Complex (5 containers) |
| Azure OpenAI | Native support | Requires config file |
| MCP Support | Experimental | Not available |
| UI Style | Modern, minimal | ChatGPT-like |
| Performance | Fast | Slower startup |

---

**Note**: Configuration files only - no repo cloned in this workspace.
