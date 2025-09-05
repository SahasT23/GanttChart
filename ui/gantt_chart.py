"""
Professional Gantt Chart Widget with horizontal scrolling and modern styling
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from typing import List, Callable, Optional
import math

from models.task import Task, TaskType, Project

class GanttChart(tk.Frame):
    """Professional Gantt Chart widget with horizontal scrolling"""
    
    def __init__(self, parent, project: Project, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.project = project
        self.selected_task = None
        self.on_task_selected: Optional[Callable] = None
        self.on_task_double_click: Optional[Callable] = None
        
        # Chart configuration
        self.row_height = 40
        self.header_height = 80
        self.day_width = 30
        self.min_day_width = 20
        self.max_day_width = 100
        
        # Timeline configuration
        self.timeline_start = datetime(2025, 1, 1)
        self.timeline_end = datetime(2025, 12, 31)
        self.visible_days = 30  # Number of days visible at once
        
        # Colors
        self.colors = {
            'background': '#ffffff',
            'grid': '#e0e0e0',
            'header_bg': '#f5f5f5',
            'header_text': '#333333',
            'today_line': '#ff4444',
            'weekend': '#f9f9f9',
            'selected': '#0078d4',
            'milestone': '#ff6b35',
            'dependency_arrow': '#666666'
        }
        
        self.setup_ui()
        self.update_timeline()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main container with scrollbars
        self.main_frame = tk.Frame(self, bg=self.colors['background'])
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas with scrollbars
        self.canvas = tk.Canvas(self.main_frame, bg=self.colors['background'])
        
        # Horizontal scrollbar
        self.h_scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=self.h_scrollbar.set)
        
        # Vertical scrollbar
        self.v_scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set)
        
        # Pack scrollbars and canvas
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind events
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        self.canvas.bind('<Double-Button-1>', self.on_canvas_double_click)
        self.canvas.bind('<MouseWheel>', self.on_mouse_wheel)
        self.canvas.bind('<Control-MouseWheel>', self.on_zoom)
        self.bind_all('<Control-plus>', lambda e: self.zoom_in())
        self.bind_all('<Control-minus>', lambda e: self.zoom_out())
        
        # Create toolbar
        self.create_toolbar()
        
    def create_toolbar(self):
        """Create the chart toolbar"""
        toolbar = tk.Frame(self, bg='#f0f0f0', height=35)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        toolbar.pack_propagate(False)
        
        # Zoom controls
        tk.Label(toolbar, text="Zoom:", bg='#f0f0f0').pack(side=tk.LEFT, padx=(10, 5))
        
        zoom_frame = tk.Frame(toolbar, bg='#f0f0f0')
        zoom_frame.pack(side=tk.LEFT)
        
        ttk.Button(zoom_frame, text="−", width=3, command=self.zoom_out).pack(side=tk.LEFT)
        ttk.Button(zoom_frame, text="+", width=3, command=self.zoom_in).pack(side=tk.LEFT)
        ttk.Button(zoom_frame, text="Fit", command=self.zoom_to_fit).pack(side=tk.LEFT, padx=(5, 0))
        
        # View controls
        tk.Label(toolbar, text="View:", bg='#f0f0f0').pack(side=tk.LEFT, padx=(20, 5))
        
        view_frame = tk.Frame(toolbar, bg='#f0f0f0')
        view_frame.pack(side=tk.LEFT)
        
        ttk.Button(view_frame, text="Today", command=self.scroll_to_today).pack(side=tk.LEFT)
        ttk.Button(view_frame, text="Start", command=self.scroll_to_start).pack(side=tk.LEFT)
        
        # Timeline info
        self.timeline_label = tk.Label(toolbar, text="", bg='#f0f0f0', fg='#666666')
        self.timeline_label.pack(side=tk.RIGHT, padx=(0, 10))
        
    def update_timeline(self):
        """Update the timeline based on project tasks"""
        if not self.project.tasks:
            return
        
        # Calculate project timeline
        start_dates = [task.start_date for task in self.project.tasks]
        end_dates = [task.end_date for task in self.project.tasks]
        
        project_start = min(start_dates)
        project_end = max(end_dates)
        
        # Add padding
        self.timeline_start = project_start - timedelta(days=7)
        self.timeline_end = project_end + timedelta(days=30)
        
        # Update timeline label
        total_days = (self.timeline_end - self.timeline_start).days
        self.timeline_label.config(
            text=f"{self.timeline_start.strftime('%Y-%m-%d')} to {self.timeline_end.strftime('%Y-%m-%d')} ({total_days} days)"
        )
        
        self.draw_chart()
        
    def draw_chart(self):
        """Draw the complete Gantt chart"""
        self.canvas.delete("all")
        
        if not self.project.tasks:
            self.draw_empty_state()
            return
        
        # Calculate dimensions
        total_days = (self.timeline_end - self.timeline_start).days
        chart_width = total_days * self.day_width
        chart_height = len(self.project.tasks) * self.row_height + self.header_height
        
        # Configure canvas scroll region
        self.canvas.configure(scrollregion=(0, 0, chart_width, chart_height))
        
        # Draw components
        self.draw_header(chart_width)
        self.draw_grid(chart_width, chart_height)
        self.draw_tasks()
        self.draw_today_line(chart_height)
        self.draw_dependencies()
        
    def draw_empty_state(self):
        """Draw empty state message"""
        self.canvas.create_text(
            200, 100, 
            text="No tasks to display\nAdd tasks to see the Gantt chart",
            font=('Arial', 12),
            fill='#888888',
            justify=tk.CENTER
        )
        
    def draw_header(self, chart_width):
        """Draw the timeline header"""
        # Header background
        self.canvas.create_rectangle(
            0, 0, chart_width, self.header_height,
            fill=self.colors['header_bg'], outline=self.colors['grid']
        )
        
        # Draw months and days
        current_date = self.timeline_start
        x = 0
        
        while current_date <= self.timeline_end:
            day_x = x * self.day_width
            
            # Month headers (first day of month)
            if current_date.day == 1:
                month_width = self.get_month_width(current_date)
                
                # Month background
                self.canvas.create_rectangle(
                    day_x, 0, day_x + month_width, 25,
                    fill=self.colors['header_bg'], outline=self.colors['grid']
                )
                
                # Month label
                self.canvas.create_text(
                    day_x + month_width // 2, 12,
                    text=current_date.strftime('%B %Y'),
                    font=('Arial', 10, 'bold'),
                    fill=self.colors['header_text']
                )
            
            # Day header
            day_bg = self.colors['weekend'] if current_date.weekday() >= 5 else self.colors['background']
            
            self.canvas.create_rectangle(
                day_x, 25, day_x + self.day_width, self.header_height,
                fill=day_bg, outline=self.colors['grid']
            )
            
            # Day number
            self.canvas.create_text(
                day_x + self.day_width // 2, 40,
                text=current_date.strftime('%d'),
                font=('Arial', 8),
                fill=self.colors['header_text']
            )
            
            # Day name (abbreviated)
            self.canvas.create_text(
                day_x + self.day_width // 2, 55,
                text=current_date.strftime('%a')[0],
                font=('Arial', 7),
                fill='#666666'
            )
            
            current_date += timedelta(days=1)
            x += 1
            
    def get_month_width(self, month_start):
        """Calculate the width of a month in pixels"""
        # Get the last day of the month
        if month_start.month == 12:
            next_month = month_start.replace(year=month_start.year + 1, month=1, day=1)
        else:
            next_month = month_start.replace(month=month_start.month + 1, day=1)
        
        month_days = (next_month - month_start).days
        return month_days * self.day_width
        
    def draw_grid(self, chart_width, chart_height):
        """Draw the background grid"""
        # Vertical lines (days)
        current_date = self.timeline_start
        x = 0
        
        while x * self.day_width <= chart_width:
            line_x = x * self.day_width
            
            # Weekend background
            if current_date.weekday() >= 5:
                self.canvas.create_rectangle(
                    line_x, self.header_height, line_x + self.day_width, chart_height,
                    fill=self.colors['weekend'], outline=""
                )
            
            # Vertical grid lines
            self.canvas.create_line(
                line_x, self.header_height, line_x, chart_height,
                fill=self.colors['grid'], width=1
            )
            
            current_date += timedelta(days=1)
            x += 1
        
        # Horizontal lines (tasks)
        for i in range(len(self.project.tasks) + 1):
            y = self.header_height + i * self.row_height
            self.canvas.create_line(
                0, y, chart_width, y,
                fill=self.colors['grid'], width=1
            )
    
    def draw_tasks(self):
        """Draw all task bars"""
        tasks = self.project.get_tasks_sorted_by_date()
        
        for i, task in enumerate(tasks):
            y = self.header_height + i * self.row_height
            self.draw_task_bar(task, y)
    
    def draw_task_bar(self, task: Task, y: int):
        """Draw a single task bar"""
        # Calculate position
        start_x = self.date_to_x(task.start_date)
        
        if task.is_milestone:
            self.draw_milestone(task, start_x, y)
        else:
            self.draw_task_rect(task, start_x, y)
    
    def draw_task_rect(self, task: Task, start_x: int, y: int):
        """Draw a regular task rectangle"""
        width = task.duration * self.day_width
        
        # Task background
        rect_id = self.canvas.create_rectangle(
            start_x, y + 5, start_x + width, y + self.row_height - 5,
            fill=task.color, outline='#333333', width=1,
            tags=('task', task.task_id)
        )
        
        # Progress bar
        if task.progress > 0:
            progress_width = (width * task.progress) / 100
            self.canvas.create_rectangle(
                start_x, y + 5, start_x + progress_width, y + self.row_height - 5,
                fill=self.darken_color(task.color), outline="",
                tags=('progress', task.task_id)
            )
        
        # Task text
        text_x = start_x + width // 2
        text_y = y + self.row_height // 2
        
        self.canvas.create_text(
            text_x, text_y,
            text=task.name,
            font=('Arial', 9, 'bold'),
            fill='white' if self.is_dark_color(task.color) else 'black',
            tags=('task_text', task.task_id)
        )
        
        # Status indicators
        if task.is_overdue:
            self.canvas.create_text(
                start_x + width + 5, text_y,
                text="⚠", font=('Arial', 12),
                fill='#ff4444',
                tags=('status', task.task_id)
            )
    
    def draw_milestone(self, task: Task, start_x: int, y: int):
        """Draw a milestone diamond"""
        center_y = y + self.row_height // 2
        size = 8
        
        # Diamond shape
        points = [
            start_x, center_y - size,  # top
            start_x + size, center_y,  # right
            start_x, center_y + size,  # bottom
            start_x - size, center_y   # left
        ]
        
        self.canvas.create_polygon(
            points,
            fill=self.colors['milestone'], outline='#333333', width=2,
            tags=('milestone', task.task_id)
        )
        
        # Milestone text
        self.canvas.create_text(
            start_x + 15, center_y,
            text=task.name,
            font=('Arial', 9, 'bold'),
            fill='#333333',
            anchor=tk.W,
            tags=('milestone_text', task.task_id)
        )
    
    def draw_dependencies(self):
        """Draw dependency arrows"""
        tasks = self.project.get_tasks_sorted_by_date()
        task_positions = {task.task_id: i for i, task in enumerate(tasks)}
        
        for i, task in enumerate(tasks):
            for dep_id in task.dependencies:
                dep_task = self.project.get_task(dep_id)
                if dep_task and dep_id in task_positions:
                    self.draw_dependency_arrow(dep_task, task, task_positions)
    
    def draw_dependency_arrow(self, from_task: Task, to_task: Task, task_positions: dict):
        """Draw a dependency arrow between two tasks"""
        from_y = self.header_height + task_positions[from_task.task_id] * self.row_height + self.row_height // 2
        to_y = self.header_height + task_positions[to_task.task_id] * self.row_height + self.row_height // 2
        
        from_x = self.date_to_x(from_task.end_date)
        to_x = self.date_to_x(to_task.start_date)
        
        # Draw arrow line
        self.canvas.create_line(
            from_x, from_y, to_x - 10, to_y,
            fill=self.colors['dependency_arrow'], width=2,
            arrow=tk.LAST, arrowshape=(10, 12, 3),
            tags=('dependency',)
        )
    
    def draw_today_line(self, chart_height):
        """Draw the 'today' indicator line"""
        today = datetime.now()
        if self.timeline_start <= today <= self.timeline_end:
            today_x = self.date_to_x(today)
            self.canvas.create_line(
                today_x, 0, today_x, chart_height,
                fill=self.colors['today_line'], width=2,
                tags=('today',)
            )
            
            # Today label
            self.canvas.create_text(
                today_x + 5, 10,
                text="TODAY",
                font=('Arial', 8, 'bold'),
                fill=self.colors['today_line'],
                anchor=tk.W,
                tags=('today_label',)
            )
    
    def date_to_x(self, date: datetime) -> int:
        """Convert a date to x coordinate"""
        days_from_start = (date - self.timeline_start).days
        return days_from_start * self.day_width
    
    def x_to_date(self, x: int) -> datetime:
        """Convert x coordinate to date"""
        days_from_start = x // self.day_width
        return self.timeline_start + timedelta(days=days_from_start)
    
    def on_canvas_click(self, event):
        """Handle canvas click events"""
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Find clicked task
        clicked_items = self.canvas.find_overlapping(canvas_x, canvas_y, canvas_x, canvas_y)
        
        task_id = None
        for item in clicked_items:
            tags = self.canvas.gettags(item)
            if 'task' in tags or 'milestone' in tags:
                for tag in tags:
                    if tag not in ['task', 'milestone', 'progress', 'task_text', 'milestone_text', 'status']:
                        task_id = tag
                        break
                break
        
        if task_id:
            self.select_task(task_id)
        else:
            self.select_task(None)
    
    def on_canvas_double_click(self, event):
        """Handle canvas double-click events"""
        if self.selected_task and self.on_task_double_click:
            self.on_task_double_click(self.selected_task)
    
    def select_task(self, task_id: str = None):
        """Select a task and highlight it"""
        # Clear previous selection
        self.canvas.delete('selection')
        
        if task_id:
            self.selected_task = task_id
            task = self.project.get_task(task_id)
            
            if task:
                # Highlight selected task
                tasks = self.project.get_tasks_sorted_by_date()
                task_index = next((i for i, t in enumerate(tasks) if t.task_id == task_id), -1)
                
                if task_index >= 0:
                    y = self.header_height + task_index * self.row_height
                    start_x = self.date_to_x(task.start_date)
                    
                    if task.is_milestone:
                        size = 12
                        center_y = y + self.row_height // 2
                        self.canvas.create_oval(
                            start_x - size, center_y - size,
                            start_x + size, center_y + size,
                            outline=self.colors['selected'], width=3,
                            fill="", tags=('selection',)
                        )
                    else:
                        width = task.duration * self.day_width
                        self.canvas.create_rectangle(
                            start_x - 2, y + 3, start_x + width + 2, y + self.row_height - 3,
                            outline=self.colors['selected'], width=3,
                            fill="", tags=('selection',)
                        )
                
                # Notify selection callback
                if self.on_task_selected:
                    self.on_task_selected(task)
        else:
            self.selected_task = None
            if self.on_task_selected:
                self.on_task_selected(None)
    
    def on_mouse_wheel(self, event):
        """Handle mouse wheel scrolling"""
        if event.state & 0x4:  # Ctrl key
            return
        
        # Horizontal scroll
        self.canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def on_zoom(self, event):
        """Handle zoom with Ctrl+mouse wheel"""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
    
    def zoom_in(self):
        """Zoom in the chart"""
        if self.day_width < self.max_day_width:
            self.day_width = min(self.max_day_width, self.day_width + 5)
            self.draw_chart()
    
    def zoom_out(self):
        """Zoom out the chart"""
        if self.day_width > self.min_day_width:
            self.day_width = max(self.min_day_width, self.day_width - 5)
            self.draw_chart()
    
    def zoom_to_fit(self):
        """Zoom to fit all tasks in view"""
        if not self.project.tasks:
            return
        
        canvas_width = self.canvas.winfo_width()
        total_days = (self.timeline_end - self.timeline_start).days
        
        if total_days > 0:
            optimal_width = (canvas_width - 50) // total_days
            self.day_width = max(self.min_day_width, min(self.max_day_width, optimal_width))
            self.draw_chart()
    
    def scroll_to_today(self):
        """Scroll to today's date"""
        today = datetime.now()
        if self.timeline_start <= today <= self.timeline_end:
            today_x = self.date_to_x(today)
            canvas_width = self.canvas.winfo_width()
            
            # Scroll to center today
            self.canvas.xview_moveto((today_x - canvas_width // 2) / (self.canvas.bbox("all")[2]))
    
    def scroll_to_start(self):
        """Scroll to project start"""
        self.canvas.xview_moveto(0)
    
    def refresh(self):
        """Refresh the chart display"""
        self.update_timeline()
    
    def set_project(self, project: Project):
        """Set a new project and refresh the chart"""
        self.project = project
        self.selected_task = None
        self.refresh()
    
    # Utility methods
    def darken_color(self, color: str, factor: float = 0.3) -> str:
        """Darken a hex color"""
        try:
            # Remove # if present
            color = color.lstrip('#')
            
            # Convert to RGB
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)
            
            # Darken
            r = int(r * (1 - factor))
            g = int(g * (1 - factor))
            b = int(b * (1 - factor))
            
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return "#333333"
    
    def is_dark_color(self, color: str) -> bool:
        """Check if a color is dark"""
        try:
            color = color.lstrip('#')
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)
            
            # Calculate luminance
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            return luminance < 0.5
        except:
            return False