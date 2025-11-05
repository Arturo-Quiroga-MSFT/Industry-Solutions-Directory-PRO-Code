# Frontend

User interfaces for the Industry Solutions Directory.

## Streamlit UI (Recommended for Quick Start)

Modern, interactive web interface built with Streamlit.

### Features

- 💬 Real-time chat interface
- 📚 Citation display with relevance scores
- 🔄 Session management
- 💡 Example questions by industry
- 🎨 Clean, responsive design
- 🔌 Backend health monitoring

### Quick Start

1. **Install Dependencies**
   ```bash
   cd frontend
   pip install -r requirements.txt
   ```

2. **Start Backend** (in separate terminal)
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload
   ```

3. **Run Streamlit App**
   ```bash
   cd frontend
   streamlit run streamlit_app.py
   ```

4. **Access the UI**
   - Open browser to: `http://localhost:8501`

### Usage

- Type questions in the chat input
- Click example questions from the sidebar
- View citations with relevance scores
- Start new sessions to reset conversation history

---

## JavaScript Chat Widget (Future)

Embeddable JavaScript chat widget for website integration.

### Features (Planned)

- Lightweight and performant
- Easy integration via script tag
- Responsive design
- Customizable theme and colors
- Session persistence
- Markdown rendering for rich responses

## Integration

### Simple Script Tag

```html
<script src="https://your-cdn.azureedge.net/chat-widget.js"></script>
<script>
  window.IndustrySolutionsChat.init({
    apiEndpoint: 'https://your-api.azurewebsites.net',
    theme: 'auto', // 'light', 'dark', or 'auto'
    primaryColor: '#0078d4',
    position: 'bottom-right' // or 'bottom-left'
  });
</script>
```

### React Component (if building custom integration)

```jsx
import { IndustrySolutionsChat } from '@industry-solutions/chat-widget';

function App() {
  return (
    <IndustrySolutionsChat
      apiEndpoint="https://your-api.azurewebsites.net"
      theme="light"
      primaryColor="#0078d4"
    />
  );
}
```

## Development

### Install Dependencies

```bash
npm install
```

### Run Development Server

```bash
npm run dev
```

### Build for Production

```bash
npm run build
```

This creates a bundled JavaScript file in `dist/` that can be hosted on Azure CDN or Static Web Apps.

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `apiEndpoint` | string | (required) | Backend API URL |
| `theme` | string | 'auto' | Color theme: 'light', 'dark', or 'auto' |
| `primaryColor` | string | '#0078d4' | Primary brand color |
| `position` | string | 'bottom-right' | Widget position on screen |
| `initialMessage` | string | null | Show initial greeting message |
| `placeholder` | string | 'Ask about solutions...' | Input placeholder text |
| `maxHeight` | string | '600px' | Maximum chat window height |

## Customization

### Custom Styles

Override default styles by including custom CSS:

```html
<style>
  .industry-chat-widget {
    --primary-color: #0078d4;
    --secondary-color: #005a9e;
    --text-color: #323130;
    --background-color: #ffffff;
  }
</style>
```

### Event Listeners

Listen to widget events:

```javascript
window.IndustrySolutionsChat.on('message:sent', (data) => {
  console.log('User sent message:', data.message);
});

window.IndustrySolutionsChat.on('message:received', (data) => {
  console.log('AI response:', data.response);
});

window.IndustrySolutionsChat.on('error', (error) => {
  console.error('Chat error:', error);
});
```

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## License

Proprietary and confidential.
