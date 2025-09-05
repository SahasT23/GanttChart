
"""
Professional Gantt Chart Application
Main entry point for the application
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import GanttMainWindow

def main():
    """Main entry point for the Gantt Chart application"""
    root = tk.Tk()
    
    # Configure the root window
    root.title("Professional Gantt Chart")
    root.geometry("1600x900")
    root.minsize(1200, 700)
    
    # Set application icon and style
    try:
        root.iconbitmap('assets/icon.ico')  # Add your icon file
    except:
        pass  # Icon file not found, continue without it
    
    # Create and run the main application
    app = GanttMainWindow(root)
    
    # Center the window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    # Start the application
    root.mainloop()

if __name__ == "__main__":
    main()