import discord
from discord.ext import commands
from discord import ui
from datetime import datetime, timedelta
from schedule_manager import ScheduleManager
import asyncio

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Initialize schedule manager
schedule_manager = ScheduleManager()

class MainMenuView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @ui.button(label='📅 View Schedule', style=discord.ButtonStyle.primary, emoji='📅', custom_id='view_schedule')
    async def view_schedule(self, interaction: discord.Interaction, button: ui.Button):
        user_id = interaction.user.id
        schedule_embed = schedule_manager.get_schedule_display(user_id)
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(embed=schedule_embed, ephemeral=True)

    
    @ui.button(label='➕ Add Task', style=discord.ButtonStyle.success, emoji='➕', custom_id='add_task')
    async def add_task(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message(
            content="🗂️ Choose a category for your new task:",
            view=CategorySelectView(),
            ephemeral=True
        )
    
    @ui.button(label='📋 List Tasks', style=discord.ButtonStyle.secondary, emoji='📋', custom_id='list_tasks')
    async def list_tasks(self, interaction: discord.Interaction, button: ui.Button):
        user_id = interaction.user.id
        tasks_embed = schedule_manager.list_user_tasks(user_id)
        
        # Add edit/delete buttons if user has tasks
        if schedule_manager.get_user_task_count(user_id) > 0:
            view = TaskManagementView(user_id)
            await interaction.response.send_message(embed=tasks_embed, view=view, ephemeral=True)
        else:
            await interaction.response.send_message(embed=tasks_embed, ephemeral=True)
    
    @ui.button(label="📎 View Another's Schedule", style=discord.ButtonStyle.secondary, emoji="📎", custom_id="view_other_schedule")
    async def view_other_schedule(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message(
            content="👤 Select a user:",
            view=UserSelectView(),
            ephemeral=True
        )

    @ui.button(label='❓ Help', style=discord.ButtonStyle.secondary, emoji='❓', custom_id='help_menu')
    async def help_command(self, interaction: discord.Interaction, button: ui.Button):
        help_embed = discord.Embed(
            title="📅 Schedule Bot Help",
            description="Use the buttons to interact with your schedule!",
            color=discord.Color.blue()
        )
        
        help_embed.add_field(
            name="📅 View Schedule",
            value="Display your schedule for the next 5 days (7 AM - 12 AM)",
            inline=False
        )
        
        help_embed.add_field(
            name="➕ Add Task",
            value="Add a new task to your schedule with description, date, and time",
            inline=False
        )
        
        help_embed.add_field(
            name="📋 List Tasks",
            value="View all your tasks with their IDs for editing/deleting",
            inline=False
        )
        
        help_embed.add_field(
            name="Date Format",
            value="Use YYYY-MM-DD format (e.g., 2024-12-25)",
            inline=True
        )
        
        help_embed.add_field(
            name="Time Format",
            value="Use HH:MM format (e.g., 09:30, 14:45, 23:30)",
            inline=True
        )
        
        await interaction.response.send_message(embed=help_embed, ephemeral=True)

class UserSelectView(ui.View):
    def __init__(self):
        super().__init__(timeout=30)
        self.add_item(ManualUserSelect())

class ManualUserSelect(ui.Select):
    def __init__(self):
        # 👤 Hardcoded users: label = name, value = user_id
        options = [
            discord.SelectOption(label="Parteek", value="668521341749690420", emoji="🧑🏾‍💻"),
            discord.SelectOption(label="Rain", value="760956176761356349", emoji="👱🏼‍♀️")
        ]

        super().__init__(
            placeholder="Select a user...",
            options=options,
            min_values=1,
            max_values=1,
            custom_id="manual_user_select"
        )

    async def callback(self, interaction: discord.Interaction):
        selected_id = int(self.values[0])
        embed = schedule_manager.get_schedule_display(selected_id)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class CategorySelectView(ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @ui.button(label="💼 Work", style=discord.ButtonStyle.primary, custom_id="cat_work")
    async def work(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message(
            content="Pick a date and time:",
            view=DateTimePickerView(category="work"),
            ephemeral=True
        )

    @ui.button(label="📘 Study", style=discord.ButtonStyle.primary, custom_id="cat_study")
    async def study(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message(
            content="Pick a date and time:",
            view=DateTimePickerView(category="study"),
            ephemeral=True
        )

    @ui.button(label="💪 Gym", style=discord.ButtonStyle.success, custom_id="cat_gym")
    async def gym(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message(
            content="Pick a date and time:",
            view=DateTimePickerView(category="gym"),
            ephemeral=True
        )

    @ui.button(label="🧘 Personal", style=discord.ButtonStyle.secondary, custom_id="cat_personal")
    async def personal(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message(
            content="Pick a date and time:",
            view=DateTimePickerView(category="personal"),
            ephemeral=True
        )

    @ui.button(label="🛠️ Project", style=discord.ButtonStyle.danger, custom_id="cat_project")
    async def project(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message(
            content="Pick a date and time:",
            view=DateTimePickerView(category="project"),
            ephemeral=True
        )

    @ui.button(label="📝 Other", style=discord.ButtonStyle.secondary, custom_id="cat_other")
    async def other(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message(
            content="Pick a date and time:",
            view=DateTimePickerView(category="default"),
            ephemeral=True
        )

class DateTimePickerView(ui.View):
    def __init__(self, category):
        super().__init__(timeout=60)
        self.category = category
        self.selected_date = None
        self.selected_time = None

        today = datetime.now()
        dates = [(today + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(20)]
        times = [f"{h:02d}:00" for h in range(7, 24)] + ["00:00"]

        self.add_item(DatePickerSelect(self, dates))
        self.add_item(TimePickerSelect(self, times))

    @ui.button(label="Continue", style=discord.ButtonStyle.success, emoji="➡️")
    async def continue_button(self, interaction: discord.Interaction, button: ui.Button):
        if not self.selected_date or not self.selected_time:
            await interaction.response.send_message(
                content="❌ Please select both a date and time before continuing.",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(
            AddTaskModal(category=self.category, preset_date=self.selected_date, preset_time=self.selected_time)
        )

class TaskManagementView(ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.add_item(TaskSelect(user_id))
    
    @ui.button(label='✏️ Edit Task', style=discord.ButtonStyle.primary, emoji='✏️', custom_id='edit_task_btn')
    async def edit_task(self, interaction: discord.Interaction, button: ui.Button):
        modal = EditTaskModal()
        await interaction.response.send_modal(modal)
    
    @ui.button(label='🗑️ Delete Task', style=discord.ButtonStyle.danger, emoji='🗑️', custom_id='delete_task_btn')
    async def delete_task(self, interaction: discord.Interaction, button: ui.Button):
        modal = DeleteTaskModal()
        await interaction.response.send_modal(modal)

class TaskSelect(ui.Select):
    def __init__(self, user_id: int):
        self.user_id = user_id
        from datetime import datetime

        now = datetime.now()
        tasks = sorted(
            [t for t in schedule_manager._get_user_tasks(user_id)
             if datetime.strptime(f"{t['date']} {t['hour']}:{t['minute']}", "%Y-%m-%d %H:%M") >= now],
            key=lambda t: f"{t['date']} {t['hour']:02}:{t['minute']:02}"
        )

        options = []
        for t in tasks[:25]:  # Limit to 25 to avoid Discord API error
            label = f"{t['date']} • {schedule_manager._format_time_display(t['hour'], t['minute'])} - {t.get('title', '[No Title]')[:80]}"
            value = str(t['id'])
            options.append(discord.SelectOption(label=label, value=value))

        super().__init__(
            placeholder="Select a task to edit or delete...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="select_task"
        )

    async def callback(self, interaction: discord.Interaction):
        task_id = int(self.values[0])
        view = EditOrDeleteTaskView(user_id=self.user_id, task_id=task_id)
        await interaction.response.send_message(content=f"Selected Task ID: `{task_id}`", view=view, ephemeral=True)

class DatePickerSelect(ui.Select):
    def __init__(self, parent_view, options):
        self.parent_view = parent_view
        super().__init__(
            placeholder="📅 Choose a date",
            options=[discord.SelectOption(label=o, value=o) for o in options],
            custom_id="date_picker"
        )

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.selected_date = self.values[0]
        await interaction.response.defer()

class TimePickerSelect(ui.Select):
    def __init__(self, parent_view, options):
        self.parent_view = parent_view
        super().__init__(
            placeholder="⏰ Choose a time",
            options=[discord.SelectOption(label=o, value=o) for o in options],
            custom_id="time_picker"
        )

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.selected_time = self.values[0]
        await interaction.response.defer()

class EditOrDeleteTaskView(ui.View):
    def __init__(self, user_id: int, task_id: int):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.task_id = task_id

    @ui.button(label="✏️ Edit", style=discord.ButtonStyle.primary)
    async def edit(self, interaction: discord.Interaction, button: ui.Button):
        modal = EditTaskByIDModal(self.user_id, self.task_id)
        await interaction.response.send_modal(modal)

    @ui.button(label="🗑️ Delete", style=discord.ButtonStyle.danger)
    async def delete(self, interaction: discord.Interaction, button: ui.Button):
        result = schedule_manager.delete_task(self.user_id, self.task_id)
        if result['success']:
            msg = f"✅ Task `{self.task_id}` deleted successfully."
        else:
            msg = f"❌ Error deleting task: {result['error']}"
        await interaction.response.send_message(content=msg, ephemeral=True)

class EditTaskByIDModal(ui.Modal, title='Edit Selected Task'):
    def __init__(self, user_id: int, task_id: int):
        super().__init__()
        self.user_id = user_id
        self.task_id = task_id

    new_title = ui.TextInput(label="New Title", required=False, max_length=100)
    new_description = ui.TextInput(label="New Description", required=False, max_length=200)
    new_date = ui.TextInput(label="New Date (YYYY-MM-DD)", required=False, max_length=10)
    new_time = ui.TextInput(label="New Time (HH:MM)", required=False, max_length=5)

    async def on_submit(self, interaction: discord.Interaction):
        result = schedule_manager.edit_task(
            user_id=self.user_id,
            task_id=self.task_id,
            new_title=self.new_title.value or None,
            new_description=self.new_description.value or None,
            new_date=self.new_date.value or None,
            new_time=self.new_time.value or None
        )
        if result['success']:
            msg = f"✅ Task `{self.task_id}` updated successfully."
        else:
            msg = f"❌ Error: {result['error']}"
        await interaction.response.send_message(content=msg, ephemeral=True)

class AddTaskModal(ui.Modal, title='Add New Task'):
    def __init__(self, category="default", preset_date="", preset_time=""):
        super().__init__()
        self.category = category
        self.preset_date = preset_date
        self.preset_time = preset_time

        self.task_title = ui.TextInput(label='Task Title', required=True, max_length=100)
        self.task_description = ui.TextInput(label='Task Description (optional)', style=discord.TextStyle.paragraph, required=False, max_length=200)
        self.date = ui.TextInput(label='Date (YYYY-MM-DD)', required=False, max_length=10, default=self.preset_date)
        self.time = ui.TextInput(label='Time (HH:MM)', required=False, max_length=5, default=self.preset_time)

        self.add_item(self.task_title)
        self.add_item(self.task_description)
        self.add_item(self.date)
        self.add_item(self.time)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        result = schedule_manager.add_task(
            user_id=user_id,
            title=self.task_title.value,
            description=self.task_description.value or "",
            date_str=self.date.value or None,
            time_str=self.time.value or None,
            category=self.category
        )

        if result["success"]:
            embed = discord.Embed(
                title="✅ Task Added",
                description=f"**{self.task_title.value}** scheduled on **{result['date']} at {result['time']}**\nCategory: `{self.category}`",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                description=result['error'],
                color=discord.Color.red()
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

class CategoryDropdown(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Work", value="work", emoji="💼"),
            discord.SelectOption(label="Study", value="study", emoji="📘"),
            discord.SelectOption(label="Gym", value="gym", emoji="💪"),
            discord.SelectOption(label="Personal", value="personal", emoji="🧘"),
            discord.SelectOption(label="Project", value="project", emoji="🛠️"),
            discord.SelectOption(label="Other", value="default", emoji="📝")
        ]

        super().__init__(
            placeholder="Select a category...",
            options=options,
            min_values=1,
            max_values=1,
            custom_id="category_select"
        )

    async def callback(self, interaction: discord.Interaction):
        pass  # Handled by modal

class EditTaskModal(ui.Modal, title='Edit Task'):
    def __init__(self):
        super().__init__()
    
    task_id = ui.TextInput(
        label='Task ID',
        placeholder='Enter the task ID you want to edit',
        required=True,
        max_length=10
    )
    
    new_description = ui.TextInput(
        label='New Description',
        placeholder='Leave empty to keep current description',
        required=False,
        max_length=400
    )

    new_title = ui.TextInput(
        label='New Title',
        placeholder='Leave empty to keep current title',
        required=False,
        max_length=24
    )
    
    new_date = ui.TextInput(
        label='New Date (YYYY-MM-DD)',
        placeholder='Leave empty to keep current date',
        required=False,
        max_length=10
    )
    
    new_time = ui.TextInput(
        label='New Time (HH:MM)',
        placeholder='Leave empty to keep current time',
        required=False,
        max_length=5
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        
        try:
            task_id = int(self.task_id.value)
        except ValueError:
            embed = discord.Embed(
                title="❌ Invalid Task ID",
                description="Please enter a valid task ID number.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        new_title = self.new_title.value if self.new_title.value else None
        new_desc = self.new_description.value if self.new_description.value else None
        new_date = self.new_date.value if self.new_date.value else None
        new_time = self.new_time.value if self.new_time.value else None
        
        result = schedule_manager.edit_task(user_id, task_id, new_title, new_desc, new_date, new_time)
        
        if result['success']:
            embed = discord.Embed(
                title="✅ Task Updated Successfully",
                description=f"**Task ID:** {task_id}\n**Updated successfully!**",
                color=discord.Color.blue()
            )
        else:
            embed = discord.Embed(
                title="❌ Error Updating Task",
                description=result['error'],
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class DeleteTaskModal(ui.Modal, title='Delete Task'):
    def __init__(self):
        super().__init__()
    
    task_id = ui.TextInput(
        label='Task ID',
        placeholder='Enter the task ID you want to delete',
        required=True,
        max_length=10
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        
        try:
            task_id = int(self.task_id.value)
        except ValueError:
            embed = discord.Embed(
                title="❌ Invalid Task ID",
                description="Please enter a valid task ID number.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        result = schedule_manager.delete_task(user_id, task_id)
        
        if result['success']:
            embed = discord.Embed(
                title="✅ Task Deleted Successfully",
                description=f"Task ID {task_id} has been removed from your schedule.",
                color=discord.Color.orange()
            )
        else:
            embed = discord.Embed(
                title="❌ Error Deleting Task",
                description=result['error'],
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_ready():
    print(f'{bot.user} is online and ready.')

    bot.add_view(MainMenuView())

    # Send the !menu to a default channel (e.g., your channel ID)
    channel = bot.get_channel('CHANNEL_ID') #============================================= CHANNEL ID
    if channel:
        embed = discord.Embed(
            title="📅 Schedule Manager Bot",
            description="Use the buttons below to manage your schedule.",
            color=discord.Color.blue()
        )
        embed.add_field(name="🕐 Time Range", value="7 AM to 12 AM", inline=False)
        embed.add_field(name="📋 Features", value="View schedule • Add • Edit • Delete • List", inline=False)
        await channel.send(embed=embed, view=MainMenuView())

    # Start 6-hour menu reminder task
    bot.loop.create_task(menu_reminder())

async def menu_reminder():
    await bot.wait_until_ready()
    channel = bot.get_channel('CHANNEL_ID')  #============================================= CHANNEL ID
    while not bot.is_closed():
        if channel:
            embed = discord.Embed(
                title="⏰ Menu Reminder",
                description="Here's your schedule manager. Click below to get started:",
                color=discord.Color.green()
            )
            await channel.send(embed=embed, view=MainMenuView())
        await asyncio.sleep(6 * 60 * 60)  # 6 hours

# Keep the old commands for backward compatibility
@bot.command(name='menu', help='Show the main menu')
async def show_menu(ctx):
    """Show the main menu with buttons"""
    embed = discord.Embed(
        title="📅 Schedule Manager Bot",
        description="Use the buttons below to manage your schedule.",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="🕐 Time Range",
        value="Schedule displays from 7:00 AM to 12:00 AM (midnight)",
        inline=False
    )
    embed.add_field(
        name="📋 Features",
        value="• View your 5-day schedule\n• Add new tasks\n• Edit existing tasks\n• Delete tasks\n• List all tasks",
        inline=False
    )
    
    view = MainMenuView()
    await ctx.send(embed=embed, view=view)

# Legacy text commands (still available)
@bot.command(name='schedule', help='Display your schedule for the next 5 days')
async def show_schedule(ctx):
    """Display the schedule for the next 5 days from 7 AM to 12 AM"""
    user_id = ctx.author.id
    schedule_embed = schedule_manager.get_schedule_display(user_id)
    await ctx.send(embed=schedule_embed)

@bot.command(name='add', help='Add a task to your schedule. Usage: !add "Task description" [date] [time]')
async def add_task(ctx, task_description: str, date: str = None, time: str = None):
    """Add a task to the schedule"""
    user_id = ctx.author.id
    
    try:
        result = schedule_manager.add_task(user_id, title=task_description, description="", date_str=date, time_str=time)
        
        if result['success']:
            embed = discord.Embed(
                title="✅ Task Added Successfully",
                description=f"**Task:** {task_description}\n**Date:** {result['date']}\n**Time:** {result['time']}",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ Error Adding Task",
                description=result['error'],
                color=discord.Color.red()
            )
        
        await ctx.send(embed=embed)
    
    except Exception as e:
        embed = discord.Embed(
            title="❌ Error",
            description=f"An error occurred: {str(e)}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="❌ Missing Required Argument",
            description=f"Missing required argument: {error.param.name}\nUse `!menu` to access the button interface.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.BadArgument):
        embed = discord.Embed(
            title="❌ Invalid Argument",
            description=f"Invalid argument provided. Use `!menu` to access the button interface.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="❌ An Error Occurred",
            description=f"An unexpected error occurred: {str(error)}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

# Run the bot
if __name__ == '__main__':
    bot.run('BOT_TOKEN')