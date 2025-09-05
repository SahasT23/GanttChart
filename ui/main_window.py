"""
Main application window that combines all components
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import os

from models.task import Project, Task, TaskType
from utils.data_manager import DataManager, AutoSaveManager
from ui.gantt_chart import GanttChart
from ui.task_sidebar import TaskSidebar

class GanttMainWindow:
    """Main application window"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Professional Gantt Chart")
        
        # Initialize components
        self.project = Project("My Project")
        self.data_manager = DataManager()
        self.auto_save_manager = AutoSaveManager(self.data_manager)
        
        # Load existing project
        saved_project = self.data_manager.load_project()
        if saved_project:
            self.project = saved_project
        else:
            # Create sample tasks for demonstration
            self.create_sample_tasks()
        
        self.setup_ui()
        self.connect_callbacks()
        
        # Start auto-save
        self.auto_save_manager.start_auto_save(self.root, self.project)
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_ui(self):
        """Setup the main user interface"""
        # Configure root window
        self.root.configure(bg='#f0f0f0')
        
        # Create status bar
        self.create_status_bar()
        
        # Main container
        main_container = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg='#f0f0f0', 
                                       sashwidth=8, sashrelief=tk.RAISED)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Task sidebar
        self.task_sidebar = TaskSidebar(main_container, self.project, bg='#f8f9fa')
        main_container.add(self.task_sidebar, minsize=350, sticky="nsew")
        
        # Right panel - Gantt chart
        chart_frame = tk.Frame(main_container, bg='#ffffff')
        main_container.add(chart_frame, minsize=800, sticky="nsew")
        
        self.gantt_chart = GanttChart(chart_frame, self.project)
        self.gantt_chart.pack(fill=tk.BOTH, expand=True)
        
        # Create menu bar after components are initialized
        self.create_menu_bar()
        
        # Set initial pane position
        self.root.after(100, lambda: main_container.sash_place(0, 400, 0))
    
    def create_menu_bar(self):
        """Create the application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        
        file_menu.add_command(label="New Project", command=self.new_project, accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(label="Open Project...", command=self.open_project, accelerator="Ctrl+O")
        file_menu.add_command(label="Save Project", command=self.save_project, accelerator="Ctrl+S")
        file_menu.add_command(label="Save Project As...", command=self.save_project_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Import from CSV...", command=self.import_csv)
        file_menu.add_command(label="Export to CSV...", command=self.export_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Project Properties", command=self.show_project_properties)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing, accelerator="Ctrl+Q")
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        
        edit_menu.add_command(label="Add Task", command=self.task_sidebar.show_add_task_dialog, accelerator="Ctrl+T")
        edit_menu.add_separator()
        edit_menu.add_command(label="Preferences", command=self.show_preferences)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        
        view_menu.add_command(label="Zoom In", command=self.gantt_chart.zoom_in, accelerator="Ctrl++")
        view_menu.add_command(label="Zoom Out", command=self.gantt_chart.zoom_out, accelerator="Ctrl+-")
        view_menu.add_command(label="Zoom to Fit", command=self.gantt_chart.zoom_to_fit, accelerator="Ctrl+0")
        view_menu.add_separator()
        view_menu.add_command(label="Go to Today", command=self.gantt_chart.scroll_to_today, accelerator="Ctrl+T")
        view_menu.add_command(label="Go to Start", command=self.gantt_chart.scroll_to_start, accelerator="Home")
        view_menu.add_separator()
        view_menu.add_command(label="Expand All Tasks", command=self.task_sidebar.expand_all)
        view_menu.add_command(label="Collapse All Tasks", command=self.task_sidebar.collapse_all)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
        tools_menu.add_command(label="Project Statistics", command=self.show_project_statistics)
        tools_menu.add_command(label="Critical Path Analysis", command=self.show_critical_path)
        tools_menu.add_separator()
        tools_menu.add_command(label="Auto-Save Settings", command=self.configure_auto_save)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts)
        help_menu.add_command(label="About", command=self.show_about)
        
        # Bind keyboard shortcuts
        self.bind_shortcuts()
    
    def create_status_bar(self):
        """Create the status bar"""
        self.status_bar = tk.Frame(self.root, relief=tk.SUNKEN, bg='#f0f0f0', height=25)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_bar.pack_propagate(False)
        
        # Status labels
        self.status_label = tk.Label(self.status_bar, text="Ready", bg='#f0f0f0', 
                                    font=('Segoe UI', 9), anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # Project info
        self.project_info_label = tk.Label(self.status_bar, text="", bg='#f0f0f0', 
                                          font=('Segoe UI', 9), anchor=tk.E)
        self.project_info_label.pack(side=tk.RIGHT, padx=10)
        
        # Auto-save indicator
        self.auto_save_label = tk.Label(self.status_bar, text="●", bg='#f0f0f0', 
                                       fg='#28a745', font=('Segoe UI', 12))
        self.auto_save_label.pack(side=tk.RIGHT, padx=(0, 10))
        
        self.update_status_bar()
    
    def bind_shortcuts(self):
        """Bind keyboard shortcuts"""
        self.root.bind('<Control-n>', lambda e: self.new_project())
        self.root.bind('<Control-o>', lambda e: self.open_project())
        self.root.bind('<Control-s>', lambda e: self.save_project())
        self.root.bind('<Control-Shift-S>', lambda e: self.save_project_as())
        self.root.bind('<Control-q>', lambda e: self.on_closing())
        self.root.bind('<Control-t>', lambda e: self.task_sidebar.show_add_task_dialog())
        self.root.bind('<Control-plus>', lambda e: self.gantt_chart.zoom_in())
        self.root.bind('<Control-minus>', lambda e: self.gantt_chart.zoom_out())
        self.root.bind('<Control-0>', lambda e: self.gantt_chart.zoom_to_fit())
        self.root.bind('<Home>', lambda e: self.gantt_chart.scroll_to_start())
        self.root.bind('<F5>', lambda e: self.refresh_all())
    
    def connect_callbacks(self):
        """Connect callbacks between components"""
        # Task sidebar callbacks
        self.task_sidebar.on_task_added = self.on_task_changed
        self.task_sidebar.on_task_updated = self.on_task_changed
        self.task_sidebar.on_task_deleted = self.on_task_changed
        self.task_sidebar.on_task_selected = self.on_task_selected
        
        # Gantt chart callbacks
        self.gantt_chart.on_task_selected = self.on_gantt_task_selected
        self.gantt_chart.on_task_double_click = self.on_gantt_task_double_click
    
    def create_sample_tasks(self):
        """Create sample tasks for demonstration"""
        sample_tasks = [
            {
                'name': 'Project Planning',
                'start_date': datetime(2025, 1, 15),
                'duration': 5,
                'color': '#0078d4',
                'progress': 100.0,
                'assignee': 'Project Manager',
                'priority': 'High'
            },
            {
                'name': 'Requirements Analysis',
                'start_date': datetime(2025, 1, 22),
                'duration': 8,
                'color': '#28a745',
                'dependencies': [],
                'progress': 75.0,
                'assignee': 'Business Analyst',
                'priority': 'High'
            },
            {
                'name': 'Design Phase',
                'start_date': datetime(2025, 2, 3),
                'duration': 12,
                'color': '#ffc107',
                'progress': 40.0,
                'assignee': 'UI/UX Designer',
                'priority': 'Normal'
            },
            {
                'name': 'Development Kickoff',
                'start_date': datetime(2025, 2, 17),
                'duration': 0,
                'task_type': TaskType.MILESTONE,
                'color': '#ff6b35',
                'assignee': 'Development Team'
            },
            {
                'name': 'Frontend Development',
                'start_date': datetime(2025, 2, 18),
                'duration': 20,
                'color': '#6f42c1',
                'progress': 25.0,
                'assignee': 'Frontend Developer',
                'priority': 'High'
            },
            {
                'name': 'Backend Development',
                'start_date': datetime(2025, 2, 20),
                'duration': 25,
                'color': '#fd7e14',
                'progress': 15.0,
                'assignee': 'Backend Developer',
                'priority': 'High'
            },
            {
                'name': 'Testing Phase',
                'start_date': datetime(2025, 3, 20),
                'duration': 10,
                'color': '#dc3545',
                'progress': 0.0,
                'assignee': 'QA Tester',
                'priority': 'Normal'
            }
        ]
        
        for task_data in sample_tasks:
            task = Task(**task_data)
            self.project.add_task(task)
    
    # Event handlers
    def on_task_changed(self, task: Task):
        """Handle task changes"""
        self.gantt_chart.refresh()
        self.update_status_bar()
        self.set_status(f"Task '{task.name}' updated")
    
    def on_task_selected(self, task: Task):
        """Handle task selection in sidebar"""
        if task:
            self.gantt_chart.select_task(task.task_id)
            self.set_status(f"Selected: {task.name}")
        else:
            self.gantt_chart.select_task(None)
            self.set_status("Ready")
    
    def on_gantt_task_selected(self, task: Task):
        """Handle task selection in Gantt chart"""
        # Note: This could sync with sidebar selection if needed
        if task:
            self.set_status(f"Selected: {task.name}")
        else:
            self.set_status("Ready")
    
    def on_gantt_task_double_click(self, task_id: str):
        """Handle double-click on Gantt chart task"""
        task = self.project.get_task(task_id)
        if task:
            self.task_sidebar.edit_task(task)
    
    # Menu actions
    def new_project(self):
        """Create a new project"""
        if self.project.tasks and messagebox.askyesno(
            "New Project", 
            "This will clear all current tasks. Do you want to save first?"
        ):
            self.save_project()
        
        self.project = Project("New Project")
        self.task_sidebar.set_project(self.project)
        self.gantt_chart.set_project(self.project)
        self.auto_save_manager.project = self.project
        self.update_status_bar()
        self.set_status("New project created")
    
    def open_project(self):
        """Open an existing project"""
        file_path = filedialog.askopenfilename(
            title="Open Project",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            defaultextension=".json"
        )
        
        if file_path:
            project = self.data_manager.load_project(file_path)
            if project:
                self.project = project
                self.task_sidebar.set_project(self.project)
                self.gantt_chart.set_project(self.project)
                self.auto_save_manager.project = self.project
                self.update_status_bar()
                self.set_status(f"Opened: {os.path.basename(file_path)}")
            else:
                messagebox.showerror("Error", "Failed to load project file")
    
    def save_project(self):
        """Save the current project"""
        if self.data_manager.save_project(self.project):
            self.set_status("Project saved successfully")
            self.flash_auto_save_indicator()
        else:
            messagebox.showerror("Error", "Failed to save project")
    
    def save_project_as(self):
        """Save the project with a new name"""
        file_path = filedialog.asksaveasfilename(
            title="Save Project As",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            defaultextension=".json"
        )
        
        if file_path:
            if self.data_manager.save_project(self.project, file_path):
                self.set_status(f"Saved as: {os.path.basename(file_path)}")
            else:
                messagebox.showerror("Error", "Failed to save project")
    
    def import_csv(self):
        """Import project from CSV"""
        file_path = filedialog.askopenfilename(
            title="Import from CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            project = self.data_manager.import_from_csv(file_path)
            if project:
                if messagebox.askyesno("Import CSV", "Replace current project with imported data?"):
                    self.project = project
                    self.task_sidebar.set_project(self.project)
                    self.gantt_chart.set_project(self.project)
                    self.auto_save_manager.project = self.project
                    self.update_status_bar()
                    self.set_status("Project imported from CSV")
            else:
                messagebox.showerror("Error", "Failed to import CSV file")
    
    def export_csv(self):
        """Export project to CSV"""
        file_path = filedialog.asksaveasfilename(
            title="Export to CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            defaultextension=".csv"
        )
        
        if file_path:
            if self.data_manager.export_to_csv(self.project, file_path):
                self.set_status(f"Exported to: {os.path.basename(file_path)}")
                messagebox.showinfo("Success", "Project exported to CSV successfully!")
            else:
                messagebox.showerror("Error", "Failed to export to CSV")
    
    def show_project_properties(self):
        """Show project properties dialog"""
        ProjectPropertiesDialog(self.root, self.project)
        self.update_status_bar()
    
    def show_preferences(self):
        """Show application preferences"""
        PreferencesDialog(self.root, self.auto_save_manager)
    
    def show_project_statistics(self):
        """Show project statistics"""
        if not self.project.tasks:
            messagebox.showinfo("Project Statistics", "No tasks in current project")
            return
        
        stats = self.calculate_project_statistics()
        ProjectStatisticsDialog(self.root, stats)
    
    def show_critical_path(self):
        """Show critical path analysis"""
        critical_tasks = self.project.get_critical_path()
        if critical_tasks:
            task_names = [task.name for task in critical_tasks]
            messagebox.showinfo(
                "Critical Path",
                f"Critical Path Tasks:\n\n" + "\n".join(f"• {name}" for name in task_names)
            )
        else:
            messagebox.showinfo("Critical Path", "No critical path found or no tasks in project")
    
    def configure_auto_save(self):
        """Configure auto-save settings"""
        AutoSaveDialog(self.root, self.auto_save_manager)
    
    def show_shortcuts(self):
        """Show keyboard shortcuts help"""
        shortcuts_text = """
Keyboard Shortcuts:

File Operations:
  Ctrl+N      New Project
  Ctrl+O      Open Project
  Ctrl+S      Save Project
  Ctrl+Shift+S Save Project As
  Ctrl+Q      Exit

Editing:
  Ctrl+T      Add Task

View:
  Ctrl++      Zoom In
  Ctrl+-      Zoom Out
  Ctrl+0      Zoom to Fit
  Home        Go to Start
  F5          Refresh

General:
  Double-click Edit Task
  Right-click Context Menu
        """
        
        ShortcutsDialog(self.root, shortcuts_text)
    
    def show_about(self):
        """Show about dialog"""
        about_text = f"""
Professional Gantt Chart Application
Version 1.0.0

A modern, feature-rich project management tool
built with Python and Tkinter.

Features:
• Professional Gantt chart visualization
• Task dependencies with visual arrows
• Color-coded tasks and milestones
• Horizontal scrolling timeline
• Auto-save functionality
• JSON and CSV import/export
• Project statistics and critical path analysis

Current Project: {self.project.name}
Tasks: {len(self.project.tasks)}
Created: {self.project.created.strftime('%Y-%m-%d %H:%M')}
        """
        
        AboutDialog(self.root, about_text)
    
    # Utility methods
    def refresh_all(self):
        """Refresh all components"""
        self.task_sidebar.refresh_task_list()
        self.gantt_chart.refresh()
        self.update_status_bar()
        self.set_status("View refreshed")
    
    def set_status(self, message: str):
        """Set status bar message"""
        self.status_label.config(text=message)
        # Clear status after 3 seconds
        self.root.after(3000, lambda: self.status_label.config(text="Ready"))
    
    def update_status_bar(self):
        """Update status bar information"""
        task_count = len(self.project.tasks)
        completed = sum(1 for task in self.project.tasks if task.is_completed)
        
        info_text = f"Project: {self.project.name} | Tasks: {task_count} | Completed: {completed}"
        if self.project.tasks:
            start_date, end_date = self.project.get_project_timeline()
            info_text += f" | Duration: {(end_date - start_date).days} days"
        
        self.project_info_label.config(text=info_text)
    
    def flash_auto_save_indicator(self):
        """Flash the auto-save indicator"""
        self.auto_save_label.config(fg='#ffc107')
        self.root.after(500, lambda: self.auto_save_label.config(fg='#28a745'))
    
    def calculate_project_statistics(self):
        """Calculate comprehensive project statistics"""
        if not self.project.tasks:
            return {}
        
        total_tasks = len(self.project.tasks)
        completed_tasks = sum(1 for task in self.project.tasks if task.is_completed)
        in_progress_tasks = sum(1 for task in self.project.tasks if task.is_in_progress)
        overdue_tasks = sum(1 for task in self.project.tasks if task.is_overdue)
        
        total_duration = sum(task.duration for task in self.project.tasks)
        avg_progress = sum(task.progress for task in self.project.tasks) / total_tasks
        
        start_date, end_date = self.project.get_project_timeline()
        project_duration = (end_date - start_date).days
        
        # Task type breakdown
        regular_tasks = sum(1 for task in self.project.tasks if task.task_type == TaskType.TASK)
        milestones = sum(1 for task in self.project.tasks if task.task_type == TaskType.MILESTONE)
        
        # Priority breakdown
        priorities = {}
        for task in self.project.tasks:
            priorities[task.priority] = priorities.get(task.priority, 0) + 1
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'in_progress_tasks': in_progress_tasks,
            'overdue_tasks': overdue_tasks,
            'completion_rate': (completed_tasks / total_tasks) * 100,
            'total_duration': total_duration,
            'avg_progress': avg_progress,
            'project_duration': project_duration,
            'start_date': start_date,
            'end_date': end_date,
            'regular_tasks': regular_tasks,
            'milestones': milestones,
            'priorities': priorities,
            'created': self.project.created,
            'last_modified': self.project.last_modified,
            'modifications': self.project.total_modifications
        }
    
    def on_closing(self):
        """Handle application closing"""
        if self.project.tasks:
            self.save_project()  # Auto-save on exit
        
        self.auto_save_manager.stop_auto_save()
        self.root.destroy()

# Dialog classes for various functions
class ProjectPropertiesDialog:
    """Dialog for editing project properties"""
    
    def __init__(self, parent, project: Project):
        self.project = project
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Project Properties")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_dialog()
        self.dialog.wait_window()
    
    def setup_dialog(self):
        """Setup the dialog UI"""
        main_frame = tk.Frame(self.dialog, bg='#ffffff')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Project name
        tk.Label(main_frame, text="Project Name:", font=('Segoe UI', 9, 'bold'), bg='#ffffff').pack(anchor=tk.W)
        self.name_var = tk.StringVar(value=self.project.name)
        tk.Entry(main_frame, textvariable=self.name_var, font=('Segoe UI', 9), width=40).pack(fill=tk.X, pady=(5, 15))
        
        # Description
        tk.Label(main_frame, text="Description:", font=('Segoe UI', 9, 'bold'), bg='#ffffff').pack(anchor=tk.W)
        self.description_text = tk.Text(main_frame, font=('Segoe UI', 9), height=5, width=40, wrap=tk.WORD)
        self.description_text.pack(fill=tk.X, pady=(5, 15))
        self.description_text.insert('1.0', self.project.description)
        
        # Read-only info
        info_frame = tk.Frame(main_frame, bg='#f8f9fa')
        info_frame.pack(fill=tk.X, pady=(10, 15))
        
        tk.Label(info_frame, text=f"Created: {self.project.created.strftime('%Y-%m-%d %H:%M')}", 
                font=('Segoe UI', 8), bg='#f8f9fa').pack(anchor=tk.W, padx=10, pady=5)
        tk.Label(info_frame, text=f"Last Modified: {self.project.last_modified.strftime('%Y-%m-%d %H:%M')}", 
                font=('Segoe UI', 8), bg='#f8f9fa').pack(anchor=tk.W, padx=10, pady=5)
        tk.Label(info_frame, text=f"Total Tasks: {len(self.project.tasks)}", 
                font=('Segoe UI', 8), bg='#f8f9fa').pack(anchor=tk.W, padx=10, pady=5)
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg='#ffffff')
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Button(button_frame, text="Cancel", command=self.dialog.destroy,
                 bg='#6c757d', fg='white', border=0, padx=20, pady=8).pack(side=tk.RIGHT, padx=(10, 0))
        tk.Button(button_frame, text="Save", command=self.save,
                 bg='#28a745', fg='white', border=0, padx=20, pady=8).pack(side=tk.RIGHT)
    
    def save(self):
        """Save project properties"""
        self.project.name = self.name_var.get().strip()
        self.project.description = self.description_text.get('1.0', tk.END).strip()
        self.project.increment_modifications()
        self.dialog.destroy()

class ProjectStatisticsDialog:
    """Dialog showing project statistics"""
    
    def __init__(self, parent, stats: dict):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Project Statistics")
        self.dialog.geometry("500x600")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.create_statistics_view(stats)
        self.dialog.wait_window()
    
    def create_statistics_view(self, stats: dict):
        """Create the statistics view"""
        main_frame = tk.Frame(self.dialog, bg='#ffffff')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        tk.Label(main_frame, text="Project Statistics", 
                font=('Segoe UI', 14, 'bold'), bg='#ffffff').pack(pady=(0, 20))
        
        # Statistics content would go here
        # (Implementation details for statistics display)
        
        # Close button
        tk.Button(main_frame, text="Close", command=self.dialog.destroy,
                 bg='#6c757d', fg='white', border=0, padx=20, pady=8).pack(pady=20)

class PreferencesDialog:
    """Application preferences dialog"""
    
    def __init__(self, parent, auto_save_manager):
        self.auto_save_manager = auto_save_manager
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Preferences")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_dialog()
        self.dialog.wait_window()
    
    def setup_dialog(self):
        """Setup preferences dialog"""
        # Implementation for preferences
        main_frame = tk.Frame(self.dialog, bg='#ffffff')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(main_frame, text="Preferences", 
                font=('Segoe UI', 14, 'bold'), bg='#ffffff').pack(pady=(0, 20))
        
        tk.Button(main_frame, text="Close", command=self.dialog.destroy,
                 bg='#6c757d', fg='white', border=0, padx=20, pady=8).pack(pady=20)

class AutoSaveDialog:
    """Auto-save configuration dialog"""
    
    def __init__(self, parent, auto_save_manager):
        # Implementation for auto-save settings
        pass

class ShortcutsDialog:
    """Keyboard shortcuts dialog"""
    
    def __init__(self, parent, shortcuts_text: str):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Keyboard Shortcuts")
        self.dialog.geometry("400x500")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        main_frame = tk.Frame(self.dialog, bg='#ffffff')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        text_widget = tk.Text(main_frame, font=('Consolas', 9), bg='#f8f9fa', 
                             wrap=tk.WORD, state='disabled')
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        text_widget.config(state='normal')
        text_widget.insert('1.0', shortcuts_text)
        text_widget.config(state='disabled')
        
        tk.Button(main_frame, text="Close", command=self.dialog.destroy,
                 bg='#6c757d', fg='white', border=0, padx=20, pady=8).pack(pady=(10, 0))

class AboutDialog:
    """About dialog"""
    
    def __init__(self, parent, about_text: str):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("About")
        self.dialog.geometry("450x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        main_frame = tk.Frame(self.dialog, bg='#ffffff')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(main_frame, text="📊", font=('Segoe UI', 48), bg='#ffffff').pack(pady=(0, 20))
        
        text_widget = tk.Text(main_frame, font=('Segoe UI', 9), bg='#ffffff', 
                             wrap=tk.WORD, state='disabled', border=0)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        text_widget.config(state='normal')
        text_widget.insert('1.0', about_text)
        text_widget.config(state='disabled')
        
        tk.Button(main_frame, text="Close", command=self.dialog.destroy,
                 bg='#0078d4', fg='white', border=0, padx=20, pady=8).pack(pady=(10, 0))