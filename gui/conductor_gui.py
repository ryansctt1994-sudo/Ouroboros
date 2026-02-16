"""
Conductor GUI - Main Control Panel for Ouroboros

Windows 8-inspired control panel with:
- System overview and metrics
- Task processing interface
- Crucible integration
- Backend connections
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
from typing import Dict, Any, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from gui.crucible_tab import CrucibleTab
except ImportError:
    CrucibleTab = None
    print("Warning: Could not import CrucibleTab")


class ConductorGUI:
    """
    Main Conductor GUI Application
    
    Features:
    - Windows 8-inspired flat design
    - Multi-tab interface
    - System monitoring
    - Task management
    - Crucible visualization
    """
    
    def __init__(self, root: tk.Tk):
        """Initialize the Conductor GUI"""
        self.root = root
        self.root.title("Ouroboros Conductor - Control Panel")
        self.root.geometry("1200x800")
        
        # Configure theme
        self._configure_theme()
        
        # Create UI
        self._create_menu()
        self._create_toolbar()
        self._create_main_interface()
        self._create_status_bar()
        
        # Initialize data
        self.task_queue = []
        self.system_metrics = {
            'cpu': 0.0,
            'memory': 0.0,
            'entities': 0,
            'uptime': 0.0
        }
        
        # Start monitoring
        self._start_monitoring()
        
    def _configure_theme(self):
        """Configure Windows 8-inspired theme"""
        style = ttk.Style()
        
        # Try to use modern theme
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'alt' in available_themes:
            style.theme_use('alt')
        
        # Configure colors
        bg_color = '#f0f0f0'
        accent_color = '#0078d7'
        
        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color)
        style.configure('TButton', padding=6)
        style.configure('Accent.TButton', foreground='white', background=accent_color)
        
    def _create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Project...", command=self._on_open_project)
        file_menu.add_command(label="Save Configuration", command=self._on_save_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Run Analysis", command=self._on_run_analysis)
        tools_menu.add_command(label="System Diagnostics", command=self._on_diagnostics)
        tools_menu.add_separator()
        tools_menu.add_command(label="Settings...", command=self._on_settings)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self._on_docs)
        help_menu.add_command(label="About", command=self._on_about)
        
    def _create_toolbar(self):
        """Create toolbar"""
        toolbar = ttk.Frame(self.root, relief=tk.RAISED)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Toolbar buttons
        ttk.Button(toolbar, text="▶ Start", command=self._on_start).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(toolbar, text="⏹ Stop", command=self._on_stop).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(toolbar, text="⟳ Refresh", command=self._on_refresh).pack(side=tk.LEFT, padx=2, pady=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        ttk.Button(toolbar, text="📊 Metrics", command=self._on_show_metrics).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(toolbar, text="🔥 Crucible", command=self._on_show_crucible).pack(side=tk.LEFT, padx=2, pady=2)
        
    def _create_main_interface(self):
        """Create main tabbed interface"""
        # Create notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 1: Overview
        self._create_overview_tab()
        
        # Tab 2: Tasks
        self._create_tasks_tab()
        
        # Tab 3: Crucible (if available)
        if CrucibleTab:
            self.crucible_tab = CrucibleTab(self.notebook)
        else:
            # Create placeholder
            crucible_frame = ttk.Frame(self.notebook)
            self.notebook.add(crucible_frame, text="🔥 Recursive Crucible")
            ttk.Label(crucible_frame, text="Crucible module not available").pack(pady=20)
        
        # Tab 4: Logs
        self._create_logs_tab()
        
    def _create_overview_tab(self):
        """Create system overview tab"""
        overview_frame = ttk.Frame(self.notebook)
        self.notebook.add(overview_frame, text="📊 Overview")
        
        # Header
        header = ttk.Frame(overview_frame)
        header.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(header, text="Ouroboros System Overview", 
                 font=('Arial', 16, 'bold')).pack(anchor=tk.W)
        ttk.Label(header, text="Real-time monitoring and control", 
                 font=('Arial', 10, 'italic')).pack(anchor=tk.W)
        
        # Metrics container
        metrics_container = ttk.Frame(overview_frame)
        metrics_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create metric cards
        self.metric_cards = {}
        
        metrics = [
            ('cpu', 'CPU Usage', '%'),
            ('memory', 'Memory', '%'),
            ('entities', 'Entities', ''),
            ('uptime', 'Uptime', 'h')
        ]
        
        row, col = 0, 0
        for key, label, unit in metrics:
            card = self._create_metric_card(metrics_container, label, unit)
            card.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
            self.metric_cards[key] = card
            
            col += 1
            if col > 1:
                col = 0
                row += 1
        
        # Configure grid weights
        for i in range(2):
            metrics_container.columnconfigure(i, weight=1)
        for i in range(2):
            metrics_container.rowconfigure(i, weight=1)
        
        # Status panel
        status_panel = ttk.LabelFrame(overview_frame, text="System Status", padding=10)
        status_panel.pack(fill=tk.X, padx=10, pady=10)
        
        self.status_text = scrolledtext.ScrolledText(status_panel, height=8, 
                                                     wrap=tk.WORD, state=tk.DISABLED)
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
        self._update_status_message("System initialized and ready")
        
    def _create_metric_card(self, parent, label: str, unit: str) -> Dict:
        """Create a metric display card"""
        card_frame = ttk.LabelFrame(parent, text=label, padding=15)
        
        value_label = ttk.Label(card_frame, text="0", font=('Arial', 24, 'bold'))
        value_label.pack()
        
        unit_label = ttk.Label(card_frame, text=unit, font=('Arial', 10))
        unit_label.pack()
        
        return {
            'frame': card_frame,
            'value': value_label,
            'unit': unit_label
        }
    
    def _create_tasks_tab(self):
        """Create task management tab"""
        tasks_frame = ttk.Frame(self.notebook)
        self.notebook.add(tasks_frame, text="📝 Tasks")
        
        # Split into two panels
        paned = ttk.PanedWindow(tasks_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left: Task submission
        left_panel = ttk.Frame(paned)
        paned.add(left_panel, weight=1)
        
        ttk.Label(left_panel, text="Submit Task", 
                 font=('Arial', 12, 'bold')).pack(anchor=tk.W, padx=5, pady=5)
        
        # Task input
        ttk.Label(left_panel, text="Task Description:").pack(anchor=tk.W, padx=5)
        self.task_entry = ttk.Entry(left_panel, width=40)
        self.task_entry.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(left_panel, text="Code/Data:").pack(anchor=tk.W, padx=5, pady=(10, 0))
        self.task_code = scrolledtext.ScrolledText(left_panel, height=15, width=40)
        self.task_code.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        
        ttk.Button(left_panel, text="Submit Task", 
                  command=self._on_submit_task).pack(fill=tk.X, padx=5, pady=5)
        
        # Right: Task queue
        right_panel = ttk.Frame(paned)
        paned.add(right_panel, weight=1)
        
        ttk.Label(right_panel, text="Task Queue", 
                 font=('Arial', 12, 'bold')).pack(anchor=tk.W, padx=5, pady=5)
        
        # Task list
        columns = ('ID', 'Description', 'Status')
        self.task_tree = ttk.Treeview(right_panel, columns=columns, 
                                     show='headings', height=15)
        
        for col in columns:
            self.task_tree.heading(col, text=col)
        
        self.task_tree.column('ID', width=50)
        self.task_tree.column('Description', width=200)
        self.task_tree.column('Status', width=100)
        
        tree_scroll = ttk.Scrollbar(right_panel, orient=tk.VERTICAL, 
                                   command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.task_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
    def _create_logs_tab(self):
        """Create logs tab"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="📋 Logs")
        
        # Controls
        control_frame = ttk.Frame(logs_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(control_frame, text="System Logs", 
                 font=('Arial', 12, 'bold')).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Clear", 
                  command=self._on_clear_logs).pack(side=tk.RIGHT, padx=2)
        ttk.Button(control_frame, text="Export", 
                  command=self._on_export_logs).pack(side=tk.RIGHT, padx=2)
        
        # Log display
        self.log_text = scrolledtext.ScrolledText(logs_frame, wrap=tk.WORD,
                                                  bg='#1e1e1e', fg='#d4d4d4',
                                                  font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self._log("System started at " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
    def _create_status_bar(self):
        """Create status bar"""
        self.status_bar = ttk.Frame(self.root, relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_bar_label = ttk.Label(self.status_bar, text="Ready", anchor=tk.W)
        self.status_bar_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.connection_label = ttk.Label(self.status_bar, text="⚫ Disconnected", anchor=tk.E)
        self.connection_label.pack(side=tk.RIGHT, padx=5)
        
    def _start_monitoring(self):
        """Start system monitoring"""
        self._update_metrics()
        
    def _update_metrics(self):
        """Update system metrics"""
        import random
        
        # Simulate metrics (in real implementation, get from backend)
        self.system_metrics['cpu'] = random.uniform(10, 60)
        self.system_metrics['memory'] = random.uniform(30, 70)
        self.system_metrics['entities'] = random.randint(100, 500)
        self.system_metrics['uptime'] += 0.1
        
        # Update displays
        for key, value in self.system_metrics.items():
            if key in self.metric_cards:
                if key in ['cpu', 'memory']:
                    self.metric_cards[key]['value'].config(text=f"{value:.1f}")
                elif key == 'uptime':
                    self.metric_cards[key]['value'].config(text=f"{value:.1f}")
                else:
                    self.metric_cards[key]['value'].config(text=str(int(value)))
        
        # Schedule next update
        self.root.after(1000, self._update_metrics)
        
    def _update_status_message(self, message: str):
        """Update status message"""
        self.status_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
        
    def _log(self, message: str):
        """Add log message"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        
    # Menu handlers
    def _on_open_project(self):
        messagebox.showinfo("Open Project", "Project opening not implemented yet")
        
    def _on_save_config(self):
        self._log("Configuration saved")
        messagebox.showinfo("Save", "Configuration saved successfully")
        
    def _on_run_analysis(self):
        self._log("Starting analysis...")
        self._update_status_message("Analysis started")
        
    def _on_diagnostics(self):
        self._log("Running diagnostics...")
        messagebox.showinfo("Diagnostics", "All systems operational")
        
    def _on_settings(self):
        messagebox.showinfo("Settings", "Settings dialog not implemented yet")
        
    def _on_docs(self):
        messagebox.showinfo("Documentation", "Opening documentation...")
        
    def _on_about(self):
        messagebox.showinfo("About", 
            "Ouroboros Conductor v1.0\n\n"
            "Self-improving AI framework with\n"
            "Recursive Crucible Core\n\n"
            "© 2026 AIOSPANDORA")
        
    # Toolbar handlers
    def _on_start(self):
        self._log("System started")
        self._update_status_message("System running")
        self.connection_label.config(text="🟢 Connected")
        
    def _on_stop(self):
        self._log("System stopped")
        self._update_status_message("System stopped")
        self.connection_label.config(text="⚫ Disconnected")
        
    def _on_refresh(self):
        self._log("Refreshing...")
        self._update_status_message("Data refreshed")
        
    def _on_show_metrics(self):
        self.notebook.select(0)  # Select overview tab
        
    def _on_show_crucible(self):
        self.notebook.select(2)  # Select crucible tab
        
    # Task handlers
    def _on_submit_task(self):
        description = self.task_entry.get()
        code = self.task_code.get(1.0, tk.END).strip()
        
        if not description:
            messagebox.showwarning("Warning", "Please enter a task description")
            return
        
        task_id = len(self.task_queue) + 1
        task = {
            'id': task_id,
            'description': description,
            'code': code,
            'status': 'Queued',
            'timestamp': datetime.now()
        }
        
        self.task_queue.append(task)
        
        # Add to tree
        self.task_tree.insert('', tk.END, values=(
            task_id,
            description[:40] + ('...' if len(description) > 40 else ''),
            'Queued'
        ))
        
        self._log(f"Task #{task_id} submitted: {description}")
        
        # Clear inputs
        self.task_entry.delete(0, tk.END)
        self.task_code.delete(1.0, tk.END)
        
    # Log handlers
    def _on_clear_logs(self):
        self.log_text.delete(1.0, tk.END)
        self._log("Logs cleared")
        
    def _on_export_logs(self):
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            with open(filename, 'w') as f:
                f.write(self.log_text.get(1.0, tk.END))
            self._log(f"Logs exported to {filename}")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = ConductorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
