"""
Task management sidebar with modern styling similar to the reference image
"""

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
from datetime import datetime, timedelta
from typing import Callable, Optional, List

from models.task import Task, TaskType, Project

class TaskSidebar(tk.Frame):
    """Modern task management sidebar"""
    
    def __init__(self, parent, project: Project, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.project = project
        self.selected_task: Optional[Task] = None
        
        # Callbacks
        self.on_task_added: Optional[Callable] = None
        self.on_task_updated: Optional[Callable] = None
        self.on_task_deleted: Optional[Callable] = None
        self.on_task_selected: Optional[Callable] = None
        
        # UI state
        self.selected_color = "#4472C4"
        self.expanded_groups = set()
        
        self.setup_ui()
        self.refresh_task_list()
        
    def setup_ui(self):
        """Setup the sidebar UI"""
        self.configure(bg='#f8f9fa', width=400)
        self.pack_propagate(False)
        
        # Header
        header_frame = tk.Frame(self, bg='#f8f9fa', height=50)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame, 
            text="Tasks",
            font=('Segoe UI', 16, 'bold'),
            bg='#f8f9fa',
            fg='#333333'
        )
        title_label.pack(side=tk.LEFT, anchor=tk.W)
        
        # Add button
        add_btn = tk.Button(
            header_frame,
            text="+ Add",
            font=('Segoe UI', 9),
            bg='#0078d4',
            fg='white',
            border=0,
            padx=15,
            pady=5,
            cursor='hand2',
            command=self.show_add_task_dialog
        )
        add_btn.pack(side=tk.RIGHT, anchor=tk.E)
        
        # Toolbar
        self.create_toolbar()
        
        # Task list frame
        list_frame = tk.Frame(self, bg='#f8f9fa')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create scrollable task list
        self.create_task_list(list_frame)
        
        # Task details panel (initially hidden)
        self.create_details_panel()
        
    def create_toolbar(self):
        """Create the toolbar with view controls"""
        toolbar = tk.Frame(self, bg='#f8f9fa', height=40)
        toolbar.pack(fill=tk.X, padx=10, pady=5)
        toolbar.pack_propagate(False)
        
        # View controls
        tk.Button(
            toolbar, text="Expand all", font=('Segoe UI', 8),
            bg='#ffffff', fg='#666666', border=1, relief=tk.FLAT,
            padx=10, pady=2, command=self.expand_all
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(
            toolbar, text="Collapse all", font=('Segoe UI', 8),
            bg='#ffffff', fg='#666666', border=1, relief=tk.FLAT,
            padx=10, pady=2, command=self.collapse_all
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # Search
        search_frame = tk.Frame(toolbar, bg='#f8f9fa')
        search_frame.pack(side=tk.RIGHT, padx=(10, 0))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_changed)
        
        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=('Segoe UI', 9),
            bg='#ffffff',
            fg='#333333',
            border=1,
            relief=tk.FLAT,
            width=15
        )
        search_entry.pack(side=tk.RIGHT)
        
        tk.Label(
            search_frame, text="Search",
            font=('Segoe UI', 8),
            bg='#f8f9fa', fg='#666666'
        ).pack(side=tk.RIGHT, padx=(0, 5))
        
    def create_task_list(self, parent):
        """Create the scrollable task list"""
        # Create frame with scrollbar
        list_container = tk.Frame(parent, bg='#ffffff', relief=tk.FLAT, border=1)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for scrolling
        self.list_canvas = tk.Canvas(list_container, bg='#ffffff', highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.list_canvas.yview)
        self.scrollable_frame = tk.Frame(self.list_canvas, bg='#ffffff')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.list_canvas.configure(scrollregion=self.list_canvas.bbox("all"))
        )
        
        self.list_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.list_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.list_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind mouse wheel
        self.list_canvas.bind("<MouseWheel>", self._on_mousewheel)
        
    def create_details_panel(self):
        """Create the task details panel"""
        self.details_frame = tk.Frame(self, bg='#f8f9fa')
        # Initially hidden - will be packed when task is selected
        
        # Details header
        details_header = tk.Frame(self.details_frame, bg='#e9ecef', height=35)
        details_header.pack(fill=tk.X)
        details_header.pack_propagate(False)
        
        tk.Label(
            details_header, text="Task Details",
            font=('Segoe UI', 10, 'bold'),
            bg='#e9ecef', fg='#333333'
        ).pack(side=tk.LEFT, padx=10, pady=8)
        
        close_btn = tk.Button(
            details_header, text="×",
            font=('Segoe UI', 12, 'bold'),
            bg='#e9ecef', fg='#666666',
            border=0, padx=8, pady=0,
            command=self.hide_details_panel
        )
        close_btn.pack(side=tk.RIGHT, padx=5)
        
        # Details content
        self.details_content = tk.Frame(self.details_frame, bg='#ffffff')
        self.details_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def refresh_task_list(self):
        """Refresh the task list display"""
        # Clear existing items
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        if not self.project.tasks:
            self.show_empty_state()
            return
        
        # Group tasks by month/category
        task_groups = self.group_tasks()
        
        for group_name, tasks in task_groups.items():
            self.create_task_group(group_name, tasks)
    
    def group_tasks(self) -> dict:
        """Group tasks by month for better organization"""
        groups = {}
        
        for task in sorted(self.project.tasks, key=lambda t: t.start_date):
            # Filter by search if active
            if (self.search_var.get().strip() and 
                self.search_var.get().lower() not in task.name.lower()):
                continue
                
            group_key = task.start_date.strftime("%B %Y")
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(task)
        
        return groups
    
    def create_task_group(self, group_name: str, tasks: List[Task]):
        """Create a collapsible task group"""
        # Group header
        group_frame = tk.Frame(self.scrollable_frame, bg='#ffffff')
        group_frame.pack(fill=tk.X, pady=(10, 0))
        
        header_frame = tk.Frame(group_frame, bg='#f8f9fa', height=30)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Expand/collapse button
        is_expanded = group_name in self.expanded_groups
        expand_text = "▼" if is_expanded else "▶"
        
        expand_btn = tk.Button(
            header_frame, text=expand_text,
            font=('Segoe UI', 8),
            bg='#f8f9fa', fg='#666666',
            border=0, padx=5,
            command=lambda: self.toggle_group(group_name)
        )
        expand_btn.pack(side=tk.LEFT, pady=6)
        
        # Group title
        tk.Label(
            header_frame,
            text=f"{group_name} ({len(tasks)} tasks)",
            font=('Segoe UI', 9, 'bold'),
            bg='#f8f9fa', fg='#333333'
        ).pack(side=tk.LEFT, pady=6)
        
        # Tasks container
        if is_expanded:
            tasks_frame = tk.Frame(group_frame, bg='#ffffff')
            tasks_frame.pack(fill=tk.X, padx=20)
            
            for i, task in enumerate(tasks):
                self.create_task_row(tasks_frame, task, i)
    
    def create_task_row(self, parent, task: Task, index: int):
        """Create a single task row"""
        # Task row frame
        row_bg = '#f8f9fa' if index % 2 == 0 else '#ffffff'
        task_frame = tk.Frame(parent, bg=row_bg, height=40)
        task_frame.pack(fill=tk.X, pady=1)
        task_frame.pack_propagate(False)
        
        # Task ID and drag handle
        id_frame = tk.Frame(task_frame, bg=row_bg, width=30)
        id_frame.pack(side=tk.LEFT, fill=tk.Y)
        id_frame.pack_propagate(False)
        
        tk.Label(
            id_frame, text="⋮⋮",
            font=('Segoe UI', 10),
            bg=row_bg, fg='#cccccc'
        ).pack(pady=12)
        
        # Task content
        content_frame = tk.Frame(task_frame, bg=row_bg)
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Task name and type indicator
        name_frame = tk.Frame(content_frame, bg=row_bg)
        name_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Type indicator
        if task.is_milestone:
            type_indicator = "◆"
            type_color = "#ff6b35"
        else:
            type_indicator = "■"
            type_color = task.color
        
        tk.Label(
            name_frame, text=type_indicator,
            font=('Segoe UI', 8),
            bg=row_bg, fg=type_color
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # Task name
        name_label = tk.Label(
            name_frame, text=task.name,
            font=('Segoe UI', 9, 'bold'),
            bg=row_bg, fg='#333333',
            anchor=tk.W
        )
        name_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Task info
        info_frame = tk.Frame(content_frame, bg=row_bg)
        info_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Dates
        date_text = f"{task.start_date.strftime('%m/%d')} - {task.end_date.strftime('%m/%d')}"
        if task.is_milestone:
            date_text = task.start_date.strftime('%m/%d')
        
        tk.Label(
            info_frame, text=date_text,
            font=('Segoe UI', 8),
            bg=row_bg, fg='#666666'
        ).pack(side=tk.LEFT)
        
        # Duration
        if not task.is_milestone:
            tk.Label(
                info_frame, text=f"• {task.duration}d",
                font=('Segoe UI', 8),
                bg=row_bg, fg='#666666'
            ).pack(side=tk.LEFT, padx=(5, 0))
        
        # Progress
        if task.progress > 0:
            tk.Label(
                info_frame, text=f"• {task.progress:.0f}%",
                font=('Segoe UI', 8),
                bg=row_bg, fg='#28a745'
            ).pack(side=tk.LEFT, padx=(5, 0))
        
        # Status indicators
        status_frame = tk.Frame(info_frame, bg=row_bg)
        status_frame.pack(side=tk.RIGHT)
        
        if task.is_overdue:
            tk.Label(
                status_frame, text="⚠",
                font=('Segoe UI', 10),
                bg=row_bg, fg='#dc3545'
            ).pack(side=tk.RIGHT, padx=2)
        
        if task.dependencies:
            tk.Label(
                status_frame, text="🔗",
                font=('Segoe UI', 8),
                bg=row_bg, fg='#666666'
            ).pack(side=tk.RIGHT, padx=2)
        
        # Bind click events
        for widget in [task_frame, content_frame, name_frame, info_frame]:
            widget.bind("<Button-1>", lambda e, t=task: self.select_task(t))
            widget.bind("<Double-Button-1>", lambda e, t=task: self.edit_task(t))
        
        # Context menu
        task_frame.bind("<Button-3>", lambda e, t=task: self.show_context_menu(e, t))
    
    def show_empty_state(self):
        """Show empty state when no tasks exist"""
        empty_frame = tk.Frame(self.scrollable_frame, bg='#ffffff')
        empty_frame.pack(fill=tk.BOTH, expand=True, pady=50)
        
        tk.Label(
            empty_frame,
            text="No tasks yet",
            font=('Segoe UI', 14, 'bold'),
            bg='#ffffff', fg='#999999'
        ).pack(pady=(0, 10))
        
        tk.Label(
            empty_frame,
            text="Click 'Add' to create your first task",
            font=('Segoe UI', 10),
            bg='#ffffff', fg='#cccccc'
        ).pack()
        
        tk.Button(
            empty_frame,
            text="+ Add Task",
            font=('Segoe UI', 10),
            bg='#0078d4', fg='white',
            border=0, padx=20, pady=8,
            cursor='hand2',
            command=self.show_add_task_dialog
        ).pack(pady=20)
    
    def toggle_group(self, group_name: str):
        """Toggle expand/collapse state of a task group"""
        if group_name in self.expanded_groups:
            self.expanded_groups.remove(group_name)
        else:
            self.expanded_groups.add(group_name)
        self.refresh_task_list()
    
    def expand_all(self):
        """Expand all task groups"""
        task_groups = self.group_tasks()
        self.expanded_groups.update(task_groups.keys())
        self.refresh_task_list()
    
    def collapse_all(self):
        """Collapse all task groups"""
        self.expanded_groups.clear()
        self.refresh_task_list()
    
    def on_search_changed(self, *args):
        """Handle search text changes"""
        self.refresh_task_list()
    
    def select_task(self, task: Task):
        """Select a task and show details"""
        self.selected_task = task
        self.show_details_panel(task)
        
        if self.on_task_selected:
            self.on_task_selected(task)
    
    def show_details_panel(self, task: Task):
        """Show the task details panel"""
        # Clear existing content
        for widget in self.details_content.winfo_children():
            widget.destroy()
        
        # Task header
        header_frame = tk.Frame(self.details_content, bg='#ffffff')
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Task type and name
        type_frame = tk.Frame(header_frame, bg='#ffffff')
        type_frame.pack(fill=tk.X)
        
        type_indicator = "◆" if task.is_milestone else "■"
        type_color = "#ff6b35" if task.is_milestone else task.color
        
        tk.Label(
            type_frame, text=type_indicator,
            font=('Segoe UI', 12),
            bg='#ffffff', fg=type_color
        ).pack(side=tk.LEFT, padx=(0, 8))
        
        tk.Label(
            type_frame, text=task.name,
            font=('Segoe UI', 12, 'bold'),
            bg='#ffffff', fg='#333333',
            anchor=tk.W
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Action buttons
        action_frame = tk.Frame(header_frame, bg='#ffffff')
        action_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Button(
            action_frame, text="Edit",
            font=('Segoe UI', 9),
            bg='#0078d4', fg='white',
            border=0, padx=15, pady=5,
            command=lambda: self.edit_task(task)
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(
            action_frame, text="Delete",
            font=('Segoe UI', 9),
            bg='#dc3545', fg='white',
            border=0, padx=15, pady=5,
            command=lambda: self.delete_task(task)
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # Task details
        details_list = tk.Frame(self.details_content, bg='#ffffff')
        details_list.pack(fill=tk.X)
        
        # Helper function to add detail rows
        def add_detail_row(label: str, value: str, color: str = '#666666'):
            row = tk.Frame(details_list, bg='#ffffff')
            row.pack(fill=tk.X, pady=2)
            
            tk.Label(
                row, text=f"{label}:",
                font=('Segoe UI', 9),
                bg='#ffffff', fg='#888888',
                width=12, anchor=tk.W
            ).pack(side=tk.LEFT)
            
            tk.Label(
                row, text=value,
                font=('Segoe UI', 9),
                bg='#ffffff', fg=color,
                anchor=tk.W
            ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Add details
        add_detail_row("Task ID", task.task_id)
        add_detail_row("Start Date", task.start_date.strftime('%Y-%m-%d'))
        
        if not task.is_milestone:
            add_detail_row("End Date", task.end_date.strftime('%Y-%m-%d'))
            add_detail_row("Duration", f"{task.duration} days")
            add_detail_row("Progress", f"{task.progress:.1f}%", 
                          '#28a745' if task.progress > 0 else '#666666')
        
        if task.assignee:
            add_detail_row("Assignee", task.assignee)
        
        add_detail_row("Priority", task.priority)
        
        if task.dependencies:
            dep_names = []
            for dep_id in task.dependencies:
                dep_task = self.project.get_task(dep_id)
                if dep_task:
                    dep_names.append(dep_task.name)
            if dep_names:
                add_detail_row("Dependencies", ", ".join(dep_names))
        
        # Status
        status_text = "Completed" if task.is_completed else "In Progress" if task.is_in_progress else "Not Started"
        status_color = '#28a745' if task.is_completed else '#ffc107' if task.is_in_progress else '#6c757d'
        if task.is_overdue:
            status_text = "Overdue"
            status_color = '#dc3545'
        
        add_detail_row("Status", status_text, status_color)
        
        if task.notes:
            notes_frame = tk.Frame(self.details_content, bg='#ffffff')
            notes_frame.pack(fill=tk.X, pady=(15, 0))
            
            tk.Label(
                notes_frame, text="Notes:",
                font=('Segoe UI', 9, 'bold'),
                bg='#ffffff', fg='#333333',
                anchor=tk.W
            ).pack(anchor=tk.W)
            
            notes_text = tk.Text(
                notes_frame,
                font=('Segoe UI', 9),
                bg='#f8f9fa', fg='#333333',
                height=3, width=30,
                wrap=tk.WORD, border=1, relief=tk.FLAT
            )
            notes_text.pack(fill=tk.X, pady=(5, 0))
            notes_text.insert('1.0', task.notes)
            notes_text.configure(state='disabled')
        
        # Show the details panel
        self.details_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
    
    def hide_details_panel(self):
        """Hide the task details panel"""
        self.details_frame.pack_forget()
        self.selected_task = None
        
        if self.on_task_selected:
            self.on_task_selected(None)
    
    def show_context_menu(self, event, task: Task):
        """Show context menu for a task"""
        context_menu = tk.Menu(self, tearoff=0)
        context_menu.add_command(label="Edit Task", command=lambda: self.edit_task(task))
        context_menu.add_command(label="Duplicate Task", command=lambda: self.duplicate_task(task))
        context_menu.add_separator()
        context_menu.add_command(label="Mark Complete", command=lambda: self.mark_complete(task))
        context_menu.add_separator()
        context_menu.add_command(label="Delete Task", command=lambda: self.delete_task(task))
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def show_add_task_dialog(self):
        """Show dialog to add a new task"""
        dialog = TaskDialog(self, "Add Task")
        if dialog.result:
            task_data = dialog.result
            task = Task(
                name=task_data['name'],
                start_date=task_data['start_date'],
                duration=task_data['duration'],
                task_type=task_data['task_type'],
                color=task_data['color'],
                dependencies=task_data['dependencies'],
                progress=task_data['progress'],
                assignee=task_data['assignee'],
                priority=task_data['priority'],
                notes=task_data['notes']
            )
            
            if self.project.add_task(task):
                self.refresh_task_list()
                if self.on_task_added:
                    self.on_task_added(task)
                messagebox.showinfo("Success", f"Task '{task.name}' added successfully!")
            else:
                messagebox.showerror("Error", "Failed to add task. Task ID might already exist.")
    
    def edit_task(self, task: Task):
        """Show dialog to edit a task"""
        dialog = TaskDialog(self, "Edit Task", task)
        if dialog.result:
            task_data = dialog.result
            
            # Update task properties
            task.name = task_data['name']
            task.start_date = task_data['start_date']
            task.duration = task_data['duration']
            task.task_type = task_data['task_type']
            task.color = task_data['color']
            task.dependencies = task_data['dependencies']
            task.progress = task_data['progress']
            task.assignee = task_data['assignee']
            task.priority = task_data['priority']
            task.notes = task_data['notes']
            
            # Recalculate end date
            task.update_dates(task.start_date, task.duration)
            
            self.project.increment_modifications()
            self.refresh_task_list()
            
            if self.selected_task and self.selected_task.task_id == task.task_id:
                self.show_details_panel(task)
            
            if self.on_task_updated:
                self.on_task_updated(task)
    
    def delete_task(self, task: Task):
        """Delete a task with confirmation"""
        if messagebox.askyesno("Confirm Delete", f"Delete task '{task.name}'?\n\nThis action cannot be undone."):
            if self.project.remove_task(task.task_id):
                self.refresh_task_list()
                self.hide_details_panel()
                
                if self.on_task_deleted:
                    self.on_task_deleted(task)
                    
                messagebox.showinfo("Success", f"Task '{task.name}' deleted successfully!")
    
    def duplicate_task(self, task: Task):
        """Duplicate a task"""
        new_task = Task(
            name=f"{task.name} (Copy)",
            start_date=task.start_date + timedelta(days=task.duration + 1),
            duration=task.duration,
            task_type=task.task_type,
            color=task.color,
            dependencies=[],  # Clear dependencies for copy
            progress=0.0,  # Reset progress
            assignee=task.assignee,
            priority=task.priority,
            notes=task.notes
        )
        
        if self.project.add_task(new_task):
            self.refresh_task_list()
            if self.on_task_added:
                self.on_task_added(new_task)
            messagebox.showinfo("Success", f"Task duplicated as '{new_task.name}'!")
    
    def mark_complete(self, task: Task):
        """Mark a task as complete"""
        task.progress = 100.0
        self.project.increment_modifications()
        self.refresh_task_list()
        
        if self.selected_task and self.selected_task.task_id == task.task_id:
            self.show_details_panel(task)
        
        if self.on_task_updated:
            self.on_task_updated(task)
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling in task list"""
        self.list_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def set_project(self, project: Project):
        """Set a new project and refresh the display"""
        self.project = project
        self.selected_task = None
        self.hide_details_panel()
        self.refresh_task_list()

class TaskDialog:
    """Dialog for adding/editing tasks"""
    
    def __init__(self, parent, title: str, task: Task = None):
        self.parent = parent
        self.task = task
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x600")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (600 // 2)
        self.dialog.geometry(f"500x600+{x}+{y}")
        
        self.selected_color = task.color if task else "#4472C4"
        
        self.setup_dialog()
        
        # Wait for dialog to close
        self.dialog.wait_window()
    
    def setup_dialog(self):
        """Setup the dialog UI"""
        main_frame = tk.Frame(self.dialog, bg='#ffffff')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Task name
        self.add_field(main_frame, "Task Name *", "name", self.task.name if self.task else "")
        
        # Task type
        type_frame = tk.Frame(main_frame, bg='#ffffff')
        type_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(type_frame, text="Task Type", font=('Segoe UI', 9, 'bold'), bg='#ffffff').pack(anchor=tk.W)
        
        self.type_var = tk.StringVar(value=self.task.task_type if self.task else TaskType.TASK)
        
        type_radio_frame = tk.Frame(type_frame, bg='#ffffff')
        type_radio_frame.pack(fill=tk.X, pady=(5, 0))
        
        tk.Radiobutton(type_radio_frame, text="Task", variable=self.type_var, value=TaskType.TASK,
                      bg='#ffffff', font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=(0, 20))
        tk.Radiobutton(type_radio_frame, text="Milestone", variable=self.type_var, value=TaskType.MILESTONE,
                      bg='#ffffff', font=('Segoe UI', 9)).pack(side=tk.LEFT)
        
        # Dates and duration
        date_frame = tk.Frame(main_frame, bg='#ffffff')
        date_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Start date
        start_frame = tk.Frame(date_frame, bg='#ffffff')
        start_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(start_frame, text="Start Date *", font=('Segoe UI', 9, 'bold'), bg='#ffffff').pack(anchor=tk.W)
        self.start_date_var = tk.StringVar(
            value=self.task.start_date.strftime('%Y-%m-%d') if self.task else datetime.now().strftime('%Y-%m-%d')
        )
        tk.Entry(start_frame, textvariable=self.start_date_var, font=('Segoe UI', 9), width=20).pack(anchor=tk.W, pady=(5, 0))
        
        # Duration
        duration_frame = tk.Frame(date_frame, bg='#ffffff')
        duration_frame.pack(fill=tk.X)
        
        tk.Label(duration_frame, text="Duration (days)", font=('Segoe UI', 9, 'bold'), bg='#ffffff').pack(anchor=tk.W)
        self.duration_var = tk.StringVar(value=str(self.task.duration) if self.task else "1")
        tk.Entry(duration_frame, textvariable=self.duration_var, font=('Segoe UI', 9), width=20).pack(anchor=tk.W, pady=(5, 0))
        
        # Color
        color_frame = tk.Frame(main_frame, bg='#ffffff')
        color_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(color_frame, text="Color", font=('Segoe UI', 9, 'bold'), bg='#ffffff').pack(anchor=tk.W)
        
        color_select_frame = tk.Frame(color_frame, bg='#ffffff')
        color_select_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.color_button = tk.Button(
            color_select_frame, bg=self.selected_color, width=4, height=1,
            command=self.choose_color, relief=tk.FLAT, border=2
        )
        self.color_button.pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Label(color_select_frame, text=self.selected_color, font=('Segoe UI', 9), bg='#ffffff').pack(side=tk.LEFT)
        
        # Progress
        self.add_field(main_frame, "Progress (%)", "progress", 
                      str(self.task.progress) if self.task else "0")
        
        # Assignee
        self.add_field(main_frame, "Assignee", "assignee", 
                      self.task.assignee if self.task else "")
        
        # Priority
        priority_frame = tk.Frame(main_frame, bg='#ffffff')
        priority_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(priority_frame, text="Priority", font=('Segoe UI', 9, 'bold'), bg='#ffffff').pack(anchor=tk.W)
        
        self.priority_var = tk.StringVar(value=self.task.priority if self.task else "Normal")
        priority_combo = ttk.Combobox(priority_frame, textvariable=self.priority_var, 
                                     values=["Low", "Normal", "High", "Critical"],
                                     state="readonly", width=17)
        priority_combo.pack(anchor=tk.W, pady=(5, 0))
        
        # Dependencies
        self.add_field(main_frame, "Dependencies (comma-separated task IDs)", "dependencies",
                      ", ".join(self.task.dependencies) if self.task else "")
        
        # Notes
        notes_frame = tk.Frame(main_frame, bg='#ffffff')
        notes_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(notes_frame, text="Notes", font=('Segoe UI', 9, 'bold'), bg='#ffffff').pack(anchor=tk.W)
        
        self.notes_text = tk.Text(notes_frame, font=('Segoe UI', 9), height=4, width=50, wrap=tk.WORD)
        self.notes_text.pack(fill=tk.X, pady=(5, 0))
        
        if self.task and self.task.notes:
            self.notes_text.insert('1.0', self.task.notes)
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg='#ffffff')
        button_frame.pack(fill=tk.X)
        
        tk.Button(button_frame, text="Cancel", font=('Segoe UI', 9), 
                 bg='#6c757d', fg='white', border=0, padx=20, pady=8,
                 command=self.cancel).pack(side=tk.RIGHT, padx=(10, 0))
        
        tk.Button(button_frame, text="Save", font=('Segoe UI', 9),
                 bg='#28a745', fg='white', border=0, padx=20, pady=8,
                 command=self.save).pack(side=tk.RIGHT)
    
    def add_field(self, parent, label: str, field_name: str, default_value: str = ""):
        """Add a labeled input field"""
        frame = tk.Frame(parent, bg='#ffffff')
        frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(frame, text=label, font=('Segoe UI', 9, 'bold'), bg='#ffffff').pack(anchor=tk.W)
        
        var = tk.StringVar(value=default_value)
        setattr(self, f"{field_name}_var", var)
        
        tk.Entry(frame, textvariable=var, font=('Segoe UI', 9), width=50).pack(anchor=tk.W, pady=(5, 0))
    
    def choose_color(self):
        """Open color chooser dialog"""
        color = colorchooser.askcolor(title="Choose task color")[1]
        if color:
            self.selected_color = color
            self.color_button.config(bg=color)
    
    def save(self):
        """Save the task data"""
        try:
            # Validate required fields
            if not self.name_var.get().strip():
                messagebox.showerror("Error", "Task name is required")
                return
            
            # Parse and validate data
            start_date = datetime.strptime(self.start_date_var.get(), '%Y-%m-%d')
            duration = int(self.duration_var.get()) if self.type_var.get() != TaskType.MILESTONE else 0
            progress = float(self.progress_var.get() or 0)
            
            dependencies = [dep.strip() for dep in self.dependencies_var.get().split(",") if dep.strip()]
            
            self.result = {
                'name': self.name_var.get().strip(),
                'start_date': start_date,
                'duration': duration,
                'task_type': self.type_var.get(),
                'color': self.selected_color,
                'dependencies': dependencies,
                'progress': max(0, min(100, progress)),
                'assignee': self.assignee_var.get().strip(),
                'priority': self.priority_var.get(),
                'notes': self.notes_text.get('1.0', tk.END).strip()
            }
            
            self.dialog.destroy()
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")
    
    def cancel(self):
        """Cancel the dialog"""
        self.dialog.destroy()