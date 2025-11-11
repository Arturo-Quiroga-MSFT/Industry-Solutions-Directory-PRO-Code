# Gradio Frontend for Industry Solutions Directory

A modern, beautiful chat interface built with Gradio for discovering Microsoft partner solutions.

## Features

✨ **Better Chat Experience**
- Clean, modern interface with streaming responses
- Real-time typing indicators
- Better visual hierarchy

🎯 **Enhanced Usability**
- Quick example questions in sidebar
- One-click session reset
- Backend health monitoring
- Clickable citations and follow-up questions

🚀 **Performance**
- Faster rendering than Streamlit
- Smoother streaming
- Better mobile responsiveness

## Quick Start

### Local Development

The app defaults to `http://localhost:8000` for the backend. This only works when the backend is reachable from your machine (for example in a local dev environment without private endpoints).

1. **Install dependencies**
```bash
pip install -r requirements.txt
```

2. **Set backend URL** (optional)
```bash
export BACKEND_API_URL=http://localhost:8000
```

3. **Run the application**
```bash
python gradio_app.py
```

4. **Open in browser**
Navigate to: http://localhost:7860

> ℹ️ **Using private endpoints?** If the backend is only accessible from Azure (for example via VNet + private link), run the Gradio app inside the same network using Azure Container Apps or another compute attached to that VNet. See the “Private Network Testing” section below.

### Docker Deployment

1. **Build the image**
```bash
docker build -t industry-solutions-gradio .
```

2. **Run the container**
```bash
docker run -p 7860:7860 \
  -e BACKEND_API_URL=http://your-backend-url:8000 \
  industry-solutions-gradio
```

### Deploy to Azure Container Apps

```bash
# Login to Azure
az login

# Build and push image
az acr build --registry <your-acr-name> \
  --image industry-solutions-gradio:latest \
  .

# Update container app
az containerapp update \
  --name frontend-gradio \
  --resource-group <your-rg> \
  --image <your-acr-name>.azurecr.io/industry-solutions-gradio:latest
```

If you are using a VNet-secured backend, make sure the Container App is joined to the same environment and subnet so it can reach the private endpoints.

## Comparison: Gradio vs Streamlit

| Feature | Gradio | Streamlit |
|---------|--------|-----------|
| **Chat Interface** | ✅ Native, beautiful | ⚠️ Custom, clunky |
| **Streaming** | ✅ Smooth | ⚠️ Requires reruns |
| **Performance** | ✅ Fast | ⚠️ Slower |
| **UI Flexibility** | ✅ High | ⚠️ Medium |
| **Mobile Support** | ✅ Excellent | ⚠️ Fair |
| **Learning Curve** | ✅ Easy | ✅ Easy |
| **Deployment** | ✅ Simple | ✅ Simple |

## Configuration

Environment variables:

- `BACKEND_API_URL`: Backend API endpoint (default: `http://localhost:8000`)

## Architecture

```
┌─────────────────┐
│  Gradio UI      │
│  (Port 7860)    │
└────────┬────────┘
         │
         │ HTTP/SSE
         │
         ▼
┌─────────────────┐
│  FastAPI        │
│  Backend        │
│  (Port 8000)    │
└────────┬────────┘
         │
         ├──► Azure OpenAI
         ├──► Azure AI Search
         └──► Cosmos DB
```

## Features in Detail

### Streaming Chat
- Real-time response streaming
- Typing indicators
- Smooth animations

### Citations
- Formatted solution cards
- Relevance scores
- Direct links to solutions

### Follow-up Questions
- AI-generated suggestions
- One-click to continue conversation

### Session Management
- Persistent session IDs
- Easy session reset
- Session info display

### Backend Health
- Real-time status monitoring
- Connection error handling
- Graceful fallbacks

## Development

### Code Structure

```
frontend-gradio/
├── gradio_app.py      # Main application
├── requirements.txt   # Dependencies
├── Dockerfile         # Container image
└── README.md         # This file
```

### Key Functions

- `stream_chat()`: Streams responses from the backend SSE endpoint
- `format_citations()`: Formats solution metadata as markdown cards
- `format_follow_up()`: Renders follow-up prompts
- `build_interface()`: Constructs the Gradio `Blocks` layout

### Customization

**Change Theme:**
```python
gr.themes.Soft(primary_hue="blue", secondary_hue="purple")
```

**Modify Layout:**
Edit `build_interface()` to adjust columns, add components, or change styling.

**Add Features:**
Extend the `stream_chat()` generator or attach new Gradio events inside `build_interface()`.

## Troubleshooting

### Backend Not Connected
- Ensure backend is running: `cd backend && uvicorn app.main:app --reload`
- Check `BACKEND_API_URL` environment variable
- Verify network connectivity or VNet routing rules

### Slow Streaming
- Check backend performance
- Verify network latency
- Review Azure OpenAI throttling

### UI Not Loading
- Clear browser cache
- Check console for errors
- Verify port 7860 is not in use

### Private Network Testing
- Deploy the Gradio container to an Azure Container App environment joined to the same VNet/subnet as the backend.
- Alternatively use Azure Container Instances or an Azure VM that has network access to the private endpoint, then run `python gradio_app.py` there.
- Remember to set `BACKEND_API_URL` to the internal FQDN or private IP that resolves inside the VNet.

## Next Steps

1. ✅ Run locally and test
2. ✅ Compare with Streamlit version
3. ✅ Deploy to Azure Container Apps
4. ✅ Update deployment scripts
5. ✅ Share with team

## Support

For issues or questions:
- Check backend logs
- Review Gradio documentation: https://gradio.app/docs
- Contact: Arturo Quiroga, Principal Solutions Architect
