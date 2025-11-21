# Live Match Viewer

A real-time sports match viewer built with Flask and SocketIO that displays live football and cricket scores from ESPN API.

## Features

- ⚽ Live football scores (College Football)
- 🏏 Live cricket scores
- Real-time updates via WebSocket
- Modern, responsive UI
- No API key required (uses ESPN public API)

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Open your browser to `http://localhost:5000`

## Environment Variables


- `PORT`: Server port (usually set automatically by platform)

## Project Structure

```
.
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── Procfile           # Process file for deployment
├── runtime.txt        # Python version
├── templates/
│   └── index.html     # Frontend UI
└── README.md          # This file
```




