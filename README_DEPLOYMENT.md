# 🚀 Deployment Guide for Call Analysis App on Hugging Face Spaces

This guide will walk you through deploying the Call Analysis App to **Hugging Face Spaces** for **FREE hosting** with Docker support.

---

## 📋 Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Creating a Hugging Face Account](#creating-a-hugging-face-account)
4. [Creating a New Space](#creating-a-new-space)
5. [Deploying Your Code](#deploying-your-code)
6. [Configuration](#configuration)
7. [Accessing Your Application](#accessing-your-application)
8. [Persistent Storage](#persistent-storage)
9. [Troubleshooting](#troubleshooting)
10. [Local Testing](#local-testing)

---

## 🎯 Overview

**Hugging Face Spaces FREE Tier Specifications:**
- **RAM**: 16GB
- **CPU**: 2 cores
- **Storage**: 50GB
- **Automatic HTTPS**: Yes
- **Custom Domain**: Available
- **No Credit Card Required**: ✅

**What This Deployment Includes:**
- ✅ Main Call Analysis App (Port 8501)
- ✅ Dashboard App (Port 8503)
- ✅ SQLite Database with persistence
- ✅ Audio processing with FFmpeg
- ✅ NLP models (spaCy, Whisper)
- ✅ Automatic health checks

**Estimated Time:**
- Account creation: 2-3 minutes
- Space setup: 5 minutes
- Build time: 5-10 minutes
- **Total**: ~15-20 minutes

---

## ✅ Prerequisites

Before starting, ensure you have:

1. **A GitHub account** (if you want to sync with GitHub)
2. **Git installed** on your local machine
3. **Basic familiarity with command line** (optional but helpful)
4. **This repository cloned** to your local machine

---

## 🆕 Creating a Hugging Face Account

If you don't already have a Hugging Face account:

### Step 1: Sign Up
1. Go to [https://huggingface.co/join](https://huggingface.co/join)
2. Fill in the registration form:
   - **Email address**
   - **Username** (will be part of your app URL)
   - **Password**
3. Click **"Sign Up"**
4. Check your email for verification link
5. Click the verification link to activate your account

### Step 2: Verify Your Account
1. Log in to [https://huggingface.co](https://huggingface.co)
2. Complete any additional profile setup if prompted

**✅ Checkpoint**: You should now be logged into Hugging Face!

---

## 🏗️ Creating a New Space

### Step 1: Navigate to Spaces
1. Click on your profile icon (top right)
2. Select **"New Space"** from the dropdown
   - Or go directly to: [https://huggingface.co/new-space](https://huggingface.co/new-space)

### Step 2: Configure Your Space

Fill in the following details:

**Basic Information:**
- **Owner**: Select your username or organization
- **Space name**: `call-analysis-app` (or your preferred name)
  - This will be part of your URL: `https://huggingface.co/spaces/YOUR_USERNAME/call-analysis-app`
- **License**: Choose `mit` or `apache-2.0` (recommended)
- **Visibility**: 
  - Select **"Public"** for free hosting
  - Or **"Private"** if you have a paid plan

**SDK Selection:**
- **Space SDK**: Select **"Docker"** ⚠️ **IMPORTANT**
  - Do NOT select "Streamlit" or "Gradio"
  - We need full Docker control for running two apps

**Hardware:**
- **Space hardware**: Select **"CPU basic - Free"**
  - This gives you 16GB RAM and 2 CPU cores
  - Sufficient for this application

### Step 3: Create Space
1. Review all settings
2. Click **"Create Space"**
3. Wait for the Space to be created (takes a few seconds)

**✅ Checkpoint**: You should now see your new Space page with upload instructions!

---

## 📤 Deploying Your Code

You have **two options** for deploying your code to Hugging Face Spaces:

### Option A: Using Git (Recommended)

#### Step 1: Get Your Space Git URL
On your Space page, you'll see Git instructions. The URL format is:
```
https://huggingface.co/spaces/YOUR_USERNAME/call-analysis-app
```

#### Step 2: Add Hugging Face as a Remote
Open your terminal in the repository directory and run:

```bash
# Navigate to your repository
cd /path/to/CallAnalysisApp

# Add Hugging Face Spaces as a git remote
git remote add space https://huggingface.co/spaces/YOUR_USERNAME/call-analysis-app

# Push your code to the Space
git push space main
```

**If your branch is named differently** (e.g., `master`):
```bash
git push space master:main
```

#### Step 3: Enter Credentials
- **Username**: Your Hugging Face username
- **Password**: Your Hugging Face **Access Token** (not your account password)

**To get your Access Token:**
1. Go to [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Click **"New token"**
3. Give it a name (e.g., "Call Analysis Deploy")
4. Select **"write"** permission
5. Click **"Generate"**
6. Copy the token and use it as your password

### Option B: Using Web Interface

#### Step 1: Prepare Files
1. Make sure all deployment files are in your repository root:
   - `Dockerfile`
   - `start.sh`
   - `.dockerignore`
   - `docker-compose.yml` (for local testing only)
   - All Python files and dependencies

#### Step 2: Upload Files
1. On your Space page, click **"Files"** tab
2. Click **"Add file"** → **"Upload files"**
3. Select and upload all necessary files:
   - All `.py` files
   - `config.yaml`
   - `requirements.txt`
   - `Dockerfile`
   - `start.sh`
   - `fonts/` directory
   - `dejavu-sans-ttf-2.37/` directory
4. Click **"Commit changes to main"**

**Note**: For large uploads, Git method (Option A) is more reliable.

**✅ Checkpoint**: Your code should now be uploading/building!

---

## ⚙️ Configuration

### Environment Variables (Optional)

If you need to set environment variables:

#### Step 1: Access Space Settings
1. Go to your Space page
2. Click **"Settings"** tab

#### Step 2: Add Variables
1. Scroll to **"Repository secrets"**
2. Click **"New secret"**
3. Add any required environment variables from `.env.example`:

Example variables you might want to set:
- `DATABASE_PATH=call_analysis.db`
- `WHISPER_MODEL_SIZE=base`
- `LOG_LEVEL=INFO`

#### Step 3: Save
Click **"Save"** after adding each variable.

### Persistent Storage

The database (`call_analysis.db`) will be stored in the Space's persistent storage automatically. 

**Important Notes:**
- Hugging Face Spaces provides persistent storage
- Your database will survive app restarts
- If you delete and recreate the Space, data will be lost

---

## 🌐 Accessing Your Application

### Step 1: Wait for Build
After pushing your code, the build process will start automatically.

**What happens during build:**
1. Docker image is built (~5-10 minutes)
2. System dependencies installed (ffmpeg, git)
3. Python packages installed from `requirements.txt`
4. spaCy model downloaded
5. Health checks performed
6. Applications started

**Monitor Build Progress:**
- On your Space page, click the **"Build"** tab
- Watch the build logs in real-time
- Look for any errors (red text)

### Step 2: Access Your Apps

Once the build completes and status shows **"Running"**, you can access your applications:

**Main Call Analysis App:**
```
https://YOUR_USERNAME-call-analysis-app.hf.space
```

**Dashboard App:**
The dashboard runs on port 8503. Hugging Face Spaces Docker containers can expose multiple ports.

**Access methods:**
1. **Primary URL** (port 8501 - main app):
   ```
   https://YOUR_USERNAME-call-analysis-app.hf.space
   ```

2. **Dashboard** (port 8503):
   - Hugging Face Spaces will detect the exposed ports automatically
   - Look for a port selector in the Hugging Face interface
   - The exact URL format may vary, but typically accessible through the HF interface
   - Check the Space's "App" section for available endpoints

**Note:** Hugging Face Spaces may require you to configure port visibility in the Space settings. If the dashboard is not automatically accessible, you may need to:
- Check the Space settings for port configuration
- Refer to Hugging Face Spaces documentation for multi-port Docker apps
- Access the dashboard through the main app if it provides navigation links

For the most up-to-date information on accessing multiple ports, see:
[Hugging Face Spaces Docker Documentation](https://huggingface.co/docs/hub/spaces-sdks-docker)

### Step 3: Test Your Application

1. **Test Main App:**
   - Upload a sample audio file
   - Run transcription
   - Check scoring functionality

2. **Test Dashboard:**
   - View existing call analyses
   - Check visualizations
   - Verify data persistence

**✅ Checkpoint**: Both apps should be accessible and functional!

---

## 💾 Persistent Storage

### Database Persistence

Your SQLite database (`call_analysis.db`) is automatically persisted by Hugging Face Spaces.

**How it works:**
- The database is stored in the Space's file system
- It persists across app restarts
- It survives code updates
- It's included in Space backups

### Backing Up Your Data

**Recommended: Regular backups**

To download your database:
1. Go to your Space page
2. Click **"Files and versions"** tab
3. Navigate to `call_analysis.db`
4. Click the download button

**Automated backup (advanced):**
You can set up a scheduled task to backup your database to Hugging Face Datasets or external storage.

### Database Size Limits

- **Free tier**: 50GB total storage
- Current database: ~13MB
- You have plenty of room for growth!

**Monitor storage:**
- Check Space settings for storage usage
- Archive old data if needed

---

## 🔧 Troubleshooting

### Build Failures

**Symptom**: Build fails during Docker image creation

**Common causes and solutions:**

1. **Out of Memory during build**
   - Solution: Reduce model sizes in `requirements.txt`
   - Use smaller Whisper model: `WHISPER_MODEL_SIZE=tiny` or `base`

2. **Package installation fails**
   - Solution: Check `requirements.txt` for version conflicts
   - Look at build logs for specific package errors

3. **spaCy model download fails**
   - Solution: Add retry logic or download during runtime instead
   - Check internet connectivity in build environment

**How to fix:**
1. Review build logs in the "Build" tab
2. Make necessary code changes locally
3. Push updates: `git push space main`
4. Monitor new build

### Runtime Errors

**Symptom**: App builds successfully but crashes at runtime

**Common causes:**

1. **Port binding issues**
   - Ensure `start.sh` is executable: `chmod +x start.sh`
   - Verify ports 8501 and 8503 are correctly configured

2. **Missing files or directories**
   - Check that all required files are committed
   - Verify `.dockerignore` isn't excluding needed files

3. **Database access errors**
   - Ensure database path is correct
   - Check file permissions

**How to debug:**
1. Click **"Logs"** tab on your Space
2. Look for error messages
3. Check application startup logs

### Application Not Accessible

**Symptom**: Build successful, but can't access the app

**Solutions:**

1. **Wait for startup**
   - Apps may take 30-60 seconds to fully start
   - Check "Logs" tab for "Running" confirmation

2. **Check Space status**
   - Ensure Space status is "Running" (not "Sleeping")
   - Free Spaces may sleep after inactivity

3. **Port issues**
   - Verify you're using correct URLs
   - Try accessing via the Hugging Face interface first

### Database Issues

**Symptom**: Data not persisting or database errors

**Solutions:**

1. **Database locked**
   - SQLite can lock if multiple processes access it
   - Ensure proper database connection handling in code

2. **Permissions**
   - Check file permissions on `call_analysis.db`
   - Ensure app has write access

3. **Database corruption**
   - Download and check database file
   - Restore from backup if needed

### Performance Issues

**Symptom**: App is slow or unresponsive

**Solutions:**

1. **Resource limits**
   - Free tier has 16GB RAM limit
   - Monitor resource usage in Logs
   - Consider upgrading to paid tier if needed

2. **Model size**
   - Use smaller Whisper model (`tiny` or `base`)
   - Reduce concurrent processing

3. **Database optimization**
   - Add indexes if querying is slow
   - Archive old data

### Getting Help

If you're still stuck:

1. **Hugging Face Community Forums**
   - [https://discuss.huggingface.co/](https://discuss.huggingface.co/)
   - Search for similar issues or ask a question

2. **Hugging Face Discord**
   - Join: [https://hf.co/join/discord](https://hf.co/join/discord)
   - Ask in #spaces channel

3. **Documentation**
   - [Hugging Face Spaces Docs](https://huggingface.co/docs/hub/spaces)
   - [Docker Spaces Guide](https://huggingface.co/docs/hub/spaces-sdks-docker)

4. **Repository Issues**
   - Check repository README for app-specific issues
   - Create an issue if you find a bug

---

## 🧪 Local Testing

Before deploying to Hugging Face Spaces, you can test the Docker setup locally.

### Prerequisites
- Docker installed on your machine
- Docker Compose installed

### Using Docker Compose (Recommended)

#### Step 1: Create .env file (Optional)
```bash
# The .env file is OPTIONAL - all settings have defaults
# Copy the example file only if you want to customize settings
cp .env.example .env

# Edit if needed (optional)
nano .env
```

**Note:** If you don't create a .env file, the application will use default values.

#### Step 2: Build and run
```bash
# Build the Docker image
docker-compose build

# Start the application
docker-compose up
```

#### Step 3: Access locally
- **Main App**: [http://localhost:8501](http://localhost:8501)
- **Dashboard**: [http://localhost:8503](http://localhost:8503)

#### Step 4: Stop the application
```bash
# Stop with Ctrl+C, then remove containers
docker-compose down
```

### Using Docker Directly

If you prefer not to use Docker Compose:

```bash
# Build the image
docker build -t call-analysis-app .

# Run the container
docker run -p 8501:8501 -p 8503:8503 \
  -v $(pwd)/call_analysis.db:/app/call_analysis.db \
  call-analysis-app
```

### Testing Checklist

Before deploying to Hugging Face Spaces, verify:

- [ ] Docker image builds successfully
- [ ] Both apps start without errors
- [ ] Can access main app on port 8501
- [ ] Can access dashboard on port 8503
- [ ] Audio upload and transcription works
- [ ] Database saves data correctly
- [ ] Data persists after container restart
- [ ] No critical errors in logs

---

## 📝 Post-Deployment

### Updating Your App

To update your deployed application:

```bash
# Make your changes locally
git add .
git commit -m "Your update message"

# Push to Hugging Face Spaces
git push space main
```

The Space will automatically rebuild with your changes.

### Monitoring

**Check application health:**
1. Visit your Space URL regularly
2. Monitor the "Logs" tab for errors
3. Check the "Analytics" tab for usage stats

**Set up notifications:**
- Hugging Face can notify you of build failures
- Configure in Space settings

### Sharing Your App

**Your app URL:**
```
https://huggingface.co/spaces/YOUR_USERNAME/call-analysis-app
```

**Share options:**
- Share the URL directly
- Embed in website using Hugging Face widgets
- Add to your Hugging Face profile

### Making it Private

To restrict access:
1. Go to Space Settings
2. Change visibility to "Private"
3. Only you and collaborators can access

Note: Private Spaces may require a paid plan.

---

## 🎉 Success Checklist

You've successfully deployed when:

- [x] Space is created on Hugging Face
- [x] Code is pushed to Space repository
- [x] Docker build completes without errors
- [x] Space status shows "Running"
- [x] Main app is accessible at your Space URL
- [x] Dashboard is accessible on port 8503
- [x] Database persists data correctly
- [x] Audio processing works
- [x] No critical errors in logs

---

## 📚 Additional Resources

### Hugging Face Documentation
- [Spaces Overview](https://huggingface.co/docs/hub/spaces-overview)
- [Docker Spaces](https://huggingface.co/docs/hub/spaces-sdks-docker)
- [Managing Spaces](https://huggingface.co/docs/hub/spaces-settings)
- [Persistent Storage](https://huggingface.co/docs/hub/spaces-storage)

### Streamlit Documentation
- [Streamlit Docs](https://docs.streamlit.io/)
- [Deployment Guide](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app)

### Docker Documentation
- [Docker Overview](https://docs.docker.com/get-started/overview/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)

---

## 💡 Tips and Best Practices

1. **Version Control**: Always commit changes before pushing to Spaces
2. **Testing**: Test locally with Docker before deploying
3. **Backups**: Regularly backup your database
4. **Monitoring**: Check logs periodically for issues
5. **Updates**: Keep dependencies updated for security
6. **Documentation**: Document any custom configurations
7. **Resource Usage**: Monitor RAM and storage usage
8. **Security**: Don't commit sensitive data (API keys, passwords)

---

## 🎯 Next Steps

After successful deployment:

1. **Customize**: Update branding, colors, or features
2. **Optimize**: Tune model sizes for performance
3. **Scale**: Consider upgrading to paid tier for more resources
4. **Integrate**: Connect to external APIs or services
5. **Share**: Share your Space with colleagues or the community

---

**Need help?** Feel free to open an issue in the repository or ask on the Hugging Face forums!

**Happy Deploying! 🚀**
