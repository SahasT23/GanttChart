# 📊 Gantt Chart Application

## TODO

* Need to add a migration script for the code.
* Need to add a method for automated email messages as well as user friendly method to add their email, as well as a way for a user to set the time and days that you want a reminder email, along with a method that let's you select time blocks etc. Need to use the Gmail API for free emails. May need to set up a workflow for sending emails, not sure about that yet. 



A beautiful and powerful project management tool with a Gantt chart interface. Built with Python and SQLite - perfect for managing projects, tasks, and deadlines!

![Project Management](https://img.shields.io/badge/Type-Project%20Management-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![SQLite](https://img.shields.io/badge/Database-SQLite-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ What Can This Do?

- 📋 **Create and manage tasks** with start/end dates
- 🔗 **Task dependencies** - link tasks that depend on each other
- 📊 **Visual timeline** - see all your tasks on a Gantt chart
- 🎯 **Milestones** - mark important project deadlines
- 📁 **Subtasks** - organize tasks into hierarchies
- 🎨 **Color coding** - categorize tasks with colors
- 📈 **Progress tracking** - track completion percentage
- 📝 **Action history** - see who changed what and when
- 🔍 **Search and filter** - find tasks quickly
- 💾 **Auto-save** - everything is saved automatically

## 🖼️ What Does It Look Like?

The interface shows:
- Left sidebar: List of all tasks (expandable/collapsible)
- Right side: Visual timeline showing when tasks happen
- Top toolbar: Buttons for zooming, searching, and adding tasks
- Task bars: Colored bars showing task duration and progress

```bash
gantt-chart-app/
├── main.py              # The main server application
├── database.py          # Database operations
├── requirements.txt     # Python packages needed
├── .gitignore          # Tells Git what files to ignore
├── README.md           # This file!
├── static/
│   └── index.html      # The web interface
└── gantt_app.db        # Your database (created automatically)
```

## 📋 Before You Start

Make sure you have these installed on your computer:

1. **Python 3.8 or newer**
   - Check by opening a terminal and typing: `python --version` or `python3 --version`
   - Don't have it? Download from [python.org](https://www.python.org/downloads/)

2. **pip** (Python package installer)
   - Usually comes with Python
   - Check by typing: `pip --version` or `pip3 --version`

3. **Git** (optional, for cloning)
   - Download from [git-scm.com](https://git-scm.com/)

## 🚀 Installation Instructions

### Step 1: Download the Code

**Option A: Using Git (Recommended)**
```bash
# Open your terminal and run:
git clone https://github.com/yourusername/gantt-chart-app.git
cd gantt-chart-app
```

## Option B: Download ZIP

1. Click the green "Code" button on GitHub
2. Click "Download ZIP"
3. Extract the ZIP file to a folder
4. Open terminal/command prompt in that folder

### Step 2: Create a Virtual Environment
A virtual environment keeps this project's dependencies separate from other Python projects.

#### For Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### On Mac/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

You'll see ```(venv)``` appear at the start of your terminal line - this means it's working properly.

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs all the necessary Python packages (FastAPI, Uvicorn, etc.) and you can start the application with command below:

```bash
python main.py
```

You should see:

```
✓ Database initialized: gantt_app.db
✓ Database ready
Starting Gantt Chart Application with SQLite...
Access the application at: http://localhost:8000
```

## 💾 Your Data
All your tasks are saved in gantt_app.db - a SQLite database file.
### ⚠️ Important: This file contains all your project data!

### Backing Up Your Data

#### Method 1: Copy the database file

```bash
cp gantt_app.db gantt_app_backup.db
```
### Method 2: Export to JSON

Open your browser and go to:
```http://localhost:8000/api/export?format=json```

Save the file that downloads.

### Restoring from Backup

Just replace ```gantt_app.db``` with your backup file and restart the app.

#### 🔧 Troubleshooting

```"Command not found: python"```

Try python3 instead of python:

```python3 main.py```

```"Port 8000 is already in use"```

Something else is using port 8000. Either:

1. Close the other application
2. Or change the port in main.py:

``` uvicorn.run(app, host="0.0.0.0", port=8001)  # Change to 8001```
Then visit http://localhost:8001

### "Module not found" errors

Make sure you:

1. Activated the virtual environment (you should see (venv) in terminal)
2. Ran pip install -r requirements.txt

### Can't see any tasks?

1. Check if the database was created: look for ```gantt_app.db``` in your folder
2. Try refreshing your browser (F5)
3. Check the terminal for error messages

### Database is locked

1. Close any other programs that might be using the database
2. Restart the application

#### Need to start fresh?

Delete ```gantt_app.db``` and restart the app - it will create a new empty database.

### 🎯 Quick Tips

1. Use meaningful task names - "Design homepage" instead of "Task 1"
2. Color code by category - Blue for development, green for design, etc.
3. Set realistic dates - You can always adjust them later
4. Use subtasks - Break big tasks into smaller chunks
5. Update progress - Keep the progress % up to date
6. Regular backups - Export your data weekly

### ⌨️ Keyboard Shortcuts

1. Ctrl+N (Cmd+N on Mac): Create new task
2. Escape: Close modal/dialog
3. Delete: Delete selected task (after confirmation)

### 🆘 Getting Help
1. Check the logs
2. The terminal where you ran python main.py shows helpful error messages.
3. Reset everything
4.  Stop the app (Ctrl+C in terminal)

# Delete the database

```rm gantt_app.db  # On Mac/Linux```
```del gantt_app.db  # On Windows```

# Restart the app

```python main.py```

Still stuck?

Create an issue on GitHub with:

1. What you were trying to do
2. What happened instead
3. Any error messages from the terminal
4. Your operating system (Windows/Mac/Linux)

### 📚 Learn More

* FastAPI Documentation: fastapi.tiangolo.com
* SQLite Tutorial: sqlitetutorial.net
* Python Basics: python.org/about/gettingstarted

🤝 Contributing
Want to add features or fix bugs?

1. Fork the repository
2. Create a new branch: git checkout -b my-feature
3. Make your changes
4. Test them
5. Commit: git commit -am 'Add new feature'
6. Push: git push origin my-feature
7. Create a Pull Request

### 🎓 For Beginners: Understanding the Code
What is this app made of?
Backend (Server) - Python:

main.py: Handles requests from your browser, manages data
database.py: Talks to the SQLite database

Frontend (Browser) - HTML/CSS/JavaScript:

static/index.html: The visual interface you see and interact with

Database - SQLite:

gantt_app.db: Stores all your tasks, logs, and settings

How does it work?

You open the app in your browser (http://localhost:8000)
Your browser sends a request to the Python server
The server reads data from the SQLite database
The server sends HTML/CSS/JavaScript to your browser
Your browser displays the Gantt chart
When you add/edit tasks, the browser sends data back to the server
The server saves it to the database

Want to learn more?
Start by reading the code in this order:

static/index.html - See how the interface works
database.py - Understand how data is stored
main.py - Learn how the server handles requests
