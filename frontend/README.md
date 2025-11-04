# Frontend Chat Widget

Embeddable JavaScript chat widget for the Industry Solutions Directory.

## Features

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
