# 📅 Personal Discord Bot 

A better Discord bot for scheduling personal tasks and keeping track of your weekly activities — with an intuitive button-based interface, category tagging, and multi-user support.

---

## ✨ Features

- ✅ **Add, edit, delete tasks** with category, description, time, and date
- 📆 **View your upcoming 5-day schedule** with clean embed formatting
- 🧘 **Categorize tasks**: Work, Study, Gym, Project, Personal, Other
- 👥 **Multi-user support** — each user’s schedule is separate and private
- 📎 **View another user’s schedule** (if enabled)
- 🎨 **Custom date & time pickers** for easy task creation
- 🔒 **Ephemeral replies** to keep your schedule private
- 🔁 **Periodic menu reminders** (every 6 hours)

---

## 🚀 Getting Started

1. **Install dependencies**  
   Make sure you're using Python 3.9+  
   ```bash
   pip install -r requirements.txt
Configure your bot
Replace the token in main.py with your own Discord bot token:

python
Copy
Edit
bot.run("YOUR_BOT_TOKEN")
Run the bot

bash
Copy
Edit
python3 main.py
Invite the bot to your server
Make sure the bot has Message, Embed Links, Use Slash Commands, and Manage Messages permissions.

🧠 Usage
!menu — Show the interactive schedule menu

!add "Task Name" [YYYY-MM-DD] [HH:MM] — Quick add a task

!schedule — View your 5-day schedule

📅 View Schedule — Button to show your upcoming tasks

➕ Add Task — Launches date/time picker + modal to add task

📋 List Tasks — View all your tasks with IDs (for edit/delete)

📎 View Another’s Schedule — Pick a user and view their week

❓ Help — Embedded instructions for using the bot

📁 Data Structure
All user tasks are saved in schedule_data.json, separated by user ID:

json
Copy
Edit
{
  "tasks": {
    "668521341749690420": [
    {
        "id": 1,
        "title": "Gym",
        "description": "Leg day",
        "date": "2025-07-15",
        "time": "18:00",
        "category": "gym"
      }
    ]
  }
}
🛠️ Tech Stack
discord.py 2.3+ (UI, views, modals, select menus)

Python 3.9+

JSON for persistent local storage

🤝 Contributions
This project is for personal use but can be extended for teams, shared schedules, calendar export, Google Sheets integration, and more.

Pull requests welcome!
