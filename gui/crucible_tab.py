"""
Crucible Tab - Visualization Layer for Recursive Crucible Monitoring

Provides real-time monitoring interface for:
- Iteration history and progress
- Weakness detection details
- Validation progress
- Fix logs and application status
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Dict, Any, List, Optional
from datetime import datetime
import json


class CrucibleTab:
    """
    Dedicated visualization layer for Recursive Crucible monitoring
    
    Features:
    - Split panel layout (Windows 8-inspired)
    - Real-time iteration tracking
    - Weakness and fix visualization
    - Validation progress monitoring
    """
    
    def __init__(self, parent_notebook: ttk.Notebook):
        """Initialize crucible tab"""
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="🔥 Recursive Crucible")
        
        # Data storage
        self.iteration_data: List[Dict[str, Any]] = []
        self.current_iteration = 0
        
        # Create UI
        self._create_ui()
        
    def _create_ui(self):
        """Create the user interface"""
        # Main container with two columns
        main_container = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Iteration History and Controls
        left_panel = ttk.Frame(main_container)
        main_container.add(left_panel, weight=1)
        
        # Right panel - Details and Logs
        right_panel = ttk.Frame(main_container)
        main_container.add(right_panel, weight=2)
        
        # Build left panel
        self._create_left_panel(left_panel)
        
        # Build right panel
        self._create_right_panel(right_panel)
        
    def _create_left_panel(self, parent):
        """Create left panel with controls and iteration history"""
        # Header
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(header_frame, text="Recursive Crucible Core", 
                 font=('Arial', 14, 'bold')).pack(anchor=tk.W)
        ttk.Label(header_frame, text="Self-Improving Framework", 
                 font=('Arial', 9, 'italic')).pack(anchor=tk.W)
        
        # Control buttons
        control_frame = ttk.LabelFrame(parent, text="Controls", padding=10)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.start_button = ttk.Button(control_frame, text="▶ Start Analysis", 
                                      command=self._on_start_analysis)
        self.start_button.pack(fill=tk.X, pady=2)
        
        self.stop_button = ttk.Button(control_frame, text="⏹ Stop", 
                                     command=self._on_stop, state=tk.DISABLED)
        self.stop_button.pack(fill=tk.X, pady=2)
        
        self.export_button = ttk.Button(control_frame, text="💾 Export Results", 
                                       command=self._on_export)
        self.export_button.pack(fill=tk.X, pady=2)
        
        # Status
        status_frame = ttk.LabelFrame(parent, text="Status", padding=10)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Ready", 
                                      font=('Arial', 10, 'bold'))
        self.status_label.pack(anchor=tk.W)
        
        # Progress
        progress_frame = ttk.LabelFrame(parent, text="Progress", padding=10)
        progress_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                           maximum=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=2)
        
        self.progress_label = ttk.Label(progress_frame, text="0 / 0 iterations")
        self.progress_label.pack(anchor=tk.W)
        
        # Iteration History
        history_frame = ttk.LabelFrame(parent, text="Iteration History", padding=5)
        history_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview for iteration history
        columns = ('Iter', 'Weaknesses', 'Fixes', 'Score')
        self.history_tree = ttk.Treeview(history_frame, columns=columns, 
                                        show='tree headings', height=10)
        
        self.history_tree.heading('#0', text='#')
        self.history_tree.column('#0', width=40)
        
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=80)
        
        # Scrollbar for treeview
        tree_scroll = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, 
                                    command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.history_tree.bind('<<TreeviewSelect>>', self._on_iteration_select)
        
    def _create_right_panel(self, parent):
        """Create right panel with details and logs"""
        # Create notebook for tabbed interface
        right_notebook = ttk.Notebook(parent)
        right_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 1: Weakness Details
        weakness_frame = ttk.Frame(right_notebook)
        right_notebook.add(weakness_frame, text="⚠ Weaknesses")
        self._create_weakness_tab(weakness_frame)
        
        # Tab 2: Fix Details
        fix_frame = ttk.Frame(right_notebook)
        right_notebook.add(fix_frame, text="🔧 Fixes")
        self._create_fix_tab(fix_frame)
        
        # Tab 3: Validation
        validation_frame = ttk.Frame(right_notebook)
        right_notebook.add(validation_frame, text="✓ Validation")
        self._create_validation_tab(validation_frame)
        
        # Tab 4: Logs
        log_frame = ttk.Frame(right_notebook)
        right_notebook.add(log_frame, text="📋 Logs")
        self._create_log_tab(log_frame)
        
    def _create_weakness_tab(self, parent):
        """Create weakness details tab"""
        # Info
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(info_frame, text="Detected Weaknesses", 
                 font=('Arial', 11, 'bold')).pack(anchor=tk.W)
        
        # List of weaknesses
        self.weakness_text = scrolledtext.ScrolledText(parent, wrap=tk.WORD, 
                                                       height=20, width=60)
        self.weakness_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.weakness_text.config(state=tk.DISABLED)
        
    def _create_fix_tab(self, parent):
        """Create fix details tab"""
        # Info
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(info_frame, text="Applied Fixes", 
                 font=('Arial', 11, 'bold')).pack(anchor=tk.W)
        
        # List of fixes
        self.fix_text = scrolledtext.ScrolledText(parent, wrap=tk.WORD, 
                                                  height=20, width=60)
        self.fix_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.fix_text.config(state=tk.DISABLED)
        
    def _create_validation_tab(self, parent):
        """Create validation progress tab"""
        # Info
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(info_frame, text="Validation Results", 
                 font=('Arial', 11, 'bold')).pack(anchor=tk.W)
        
        # Validation details
        self.validation_text = scrolledtext.ScrolledText(parent, wrap=tk.WORD, 
                                                         height=20, width=60)
        self.validation_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.validation_text.config(state=tk.DISABLED)
        
    def _create_log_tab(self, parent):
        """Create log tab"""
        # Info
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(info_frame, text="Crucible Logs", 
                 font=('Arial', 11, 'bold')).pack(anchor=tk.W)
        
        control_frame = ttk.Frame(info_frame)
        control_frame.pack(fill=tk.X, pady=2)
        
        ttk.Button(control_frame, text="Clear Logs", 
                  command=self._on_clear_logs).pack(side=tk.LEFT)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(parent, wrap=tk.WORD, 
                                                  height=20, width=60, 
                                                  bg='#1e1e1e', fg='#d4d4d4')
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text.config(state=tk.DISABLED)
        
    def _on_start_analysis(self):
        """Handle start analysis button"""
        self.log_message("Starting recursive crucible analysis...")
        self.status_label.config(text="Running...")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # Simulate analysis (in real implementation, this would trigger the crucible)
        self._simulate_analysis()
        
    def _on_stop(self):
        """Handle stop button"""
        self.log_message("Stopping analysis...")
        self.status_label.config(text="Stopped")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
    def _on_export(self):
        """Handle export button"""
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.iteration_data, f, indent=2)
                self.log_message(f"Results exported to {filename}")
            except Exception as e:
                self.log_message(f"Error exporting: {str(e)}", level="ERROR")
    
    def _on_clear_logs(self):
        """Clear log text"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def _on_iteration_select(self, event):
        """Handle iteration selection in treeview"""
        selection = self.history_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        iteration_idx = int(self.history_tree.item(item, 'text')) - 1
        
        if 0 <= iteration_idx < len(self.iteration_data):
            self._display_iteration_details(self.iteration_data[iteration_idx])
    
    def _simulate_analysis(self):
        """Simulate crucible analysis (for demo purposes)"""
        import random
        
        # Simulate 5 iterations
        for i in range(5):
            self.current_iteration = i + 1
            
            # Generate fake data
            weaknesses = random.randint(3, 10)
            fixes = random.randint(2, weaknesses)
            score = random.uniform(0.6, 0.95)
            
            iteration_data = {
                'iteration': i + 1,
                'weaknesses': weaknesses,
                'fixes': fixes,
                'score': score,
                'timestamp': datetime.now().isoformat(),
                'details': {
                    'weakness_list': [
                        {
                            'type': 'static_analysis',
                            'location': f'sample.py:{random.randint(1, 100)}',
                            'description': 'Missing error handling',
                            'severity': random.uniform(0.3, 0.8)
                        }
                        for _ in range(weaknesses)
                    ],
                    'fix_list': [
                        {
                            'strategy': 'add_error_handling',
                            'description': 'Add try-except block',
                            'success': random.choice([True, True, False])
                        }
                        for _ in range(fixes)
                    ]
                }
            }
            
            self.add_iteration(iteration_data)
            self.update_progress(i + 1, 5)
            
            # Simulate delay
            self.frame.update()
            self.frame.after(500)
        
        # Finish
        self.status_label.config(text="Completed")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.log_message("Analysis complete!")
    
    def add_iteration(self, iteration_data: Dict[str, Any]):
        """Add iteration to history"""
        self.iteration_data.append(iteration_data)
        
        # Add to treeview
        item_id = self.history_tree.insert('', tk.END, 
                                          text=str(iteration_data['iteration']),
                                          values=(
                                              f"{iteration_data['iteration']}",
                                              f"{iteration_data['weaknesses']}",
                                              f"{iteration_data['fixes']}",
                                              f"{iteration_data['score']:.2f}"
                                          ))
        
        # Log
        self.log_message(
            f"Iteration {iteration_data['iteration']}: "
            f"{iteration_data['weaknesses']} weaknesses, "
            f"{iteration_data['fixes']} fixes, "
            f"score: {iteration_data['score']:.2f}"
        )
        
        # Auto-select latest
        self.history_tree.selection_set(item_id)
        self.history_tree.see(item_id)
        
    def update_progress(self, current: int, total: int):
        """Update progress bar"""
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_var.set(progress)
            self.progress_label.config(text=f"{current} / {total} iterations")
        
    def _display_iteration_details(self, iteration_data: Dict[str, Any]):
        """Display details for selected iteration"""
        details = iteration_data.get('details', {})
        
        # Display weaknesses
        self.weakness_text.config(state=tk.NORMAL)
        self.weakness_text.delete(1.0, tk.END)
        
        weakness_list = details.get('weakness_list', [])
        if weakness_list:
            for i, w in enumerate(weakness_list, 1):
                self.weakness_text.insert(tk.END, 
                    f"{i}. [{w.get('type', 'unknown')}] {w.get('description', 'N/A')}\n")
                self.weakness_text.insert(tk.END, 
                    f"   Location: {w.get('location', 'N/A')}\n")
                self.weakness_text.insert(tk.END, 
                    f"   Severity: {w.get('severity', 0.0):.2f}\n\n")
        else:
            self.weakness_text.insert(tk.END, "No weaknesses detected.\n")
        
        self.weakness_text.config(state=tk.DISABLED)
        
        # Display fixes
        self.fix_text.config(state=tk.NORMAL)
        self.fix_text.delete(1.0, tk.END)
        
        fix_list = details.get('fix_list', [])
        if fix_list:
            for i, f in enumerate(fix_list, 1):
                status = "✓" if f.get('success', False) else "✗"
                self.fix_text.insert(tk.END, 
                    f"{i}. {status} [{f.get('strategy', 'unknown')}] {f.get('description', 'N/A')}\n\n")
        else:
            self.fix_text.insert(tk.END, "No fixes applied.\n")
        
        self.fix_text.config(state=tk.DISABLED)
        
        # Display validation
        self.validation_text.config(state=tk.NORMAL)
        self.validation_text.delete(1.0, tk.END)
        
        self.validation_text.insert(tk.END, 
            f"Overall Score: {iteration_data.get('score', 0.0):.2f}\n\n")
        self.validation_text.insert(tk.END, 
            f"Weaknesses Found: {iteration_data.get('weaknesses', 0)}\n")
        self.validation_text.insert(tk.END, 
            f"Fixes Applied: {iteration_data.get('fixes', 0)}\n")
        
        successful_fixes = sum(1 for f in fix_list if f.get('success', False))
        self.validation_text.insert(tk.END, 
            f"Successful Fixes: {successful_fixes}\n")
        
        self.validation_text.config(state=tk.DISABLED)
        
    def log_message(self, message: str, level: str = "INFO"):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)


# Standalone test
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Recursive Crucible - Test")
    root.geometry("1000x700")
    
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)
    
    crucible_tab = CrucibleTab(notebook)
    
    root.mainloop()
