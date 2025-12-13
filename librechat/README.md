# LibreChat Docker Setup

This directory contains Docker-only configuration for LibreChat - no repo cloning needed!

## Quick Start

```bash
# From this directory
docker-compose up -d
```

Access at: http://localhost:3080

## Stop LibreChat

```bash
docker-compose down
```

## View Logs

```bash
docker-compose logs -f
```

## Configuration

- `docker-compose.yml` - Docker services configuration
- `.env` - Environment variables (Azure OpenAI credentials)

## Azure OpenAI Models

Configured models:
- gpt-4o-mini (default)
- gpt-4o

## MCP Server Integration

The `.env` file includes paths to your ISD MCP server for future integration.

## Data Persistence

LibreChat data is stored in Docker volumes. To reset:

```bash
docker-compose down -v  # Warning: deletes all data!
docker-compose up -d
```

## Troubleshooting

If LibreChat won't start:
1. Check if port 3080 is available: `lsof -i :3080`
2. View logs: `docker-compose logs`
3. Restart: `docker-compose restart`

## Updating

```bash
docker-compose pull
docker-compose up -d
```

---

**Note**: This setup uses Docker only - no LibreChat repo cloned in this workspace.
