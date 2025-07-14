import discord
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import os

CATEGORY_STYLES = {
    "work":      {"emoji": "💼", "color": "🟦"},
    "study":     {"emoji": "📘", "color": "🟩"},
    "gym":       {"emoji": "💪", "color": "🟥"},
    "personal":  {"emoji": "🧘", "color": "🟨"},
    "project":   {"emoji": "🛠️", "color": "🟪"},
    "default":   {"emoji": "📝", "color": "⚪"},
}

class ScheduleManager:
    def __init__(self, storage_path='schedule_data.json'):
        self.storage_path = storage_path
        self.tasks: Dict[int, List[Dict]] = {}
        self.next_task_id = 1
        self._load_data()

    def _load_data(self):
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r') as f:
                data = json.load(f)

            raw_tasks = data.get("tasks", {})
            self.tasks = {}

            for key, task_list in raw_tasks.items():
                user_id = int(key)
                if user_id not in self.tasks:
                    self.tasks[user_id] = []
                self.tasks[user_id].extend(task_list)  # merge if duplicates found

            # Rebuild task ID counter from all tasks
            all_ids = [task['id'] for tasks in self.tasks.values() for task in tasks]
            self.next_task_id = max(all_ids, default=0) + 1

    def _save_data(self):
        # Convert keys to strings to ensure valid JSON keys
        serializable_tasks = {str(k): v for k, v in self.tasks.items()}
        with open(self.storage_path, 'w') as f:
            json.dump({
                "tasks": serializable_tasks,
                "next_task_id": self.next_task_id
            }, f, indent=2)

    def _get_user_tasks(self, user_id: int) -> List[Dict]:
        """Get all tasks for a specific user"""
        if user_id not in self.tasks:
            self.tasks[user_id] = []
        return self.tasks[user_id]
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string in YYYY-MM-DD format"""
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            raise ValueError(f"Invalid date format '{date_str}'. Use YYYY-MM-DD format (e.g., 2024-12-25)")
    
    def _parse_time(self, time_str: str) -> tuple:
        """Parse time string in HH:MM format, return (hour, minute)"""
        try:
            time_obj = datetime.strptime(time_str, '%H:%M')
            return time_obj.hour, time_obj.minute
        except ValueError:
            raise ValueError(f"Invalid time format '{time_str}'. Use HH:MM format (e.g., 09:30, 14:45, 23:30)")
    
    def _validate_time_range(self, hour: int) -> bool:
        """Check if time is within display range (7 AM to 12 AM / midnight)"""
        return 7 <= hour <= 23 or hour == 0  # 7 AM to 11 PM, plus midnight (0)
    
    def _format_time_display(self, hour: int, minute: int) -> str:
        """Format time for display in 12-hour format"""
        if hour == 0:
            return f"12:{minute:02d} AM"
        elif hour < 12:
            return f"{hour}:{minute:02d} AM"
        elif hour == 12:
            return f"12:{minute:02d} PM"
        else:
            return f"{hour-12}:{minute:02d} PM"
    
    def add_task(self, user_id: int, title: str, description: str = "", date_str: str = None, time_str: str = None, category: str = "default") -> Dict[str, Any]:

        """Add a new task to the schedule"""
        try:
            # Parse date (default to today if not provided)
            if date_str is None:
                task_date = datetime.now()
            else:
                task_date = self._parse_date(date_str)

            # Parse time (default to 9:00 AM if not provided)
            if time_str is None:
                hour, minute = 9, 0
            else:
                hour, minute = self._parse_time(time_str)

            # Validate time range
            if not self._validate_time_range(hour):
                return {
                    'success': False,
                    'error': f"Time must be between 7:00 AM and 12:00 AM (midnight). You entered {self._format_time_display(hour, minute)}."
                }

            user_tasks = self._get_user_tasks(user_id)

            # 🛡️ Ensure the next_task_id isn't already used (safe guard)
            existing_ids = {task['id'] for task_list in self.tasks.values() for task in task_list}
            while self.next_task_id in existing_ids:
                self.next_task_id += 1

            # Create task
            task = {
                'id': self.next_task_id,
                'title': title,
                'description': description,
                'date': task_date.strftime('%Y-%m-%d'),
                'time': f"{hour:02d}:{minute:02d}",
                'hour': hour,
                'minute': minute,
                "category": category.lower(),
                'created_at': datetime.now().isoformat()
            }

            user_tasks.append(task)
            user_tasks.sort(key=lambda x: (x['date'], x['hour'], x['minute']))
            self.next_task_id += 1
            self._save_data()

            return {
                'success': True,
                'task_id': task['id'],
                'date': task['date'],
                'time': task['time']
            }

        except ValueError as e:
            return {
                'success': False,
                'error': str(e)
            }

    def edit_task(self, user_id: int, task_id: int, new_title: Optional[str] = None,
              new_description: Optional[str] = None, new_date: Optional[str] = None,
              new_time: Optional[str] = None) -> Dict[str, Any]:
        """Edit an existing task"""
        try:
            user_tasks = self._get_user_tasks(user_id)
            
            # Find the task
            task_index = None
            for i, task in enumerate(user_tasks):
                if task['id'] == task_id:
                    task_index = i
                    break
            
            if task_index is None:
                return {
                    'success': False,
                    'error': f"Task with ID {task_id} not found."
                }
            
            if new_title is not None:
                task['title'] = new_title

            task = user_tasks[task_index]
            
            # Update description if provided
            if new_description is not None:
                task['description'] = new_description
            
            # Update date if provided
            if new_date is not None:
                parsed_date = self._parse_date(new_date)
                task['date'] = parsed_date.strftime('%Y-%m-%d')
            
            # Update time if provided
            if new_time is not None:
                hour, minute = self._parse_time(new_time)
                
                if not self._validate_time_range(hour):
                    return {
                        'success': False,
                        'error': f"Time must be between 7:00 AM and 12:00 AM (midnight). You entered {self._format_time_display(hour, minute)}."
                    }
                
                task['time'] = f"{hour:02d}:{minute:02d}"
                task['hour'] = hour
                task['minute'] = minute
            
            # Re-sort tasks
            user_tasks.sort(key=lambda x: (x['date'], x['hour'], x['minute']))
            self._save_data()

            return {
                'success': True,
                'task_id': task_id
            }
            
        except ValueError as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_task(self, user_id: int, task_id: int) -> Dict[str, Any]:
        """Delete a task from the schedule"""
        user_tasks = self._get_user_tasks(user_id)

        for i, task in enumerate(user_tasks):
            if task['id'] == task_id:
                deleted_task = user_tasks.pop(i)
                if not user_tasks:
                    del self.tasks[user_id]
                self._save_data()  # ✅ Save after deletion
                return {
                    'success': True,
                    'deleted_task': deleted_task
                }

        return {
            'success': False,
            'error': f"Task with ID {task_id} not found."
        }
    
    def get_schedule_display(self, user_id: int) -> discord.Embed:
        """Outlook-style horizontal schedule with stylized inline formatting."""
        user_tasks = self._get_user_tasks(user_id)
        today = datetime.now()
        dates = [(today + timedelta(days=i)) for i in range(5)]

        embed = discord.Embed(
            title="📅 Your Weekly Outlook",
            color=discord.Color.dark_blue()
        )

        color_emojis = ['🟢', '🔵', '🟣', '🟡', '🟠', '🔴', '🟤']

        for idx, date in enumerate(dates):
            date_str = date.strftime('%Y-%m-%d')
            display_date = f"**{date.strftime('%a %b %d')}**"
            day_tasks = [task for task in user_tasks if task['date'] == date_str]
            day_tasks.sort(key=lambda x: (x['hour'], x['minute']))

            if day_tasks:
                task_lines = []
                for task in day_tasks:
                    time = self._format_time_display(task['hour'], task['minute'])
                    category = task.get("category", "default")
                    emoji = CATEGORY_STYLES.get(category, CATEGORY_STYLES["default"])["emoji"]
                    title = task.get('title', '[Untitled Task]')[:60]
                    task_lines.append(f"{emoji} **{title}**\n`{time}`")
                value = "\n\n".join(task_lines)
            else:
                value = "❌ *No tasks scheduled*"

            embed.add_field(name=display_date, value=value, inline=True)

        embed.set_footer(text="🧠 Use /menu or buttons to manage your tasks.")
        return embed


    def list_user_tasks(self, user_id: int) -> discord.Embed:
        """List all tasks for a user with their IDs"""
        user_tasks = self._get_user_tasks(user_id)
        
        embed = discord.Embed(
            title="📋 Your Tasks",
            color=discord.Color.green()
        )
        
        if not user_tasks:
            embed.description = "You have no tasks scheduled."
            return embed
        
        # Group tasks by date
        tasks_by_date = {}
        for task in user_tasks:
            date = task['date']
            if date not in tasks_by_date:
                tasks_by_date[date] = []
            tasks_by_date[date].append(task)
        
        # Display tasks grouped by date
        for date_str in sorted(tasks_by_date.keys()):
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            day_name = date_obj.strftime('%A')
            display_date = date_obj.strftime('%B %d, %Y')
            
            tasks_text = ""
            for task in tasks_by_date[date_str]:
                task_time_display = self._format_time_display(task['hour'], task['minute'])
                title = task.get('title', '[Untitled Task]')
                tasks_text += f"**ID {task['id']}** - {task_time_display} - {title}\n"
                desc = task.get('description')
                if desc:
                    tasks_text += f"> {desc[:80]}\n"

            
            embed.add_field(
                name=f"{day_name} ({display_date})",
                value=tasks_text,
                inline=False
            )
        
        embed.set_footer(text=f"Total tasks: {len(user_tasks)}")
        
        return embed
    
    def get_user_task_count(self, user_id: int) -> int:
        """Get the total number of tasks for a user"""
        return len(self._get_user_tasks(user_id))
    
    def clear_user_tasks(self, user_id: int) -> Dict[str, Any]:
        """Clear all tasks for a user (admin function)"""
        user_tasks = self._get_user_tasks(user_id)
        cleared_count = len(user_tasks)
        self.tasks[user_id] = []
        self._save_data()

        return {
            'success': True,
            'cleared_count': cleared_count
        }