# Fix for Render Deployment Error

## Problem
You're getting: `ModuleNotFoundError: No module named 'distutils'`

This happens because:
- Render is using Python 3.13 (or 3.12+)
- `distutils` was removed in Python 3.12+
- `eventlet` still tries to import `distutils`

## Solution

### Option 1: Use Python 3.11 (Recommended)

In Render Dashboard:
1. Go to your service settings
2. Under "Environment", set **Python Version** to `3.11.9`
3. Or add environment variable: `PYTHON_VERSION` = `3.11.9`
4. Redeploy

The `runtime.txt` file already specifies Python 3.11, but you may need to set it manually in Render.

### Option 2: Use Alternative Start Command (No eventlet)

If Python 3.11 doesn't work, use this start command instead:

**Start Command:**
```
python app.py
```

This uses the built-in SocketIO server instead of gunicorn+eventlet.

### Option 3: Use gevent instead of eventlet

Update `requirements.txt`:
```
gevent==23.9.1
gevent-websocket==0.10.1
```

**Start Command:**
```
gunicorn --worker-class gevent --worker-connections 1000 --bind 0.0.0.0:$PORT app:app
```

## Quick Fix Steps

1. **In Render Dashboard:**
   - Go to your web service
   - Click "Environment"
   - Add/Edit: `PYTHON_VERSION` = `3.11.9`
   - Save changes
   - Manual Deploy → Clear build cache & deploy

2. **Or use simpler start command:**
   - Change Start Command to: `python app.py`
   - This avoids the eventlet/gunicorn issue entirely

## Recommended Settings for Render

**Build Command:**
```
pip install -r requirements.txt
```

**Start Command (Option A - with gunicorn):**
```
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app
```
*(Requires Python 3.11)*

**Start Command (Option B - simpler):**
```
python app.py
```
*(Works with any Python version)*

**Environment Variables:**
- `SECRET_KEY` = (your random string)
- `PYTHON_VERSION` = `3.11.9` (optional, but recommended)

