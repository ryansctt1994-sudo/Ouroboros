#!/usr/bin/env python3
"""
EDEN Chat - GTK4 Native Chat Interface
======================================

Metro-style GTK4/Libadwaita chat window that connects to the EDEN daemon
via Unix socket IPC.

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

import sys
import threading
from pathlib import Path

# Add current directory to path
SCRIPT_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(SCRIPT_DIR))

try:
    import gi
    gi.require_version('Gtk', '4.0')
    gi.require_version('Adw', '1')
    from gi.repository import Gtk, Adw, GLib
    GTK_AVAILABLE = True
except (ImportError, ValueError) as e:
    GTK_AVAILABLE = False
    print(f"Error: GTK4/Libadwaita not available: {e}", file=sys.stderr)
    print("Please install: sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adwaita-1", file=sys.stderr)

from eden_ipc import SOCKET_PATH
from eden_cli import send_request


class EdenChatWindow(Adw.ApplicationWindow):
    """Main chat window."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Window properties
        self.set_default_size(800, 600)
        self.set_title("EDEN Chat")
        
        # Create main layout
        self.setup_ui()
        
        # Check daemon status on startup
        GLib.idle_add(self.check_daemon_status)
    
    def setup_ui(self):
        """Setup the UI layout."""
        # Main box (vertical)
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(main_box)
        
        # Header bar
        header = Adw.HeaderBar()
        
        # Sidebar toggle button
        self.sidebar_toggle = Gtk.ToggleButton()
        self.sidebar_toggle.set_icon_name("view-sidebar-start-symbolic")
        self.sidebar_toggle.connect("toggled", self.on_sidebar_toggle)
        header.pack_start(self.sidebar_toggle)
        
        main_box.append(header)
        
        # Split view for sidebar and main area
        self.split_view = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        main_box.append(self.split_view)
        
        # Sidebar (initially hidden)
        self.sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.sidebar.set_size_request(250, -1)
        self.sidebar.add_css_class("sidebar")
        
        sidebar_label = Gtk.Label(label="Settings")
        sidebar_label.set_margin_top(20)
        sidebar_label.set_margin_bottom(20)
        sidebar_label.add_css_class("title-2")
        self.sidebar.append(sidebar_label)
        
        info_label = Gtk.Label(label="EDEN AI Assistant\nv1.0.0")
        info_label.set_margin_top(10)
        info_label.set_margin_bottom(10)
        self.sidebar.append(info_label)
        
        # Initially hide sidebar
        self.sidebar.set_visible(False)
        self.split_view.set_start_child(self.sidebar)
        
        # Main chat area
        chat_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.split_view.set_end_child(chat_box)
        self.split_view.set_resize_start_child(False)
        self.split_view.set_shrink_start_child(False)
        
        # Chat history (scrollable)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        chat_box.append(scrolled)
        
        self.chat_view = Gtk.TextView()
        self.chat_view.set_editable(False)
        self.chat_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.chat_view.set_margin_start(10)
        self.chat_view.set_margin_end(10)
        self.chat_view.set_margin_top(10)
        self.chat_view.set_margin_bottom(10)
        scrolled.set_child(self.chat_view)
        
        self.chat_buffer = self.chat_view.get_buffer()
        
        # Entry bar at bottom
        entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        entry_box.set_margin_start(10)
        entry_box.set_margin_end(10)
        entry_box.set_margin_top(6)
        entry_box.set_margin_bottom(10)
        chat_box.append(entry_box)
        
        self.entry = Gtk.Entry()
        self.entry.set_hexpand(True)
        self.entry.set_placeholder_text("Type your message...")
        self.entry.connect("activate", self.on_send_clicked)
        entry_box.append(self.entry)
        
        send_button = Gtk.Button(label="Send")
        send_button.add_css_class("suggested-action")
        send_button.connect("clicked", self.on_send_clicked)
        entry_box.append(send_button)
        
        # Scrolled window reference for auto-scroll
        self.scrolled_window = scrolled
    
    def on_sidebar_toggle(self, toggle_button):
        """Toggle sidebar visibility."""
        visible = toggle_button.get_active()
        self.sidebar.set_visible(visible)
    
    def check_daemon_status(self):
        """Check if daemon is running."""
        import os
        if not os.path.exists(SOCKET_PATH):
            self.append_message("System", 
                "⚠️ EDEN daemon is not running.\n"
                "Please start it with: python3 os/eden_daemon.py\n")
        else:
            self.append_message("System", 
                "✓ Connected to EDEN daemon.\n"
                "You can start chatting!\n")
        return False  # Don't repeat
    
    def append_message(self, sender: str, text: str):
        """Append a message to the chat view."""
        end_iter = self.chat_buffer.get_end_iter()
        self.chat_buffer.insert(end_iter, f"{sender}: {text}\n\n")
        
        # Auto-scroll to bottom
        GLib.idle_add(self.scroll_to_bottom)
    
    def scroll_to_bottom(self):
        """Scroll chat view to bottom."""
        adj = self.scrolled_window.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())
        return False
    
    def on_send_clicked(self, widget):
        """Handle send button click."""
        message = self.entry.get_text().strip()
        if not message:
            return
        
        # Clear entry
        self.entry.set_text("")
        
        # Show user message
        self.append_message("You", message)
        
        # Disable entry while processing
        self.entry.set_sensitive(False)
        
        # Send to daemon in background thread
        thread = threading.Thread(
            target=self.send_message_to_daemon,
            args=(message,),
            daemon=True
        )
        thread.start()
    
    def send_message_to_daemon(self, message: str):
        """Send message to daemon via IPC (runs in background thread)."""
        try:
            result = send_request("chat", {"message": message})
            response = result.get("response", "No response")
            
            # Update UI in main thread
            GLib.idle_add(self.on_response_received, response, None)
        
        except ConnectionError as e:
            error_msg = str(e)
            GLib.idle_add(self.on_response_received, None, error_msg)
        
        except Exception as e:
            error_msg = f"Error: {e}"
            GLib.idle_add(self.on_response_received, None, error_msg)
    
    def on_response_received(self, response: str = None, error: str = None):
        """Handle response from daemon (runs in main thread)."""
        if error:
            self.append_message("Error", error)
        elif response:
            self.append_message("EDEN", response)
        
        # Re-enable entry
        self.entry.set_sensitive(True)
        self.entry.grab_focus()
        
        return False  # Don't repeat


class EdenChatApp(Adw.Application):
    """GTK Application."""
    
    def __init__(self):
        super().__init__(application_id="org.ouroboros.eden.chat")
    
    def do_activate(self):
        """Activate the application."""
        win = EdenChatWindow(application=self)
        win.present()


def main():
    """Main entry point."""
    if not GTK_AVAILABLE:
        return 1
    
    app = EdenChatApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
