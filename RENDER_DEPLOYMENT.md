# Render Deployment Guide

## Quick Setup for Render

### Step 1: Push to GitHub
Make sure your code is pushed to a GitHub repository.

### Step 2: Deploy on Render

1. Go to [render.com](https://render.com) and sign up/login
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Select your repository

### Step 3: Configure Settings

**Basic Settings:**
- **Name:** `live-match-viewer` (or any name you prefer)
- **Region:** Choose closest to you
- **Branch:** `main` (or your default branch)
- **Root Directory:** Leave empty (or `.` if needed)

**Build & Deploy:**
- **Environment:** `Python 3`
- **Python Version:** `3.11.9` (IMPORTANT: Set this to avoid distutils error)
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app`

**OR (Simpler alternative - works with any Python version):**
- **Start Command:** `python app.py`

### Step 4: Environment Variables

Click **"Advanced"** → **"Add Environment Variable"**

Add:
- **Key:** `SECRET_KEY`
- **Value:** Generate a random string (e.g., use: `python -c "import secrets; print(secrets.token_hex(32))"`)

### Step 5: Deploy

Click **"Create Web Service"** and wait for deployment.

## Commands Summary

### Build Command:
```
pip install -r requirements.txt
```

### Start Command (Recommended - Production):
```
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app
```

### Start Command (Alternative - Simpler):
```
python app.py
```

## Important Notes

1. **WebSocket Support:** Render supports WebSockets, so your SocketIO will work fine.

2. **Port:** Render automatically sets the `PORT` environment variable. Your app already reads it.

3. **SECRET_KEY:** Make sure to set a strong secret key in environment variables.

4. **Free Tier:** Render's free tier:
   - Spins down after 15 minutes of inactivity
   - Takes ~30 seconds to wake up
   - Perfect for testing and small projects

5. **Upgrade:** For always-on service, upgrade to paid plan ($7/month).

## Troubleshooting

- **Build fails:** Check that all dependencies are in `requirements.txt`
- **App crashes:** Check logs in Render dashboard
- **WebSocket not working:** Make sure you're using the gunicorn command with eventlet
- **Port errors:** Make sure your app uses `os.environ.get('PORT', 5000)`

## Testing After Deployment

1. Visit your Render URL: `https://your-app-name.onrender.com`
2. Test API: `https://your-app-name.onrender.com/api/test`
3. Subscribe to a match and verify real-time updates work

## Auto-Deploy

Render automatically deploys when you push to your connected branch (usually `main`).

