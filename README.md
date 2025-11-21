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

## Deployment Options

### 1. **Railway** (Recommended - Easy & Free)

1. Go to [railway.app](https://railway.app)
2. Sign up/login with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Connect your repository
5. Railway will auto-detect Python and deploy
6. Add environment variable: `SECRET_KEY` (generate a random string)
7. Your app will be live at `https://your-app.railway.app`

**Pros:** Free tier, easy setup, supports WebSockets, auto-deploys on git push

### 2. **Render** (Free Tier Available)

1. Go to [render.com](https://render.com)
2. Sign up/login
3. Click "New" → "Web Service"
4. Connect your GitHub repository
5. Settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python app.py`
   - **Environment:** Python 3
6. Add environment variable: `SECRET_KEY`
7. Deploy!

**Pros:** Free tier, good documentation, supports WebSockets

### 3. **Fly.io** (Free Tier)

1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Login: `fly auth login`
3. Initialize: `fly launch`
4. Deploy: `fly deploy`

**Pros:** Free tier, global edge network, good performance

### 4. **Heroku** (Paid, but reliable)

1. Install Heroku CLI
2. Login: `heroku login`
3. Create app: `heroku create your-app-name`
4. Set config: `heroku config:set SECRET_KEY=your-secret-key`
5. Deploy: `git push heroku main`

**Note:** Heroku removed free tier, but still reliable for paid plans

### 5. **PythonAnywhere** (Free Tier, Limited)

1. Sign up at [pythonanywhere.com](https://www.pythonanywhere.com)
2. Upload your files via web interface
3. Configure web app
4. **Note:** Free tier has limitations with WebSockets

### 6. **DigitalOcean App Platform**

1. Go to [digitalocean.com](https://www.digitalocean.com)
2. Create App Platform project
3. Connect GitHub repo
4. Configure build and run commands
5. Deploy

**Pros:** Good performance, reasonable pricing

### 7. **AWS/GCP/Azure** (Advanced)

- **AWS:** Use Elastic Beanstalk or EC2
- **GCP:** Use App Engine or Cloud Run
- **Azure:** Use App Service

These require more setup but offer more control and scalability.

## Environment Variables

- `SECRET_KEY`: Flask secret key (required for production)
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

## Testing

Visit `/api/test` to test the API connection:
- `/api/test` - Test football API
- `/api/test/cricket` - Test cricket API

## Notes

- The app uses ESPN's public API which doesn't require authentication
- WebSocket support is required for real-time updates
- Some platforms may require additional configuration for WebSockets
- Make sure to set a strong `SECRET_KEY` in production

## License

MIT

