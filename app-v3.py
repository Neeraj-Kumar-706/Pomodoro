# final edit 16/01/25 replace simple audio with pygame and add rain sound feature
import tkinter as tk
from ttkbootstrap import Style, ttk
from tkinter import messagebox
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque
import datetime
import json
import os
import chime
import sys
import importlib


# Add error handling utility
def safe_operation(operation, error_message="Operation failed", default_return=None):
    """Utility function for safe operation execution with error handling"""
    try:
        return operation()
    except Exception as e:
        print(f"{error_message}: {str(e)}")
        return default_return

class PomodoroTimer:
    def __init__(self):
        self.auto_switch = True  # Change default to True since settings will override it
        self.load_settings()
        self.today = datetime.date.today()
        self.sessions_completed = 0
        self.load_state()  # This will now properly override auto_switch from session state
        self.historical_data = self.load_historical_data()
        self._last_save_time = 0
        self.save_interval = 5  # Save state every 5 seconds

    def load_state(self):
        """Load today's session state"""
        try:
            with open("session_state.json", "r") as f:
                state = json.load(f)
                if state.get("date") == self.today.isoformat():
                    self.current_time = state.get("current_time", self.pomodoro_time)
                    self.pomodoro_count = state.get("pomodoro_count", 0)
                    self.total_pomodoro_time = state.get("total_time", 0)
                    self._daily_time = state.get("daily_time", 0)
                    self.mode = state.get("mode", "Pomodoro")
                    self.sessions_completed = state.get("sessions_completed", 0)  # Add this line
                    self.auto_switch = bool(state.get("auto_switch", self.auto_switch))  # Ensure boolean conversion
                else:
                    self._init_new_day()
        except FileNotFoundError:
            self._init_new_day()
        except json.JSONDecodeError as e:
            print(f"Corrupted session state file: {e}")
            self._init_new_day()
        except Exception as e:
            print(f"Error loading state: {e}")
            self._init_new_day()

    def _init_new_day(self):
        """Initialize state for a new day"""
        self.current_time = self.pomodoro_time
        self.pomodoro_count = 0
        self.total_pomodoro_time = 0
        self._daily_time = 0
        self.mode = "Pomodoro"
        self.sessions_completed = 0  # Add this line

    def save_state(self):
        if not hasattr(self, '_last_save_time'):
            self._last_save_time = 0

        current_time = time.time()
        if current_time - self._last_save_time < self.save_interval:
            return

        def _save():
            state = {
                "date": self.today.isoformat(),
                "current_time": max(0, self.current_time),  # Ensure non-negative
                "pomodoro_count": max(0, self.pomodoro_count),
                "total_time": max(0, self.total_pomodoro_time),
                "daily_time": max(0, self._daily_time),
                "mode": self.mode,
                "sessions_completed": max(0, self.sessions_completed),
                "auto_switch": bool(self.auto_switch)  # Ensure boolean
            }
            with open("session_state.json", "w") as f:
                json.dump(state, f, indent=2)
            self._last_save_time = current_time

        safe_operation(_save, "Error saving state")

    def load_settings(self):
        try:
            with open("settings.json", "r") as f:
                settings = json.load(f)
                self.pomodoro_time = settings["pomodoro"] * 60
                self.short_break_time = settings["short_break"] * 60
                self.long_break_time = settings["long_break"] * 60
                self.mega_goal = settings.get("mega_goal", 4) * 3600  # Default 4 hours
                self.auto_switch = settings.get("auto_switch", False)
                self.sound_enabled = settings.get("sound_enabled", True)  # Add sound enabled setting
                self.rain_sound_path = settings.get("rain_sound_path", "")  # Add this line
        except FileNotFoundError:
            self.pomodoro_time = 25 * 60
            self.short_break_time = 5 * 60
            self.long_break_time = 15 * 60
            self.mega_goal = 4 * 3600  # 4 hours in seconds
            self.auto_switch = False
            self.sound_enabled = True
            self.rain_sound_path = ""  # Add this line

    def get_mode_time(self):
        return {
            "Pomodoro": self.pomodoro_time,
            "Short Break": self.short_break_time,
            "Long Break": self.long_break_time,
        }.get(self.mode, self.pomodoro_time)

    def load_historical_data(self):
        try:
            with open("pomodoro_history.json", "r") as f:
                data = json.load(f)
                processed_data = []
                today = datetime.date.today().isoformat()
                
                for entry in data:
                    if len(entry) == 3:  # Format: [date, count, time]
                        d, count, time_value = entry
                        mega_goal = self.mega_goal  # Use current mega goal if not stored
                    else:  # New format: [date, count, time, mega_goal]
                        d, count, time_value, mega_goal = entry
                        
                    if d == today:
                        self._daily_time = time_value
                    
                    processed_data.append((
                        datetime.date.fromisoformat(d),
                        count,
                        time_value,
                        mega_goal
                    ))
                
                return deque(processed_data)
        except (FileNotFoundError, json.JSONDecodeError):
            return deque()
        except Exception as e:
            print(f"Error loading history: {e}")
            return deque()

    def save_historical_data(self):
        """Optimized historical data saving with error handling"""
        try:
            # Keep original mega_goals when saving history
            data = [(d.isoformat(), count, total_time, mega_goal) 
                    for d, count, total_time, mega_goal in self.historical_data]
            with open("pomodoro_history.json", "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")
            return False
        return True

    def save_settings(self):
        settings = {
            "pomodoro": self.pomodoro_time // 60,
            "short_break": self.short_break_time // 60,
            "long_break": self.long_break_time // 60,
            "mega_goal": self.mega_goal // 3600,
            "auto_switch": self.auto_switch,
            "sound_enabled": self.sound_enabled,
            "rain_sound_path": self.rain_sound_path  # Add this line
        }
        with open("settings.json", "w") as f:
            json.dump(settings, f)

    def update_daily_time(self, seconds):
        """Atomic update of daily time"""
        if seconds <= 0:
            return False
        try:
            self._daily_time += seconds
            return self.save_historical_data()
        except Exception:
            return False


class PomodoroTimerGUI:
    def __init__(self, master):
        self.master = master
        self.timer = PomodoroTimer()
        self.auto_switch_var = tk.BooleanVar(value=self.timer.auto_switch)  # Set initial value here
        self.setup_gui()
        self.setup_audio()
        self.initialize_state()

    def setup_audio(self):
        """Initialize audio-related attributes"""
        self.rain_sound = self.timer.rain_sound_path  # Use path from settings
        self.is_playing = False
        self.is_user_playsound = False
        self.pygame_initialized = False
        self.pygame = None
        chime.theme("big-sur")

    def _load_pygame(self):
        """Lazy load pygame module"""
        if not self.pygame_initialized:
            try:
                # Suppress pygame startup message
                original_stdout = sys.stdout
                sys.stdout = open(os.devnull, "w")
                
                # Lazy import pygame
                self.pygame = importlib.import_module('pygame')
                self.pygame.mixer.init()
                
                sys.stdout = original_stdout
                self.pygame_initialized = True
                return True
            except Exception as e:
                sys.stdout = original_stdout
                print(f"Failed to initialize sound system: {e}")
                messagebox.showerror("Sound Error", "Failed to initialize sound system")
                return False
        return True

    def initialize_state(self):
        """Initialize timer state"""
        self.timer_thread = None
        self.is_running = False
        self.is_paused = False
        self.should_stop = threading.Event()
        self._display_update_pending = False
        self._last_display_update = 0
        self.display_update_interval = 0.5
        
        self.check_date()
        self.update_initial_display()
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def update_initial_display(self):
        """Update all displays with saved session data on app startup"""
        # Update pomodoro count label
        self.pomodoro_count_label.config(text=f"Pomodoros: {self.timer.pomodoro_count}")
        
        # Update total time label
        formatted_time = time.strftime("%H:%M:%S", time.gmtime(self.timer.total_pomodoro_time))
        self.total_time_label.config(text=f"Total Time: {formatted_time}")
        
        # Update mode
        self.mode_var.set(self.timer.mode)
        
        # Update session displays
        total_sessions = int((self.timer.mega_goal / 3600) * 2)
        sessions_done = self.timer.sessions_completed
        
        # Update session label and progress
        self.session_label.config(
            text=f"Sessions: {sessions_done}/{total_sessions}",
            foreground="lime" if sessions_done >= total_sessions else "white"
        )
        self.session_progress["value"] = min(100, (sessions_done / total_sessions) * 100)
        
        # Update progress dots
        for i, dot in enumerate(self.progress_dots):
            if i < total_sessions:
                dot.configure(
                    foreground="lime" if i < sessions_done else "gray",
                    text="●"
                )
            else:
                dot.configure(text=" ")

        # Update auto switch state from session state
        self.auto_switch_var.set(self.timer.auto_switch)

    def setup_gui(self):

        self.master.title("Pomodoro Timer")
        self.master.geometry("300x600")  # Increased height from 550 to 600
        self.master.resizable(False, False)
        self.style = Style(theme="darkly")

        self.timer_label = ttk.Label(
            self.master,
            text=self.format_time(self.timer.current_time),
            font=("Helvetica", 48),
        )
        self.timer_label.pack(pady=20)

        self.start_button = ttk.Button(
            self.master, text="Start", command=self.toggle_timer
        )
        self.start_button.pack(pady=10)

        self.reset_button = ttk.Button(
            self.master, text="Reset", command=self.reset_timer
        )
        self.reset_button.pack(pady=10)

        self.mode_var = tk.StringVar(value=self.timer.mode)  # Change this line to use saved mode
        self.mode_menu = ttk.OptionMenu(
            self.master,
            self.mode_var,
            "Pomodoro",
            "Pomodoro",
            "Short Break",
            "Long Break",
            command=self.change_mode,
        )
        self.mode_menu.pack(pady=10)

        self.progress_bar = ttk.Progressbar(
            self.master, orient="horizontal", length=200, mode="determinate"
        )
        self.progress_bar.pack(pady=20)

        self.pomodoro_count_label = ttk.Label(self.master, text="Pomodoros: 0")
        self.pomodoro_count_label.pack(pady=10)

        self.total_time_label = ttk.Label(self.master, text="Total Time: 00:00:00")
        self.total_time_label.pack(pady=10)

        button_frame = ttk.Frame(self.master)
        button_frame.pack(pady=10)

        self.settings_button = ttk.Button(
            button_frame, text="Settings", command=self.open_settings
        )
        self.settings_button.pack(side=tk.LEFT, padx=5)

        self.history_button = ttk.Button(
            button_frame, text="History", command=self.open_history
        )
        self.history_button.pack(side=tk.LEFT, padx=5)
        # edit on 15/01/25 add rain sound button

        # Add sound button to button_frame instead of packing separately
        self.play_sound_button = ttk.Button(
            button_frame,  # Changed from self.master to button_frame
            text="Play Sound",
            command=self.toggle_rain_sound,
            style="primary.TButton",
        )
        self.play_sound_button.pack(side=tk.LEFT, padx=5)  # Pack in button frame with other buttons

        # Replace Mega Goal frame with Session Progress frame
        session_frame = ttk.LabelFrame(self.master, text="Daily Sessions", padding=10)
        session_frame.pack(pady=10, padx=5, fill="x")

        # Session progress bar
        self.session_progress = ttk.Progressbar(
            session_frame, 
            orient="horizontal",
            length=200,
            mode="determinate",
            style="info.Horizontal.TProgressbar"
        )
        self.session_progress.pack(pady=5)

        # Session counter and dots
        self.session_label = ttk.Label(
            session_frame,
            text="Sessions: 0/16",  # Default for 8-hour goal
            font=("Helvetica", 10)
        )
        self.session_label.pack(pady=2)

        # Add progress dots frame
        dots_frame = ttk.Frame(session_frame)
        dots_frame.pack(pady=2)
        
        # Create progress dots
        self.progress_dots = []
        max_dots_per_row = 8
        for i in range(16):
            if i % max_dots_per_row == 0:
                row_frame = ttk.Frame(dots_frame)
                row_frame.pack()
            
            dot = ttk.Label(
                row_frame,
                text="●",
                font=("Helvetica", 8),
                foreground="gray"
            )
            dot.pack(side="left", padx=1)
            self.progress_dots.append(dot)

    def toggle_rain_sound(self):
        if self.is_playing:
            self.is_user_playsound = False
            self.stop_rain_sound()
        else:
            self.is_user_playsound = True
            self.play_rain_sound()

    def play_rain_sound(self):
        try:
            if not self.rain_sound:
                messagebox.showwarning("Sound Disabled", "Rain sound feature is disabled. No sound file was provided during installation.")
                return

            if not os.path.exists(self.rain_sound):
                messagebox.showerror("File Error", "Rain sound file not found")
                return

            if not self._load_pygame():
                return

            self.pygame.mixer.music.load(self.rain_sound)
            self.pygame.mixer.music.play(-1)
            self.is_playing = True
            self.play_sound_button.config(text="Stop Sound", style="danger.TButton")
        except Exception as e:
            print(f"Error playing sound: {e}")
            messagebox.showerror("Sound Error", "Failed to play sound")
            self.is_playing = False

    def stop_rain_sound(self):
        """Stop the rain sound playback"""
        if self.pygame_initialized and self.is_playing:
            try:
                self.pygame.mixer.music.stop()
                self.is_playing = False
                self.play_sound_button.config(text="Play Sound", style="primary.TButton")
            except Exception as e:
                print(f"Error stopping sound: {e}")

    def change_volume(self, value):
        if self.pygame_initialized:
            volume = float(value) / 100
            self.timer.sound_volume = volume
            self.pygame.mixer.music.set_volume(volume)
            self.timer.save_settings()

    def toggle_timer(self):
        if self.is_running:
            if self.is_paused:
                self.is_paused = False
                chime.info()
                self.start_button.config(text="Pause")
            else:
                self.is_paused = True
                chime.info()
                self.start_button.config(text="Resume")
        else:
            # Reset timer if it's at 0
            if self.timer.current_time <= 0:
                self.timer.current_time = self.timer.get_mode_time()
                self.update_display()
            
            self.is_running = True
            self.is_paused = False
            self.should_stop.clear()  # Clear stop flag
            chime.info()
            self.start_button.config(text="Pause")
            self.timer_thread = threading.Thread(target=self.run_timer)
            self.timer_thread.start()
        self.timer.save_state()

    def run_timer(self):
        """Fixed timer with consistent speed and proper time tracking"""
        target_interval = 1.0
        last_tick = time.time()
        
        while not self.should_stop.is_set() and self.timer.current_time > 0:  # Changed back to > 0
            current_time = time.time()
            
            if self.is_paused:
                last_tick = current_time
                time.sleep(0.1)
                continue
            
            elapsed = current_time - last_tick
            if elapsed >= target_interval:
                # Update timer first
                self.timer.current_time = max(0, self.timer.current_time - 1)
                self.master.after(0, self.update_display)
                
                # Handle Pomodoro mode updates
                if self.timer.mode == "Pomodoro":
                    self.timer.total_pomodoro_time += 1
                    self.master.after(0, self.update_total_time_label)
                    
                    # Check for session completion
                    if self.timer.total_pomodoro_time % 1800 == 0:
                        self.timer.sessions_completed += 1
                        self.master.after(0, self.update_session_display)
                
                # Check completion after updates
                if self.timer.current_time == 0:  # Changed to exact equality
                    self.master.after(0, self._handle_completion)
                    break
                
                last_tick = current_time
            
            sleep_time = max(0.01, min(0.1, target_interval - (time.time() - current_time)))
            time.sleep(sleep_time)

    def _handle_completion(self):
        """Internal method to handle timer completion with proper order"""
        if not self.master.winfo_exists():
            return
            
        # Stop timer immediately
        self.is_running = False
        self.should_stop.set()
        
        # Save current state
        was_playing = self.is_playing
        current_mode = self.timer.mode
        
        # Handle sound
        if self.is_playing:
            self.stop_rain_sound()
        chime.success()
        
        # Update pomodoro count first if needed
        if current_mode == "Pomodoro":
            self.update_pomodoro_completion()
        
        # Show message if not auto-switching
        if not self.timer.auto_switch:
            self.show_completion_message()
        
        # Switch mode last
        next_mode = self.get_next_mode()
        def switch_with_state():
            if self.master.winfo_exists():
                self.switch_mode(next_mode)
                if was_playing or self.is_user_playsound:
                    self.play_rain_sound()
        
        self.master.after(500, switch_with_state)
        self.timer.save_state()

    def timer_completed(self):
        """Streamlined timer completion handler"""
        if not self.master.winfo_exists():
            return
            
        self.is_running = False
        was_playing = self.is_playing
        
        # Stop sound and play completion chime
        if self.is_playing:
            self.stop_rain_sound()
        chime.success()
        
        # Show completion message before mode switch if not auto-switching
        if not self.timer.auto_switch:
            self.show_completion_message()
            
        # Get next mode
        next_mode = self.get_next_mode()
        
        # Update pomodoro count if needed
        if self.timer.mode == "Pomodoro":
            self.update_pomodoro_completion()
        
        # Switch mode after a short delay
        def switch_with_state():
            if self.master.winfo_exists():  # Check if window still exists
                self.switch_mode(next_mode)
                if was_playing or self.is_user_playsound:
                    self.play_rain_sound()
        
        self.master.after(500, switch_with_state)
        self.timer.save_state()

    def get_next_mode(self):
        """Determine next timer mode"""
        if self.timer.mode == "Pomodoro":
            return "Long Break" if self.timer.pomodoro_count % 4 == 0 else "Short Break"
        return "Pomodoro"

    def show_completion_message(self):
        """Show appropriate completion message"""
        if self.timer.mode == "Pomodoro":
            messagebox.showinfo("Pomodoro Complete", "Well done! Time for a break!")
        else:
            messagebox.showinfo("Break Complete", "Break finished! Time to work!")

    def update_pomodoro_completion(self):
        """Update pomodoro completion state"""
        self.timer.pomodoro_count += 1
        self.pomodoro_count_label.config(text=f"Pomodoros: {self.timer.pomodoro_count}")
        self.update_historical_data()
        self.timer.save_state()

    def update_session_display(self):
        """Update session display independently"""
        sessions_done = self.timer.sessions_completed
        total_sessions = int((self.timer.mega_goal / 3600) * 2)  # 2 sessions per hour
        
        # Update session counter and progress bar
        self.session_label.config(
            text=f"Sessions: {sessions_done}/{total_sessions}",
            foreground="lime" if sessions_done >= total_sessions else "white"
        )
        self.session_progress["value"] = min(100, (sessions_done / total_sessions) * 100)
        
        # Update progress dots
        for i, dot in enumerate(self.progress_dots):
            if i < total_sessions:
                dot.configure(
                    foreground="lime" if i < sessions_done else "gray",
                    text="●"
                )
            else:
                dot.configure(text=" ")

    def switch_mode(self, new_mode):
        """Enhanced mode switching with proper state management"""
        # Stop current timer thread
        self.is_running = False
        self.should_stop.set()
        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.join(timeout=1)
        
        # Update mode and reset state
        self.timer.mode = new_mode
        self.mode_var.set(new_mode)
        self.timer.current_time = self.timer.get_mode_time()
        self.should_stop.clear()
        
        # Update display before starting new timer
        self.update_display()
        
        # Start new timer thread
        self.is_running = True
        self.is_paused = False
        self.start_button.config(text="Pause")
        self.timer_thread = threading.Thread(target=self.run_timer)
        self.timer_thread.start()

    def reset_timer(self):
        """Enhanced reset with proper thread cleanup and immediate display update"""
        # Store the current total time and session state before reset
        current_total = self.timer.total_pomodoro_time
        current_sessions = self.timer.sessions_completed
        
        self.is_running = False
        self.is_paused = False
        self.should_stop.set()
        chime.warning()
        
        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.join(timeout=1)
            
        self.should_stop.clear()
        self.timer.current_time = self.timer.get_mode_time()
        self.start_button.config(text="Start")
        
        # Restore the total time and session state
        self.timer.total_pomodoro_time = current_total
        self.timer.sessions_completed = current_sessions
        
        # Force immediate display update
        self.timer_label.config(text=self.format_time(self.timer.current_time))
        self.progress_bar["value"] = 0
        self.update_display()
        self.timer.save_state()

    def change_mode(self, *args):
        chime.warning()  # Audio feedback for mode change
        self.timer.mode = self.mode_var.get()
        self.reset_timer()

    def update_display(self):
        """Modified update_display with improved session tracking"""
        if self._display_update_pending:
            return
        
        current_time = time.time()
        if current_time - self._last_display_update < self.display_update_interval:
            return

        self._display_update_pending = True
        try:
            # Cache frequently used values
            current_time = self.timer.current_time
            mode_time = self.timer.get_mode_time()
            
            # Update main display
            self.timer_label.config(text=self.format_time(current_time))
            current_progress = (1 - current_time / mode_time) * 100
            self.progress_bar["value"] = current_progress

            # Update total time display if in Pomodoro mode
            if self.timer.mode == "Pomodoro":
                if not hasattr(self, '_last_total_time') or self._last_total_time != self.timer.total_pomodoro_time:
                    self._last_total_time = self.timer.total_pomodoro_time
                    self.update_total_time_label()
                    
                    # Check for session completion
                    if self.timer.total_pomodoro_time > 0 and self.timer.total_pomodoro_time % 1800 == 0:
                        self.update_session_display()

            self._last_display_update = current_time
            
        finally:
            self._display_update_pending = False

    def update_progress_bars(self):
        # Update session progress
        session_progress = (1 - self.timer.current_time / self.timer.get_mode_time()) * 100
        self.session_progress["value"] = session_progress

        # Update mega goal progress
        daily_time = 0
        today = datetime.date.today()
        if self.timer.historical_data and self.timer.historical_data[-1][0] == today:
            daily_time = self.timer.historical_data[-1][2]
        if self.timer.mode == "Pomodoro":
            daily_time += self.timer.total_pomodoro_time
        mega_progress = min(100, (daily_time / self.timer.mega_goal) * 100)
        self.mega_goal_progress["value"] = mega_progress

    def update_historical_data(self):
        today = datetime.date.today()
        try:
            if self.timer.historical_data and self.timer.historical_data[-1][0] == today:
                _, prev_count, prev_time, prev_goal = self.timer.historical_data[-1]
                self.timer.historical_data[-1] = (
                    today,
                    prev_count + 1,
                    prev_time + self.timer.pomodoro_time,
                    self.timer.mega_goal
                )
            else:
                self.timer.historical_data.append(
                    (today, 1, self.timer.pomodoro_time, self.timer.mega_goal)
                )
                year_ago = today - datetime.timedelta(days=365)
                while (self.timer.historical_data and 
                       self.timer.historical_data[0][0] < year_ago):
                    self.timer.historical_data.popleft()
            
            self.timer.update_daily_time(self.timer.pomodoro_time)
        except Exception as e:
            print(f"Error updating history: {e}")
            messagebox.showerror("Error", "Failed to update history")

    def open_settings(self):
        chime.info()
        settings_window = tk.Toplevel(self.master)
        settings_window.title("Settings")
        settings_window.geometry("400x600")

        settings_frame = ttk.Frame(settings_window, padding="20")
        settings_frame.pack(fill="both", expand=True)

        ttk.Label(settings_frame, text="Pomodoro Duration (minutes):").pack(pady=5)
        pomodoro_entry = ttk.Entry(settings_frame)
        pomodoro_entry.insert(0, str(self.timer.pomodoro_time // 60))
        pomodoro_entry.pack(pady=5)

        ttk.Label(settings_frame, text="Short Break Duration (minutes):").pack(pady=5)
        short_break_entry = ttk.Entry(settings_frame)
        short_break_entry.insert(0, str(self.timer.short_break_time // 60))
        short_break_entry.pack(pady=5)

        ttk.Label(settings_frame, text="Long Break Duration (minutes):").pack(pady=5)
        long_break_entry = ttk.Entry(settings_frame)
        long_break_entry.insert(0, str(self.timer.long_break_time // 60))
        long_break_entry.pack(pady=5)

        ttk.Label(settings_frame, text="Daily Mega Goal (hours):").pack(pady=5)
        mega_goal_entry = ttk.Entry(settings_frame)
        mega_goal_entry.insert(0, str(self.timer.mega_goal // 3600))
        mega_goal_entry.pack(pady=5)

        ttk.Label(settings_frame, text="Auto Switch Modes:").pack(pady=5)
        auto_switch_var = tk.BooleanVar(value=self.timer.auto_switch)
        ttk.Checkbutton(
            settings_frame,
            variable=auto_switch_var,
            text="Enable automatic mode switching"
        ).pack(pady=5)

        # Add rain sound path setting - remove browse button, just keep entry
        ttk.Label(settings_frame, text="Rain Sound File Path:").pack(pady=5)
        rain_sound_path_entry = ttk.Entry(settings_frame, width=50)
        rain_sound_path_entry.insert(0, self.timer.rain_sound_path)
        rain_sound_path_entry.pack(pady=5)

        button_frame = ttk.Frame(settings_frame)
        button_frame.pack(pady=20, fill="x")

        ttk.Button(
            button_frame,
            text="Cancel",
            style="secondary.TButton",
            command=settings_window.destroy
        ).pack(side="left", padx=5, expand=True)

        ttk.Button(
            button_frame,
            text="Apply",
            style="info.TButton",
            command=lambda: save_settings(False)
        ).pack(side="left", padx=5, expand=True)

        ttk.Button(
            button_frame,
            text="Save",
            style="primary.TButton",
            command=lambda: save_settings(True)
        ).pack(side="right", padx=5, expand=True)

        def save_settings(close_window=True):
            try:
                self.timer.pomodoro_time = int(pomodoro_entry.get()) * 60
                self.timer.short_break_time = int(short_break_entry.get()) * 60
                self.timer.long_break_time = int(long_break_entry.get()) * 60
                
                old_mega_goal = self.timer.mega_goal
                new_mega_goal = int(mega_goal_entry.get()) * 3600
                if new_mega_goal != self.timer.mega_goal:
                    today = datetime.date.today()
                    if self.timer.historical_data:
                        last_entry = self.timer.historical_data[-1]
                        if last_entry[0] == today:
                            self.timer.historical_data[-1] = (
                                today,
                                last_entry[1],
                                last_entry[2],
                                new_mega_goal
                            )
                        else:
                            self.timer.historical_data.append((today, 0, 0, new_mega_goal))
                    else:
                        self.timer.historical_data.append((today, 0, 0, new_mega_goal))
                    self.timer.mega_goal = new_mega_goal
                    self.timer.save_historical_data()
                
                self.timer.auto_switch = auto_switch_var.get()
                # Update our GUI's variable to match
                self.auto_switch_var.set(self.timer.auto_switch)
                
                # Update rain sound path and test it
                new_path = rain_sound_path_entry.get().strip()
                if new_path and not os.path.exists(new_path):
                    messagebox.showwarning("Warning", "Rain sound file not found. Path will be saved but sound won't work.")
                
                # Save the path even if file doesn't exist - user might fix it later
                self.timer.rain_sound_path = new_path
                self.rain_sound = new_path  # Update current instance path
                
                self.timer.save_settings()
                self.reset_timer()
                
                if close_window:
                    settings_window.destroy()
                    
            except ValueError:
                chime.error()
                messagebox.showerror(
                    "Invalid Input",
                    "Please enter valid numbers for all durations."
                )

    def update_total_time_label(self):
        """Enhanced total time label update"""
        if not self.master.winfo_exists():
            return

        try:
            total_seconds = self.timer.total_pomodoro_time
            formatted_time = time.strftime("%H:%M:%S", time.gmtime(total_seconds))
            self.total_time_label.config(text=f"Total Time: {formatted_time}")
            self.timer.save_state()
        except tk.TclError:
            pass

    def open_history(self):
        chime.info()  # Audio feedback for opening history
        if not self.timer.historical_data:
            chime.warning()  # Audio feedback for no history
            messagebox.showinfo("History", "No history data available")
            return

        history_window = tk.Toplevel(self.master)
        history_window.title("Pomodoro History")
        history_window.geometry("800x800")

        plt.style.use("dark_background")
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        fig.patch.set_facecolor("#2b2b2b")

        data = list(self.timer.historical_data)[-30:]
        dates = [item[0] for item in data]
        counts = [item[1] for item in data]
        total_times = [item[2] / 3600 for item in data]
        mega_goals = [item[3] / 3600 for item in data]

        ax1.plot(dates, counts, color="#1e90ff", marker='o', label="Daily Pomodoros", linewidth=2)
        ax1.set_ylabel("Pomodoros", color="#1e90ff")
        ax1.grid(True, alpha=0.3)
        
        ax2.plot(dates, total_times, color="lime", marker='s', label="Hours Worked", linewidth=2)
        ax2.plot(dates, mega_goals, color='red', linestyle='--', label='Daily Goals')
        ax2.set_ylabel("Hours", color="lime")
        ax2.grid(True, alpha=0.3)

        for ax in [ax1, ax2]:
            ax.set_facecolor("#2b2b2b")
            ax.tick_params(colors='white')
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            ax.legend(loc='upper left')

        stats_text = (f"Total Pomodoros: {sum(counts)}\n"
                      f"Total Hours: {sum(total_times):.1f}\n"
                      f"Daily Average: {sum(total_times)/len(dates):.1f} hours")

        fig.text(0.05, 0.02, stats_text,
                color='white',
                fontsize=10,
                bbox=dict(facecolor='#2b2b2b',
                         edgecolor='white',
                         alpha=0.7,
                         pad=10))

        plt.tight_layout(rect=[0, 0.1, 1, 0.95])
        canvas = FigureCanvasTkAgg(fig, master=history_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    @staticmethod
    def format_time(seconds):
        try:
            seconds = max(0, int(seconds))
            if seconds < 3600:
                return time.strftime("%M:%S", time.gmtime(seconds))
            return time.strftime("%H:%M:%S", time.gmtime(seconds))
        except Exception:
            return "00:00"

    def on_closing(self):
        """Enhanced cleanup on application exit"""
        try:
            self.timer.save_state()
            self.is_running = False
            self.should_stop.set()
            
            if self.is_playing:
                self.stop_rain_sound()
            
            if self.timer_thread and self.timer_thread.is_alive():
                self.timer_thread.join(timeout=1)
            
            if self.pygame_initialized:
                try:
                    self.pygame.mixer.quit()
                except:
                    pass
            
            if self.master.winfo_exists():
                self.master.quit()
                self.master.destroy()
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            os._exit(0)

    def toggle_sound_enabled(self):
        self.timer.sound_enabled = self.sound_enabled_var.get()
        state = "normal" if self.timer.sound_enabled else "disabled"
        self.volume_scale.configure(state=state)
        self.play_sound_button.configure(state=state)
        if not self.timer.sound_enabled and self.is_playing:
            self.stop_rain_sound()
        self.timer.save_settings()

    def check_date(self):
        """Check if it's a new day and reset if needed"""
        today = datetime.date.today()
        if today != self.timer.today:
            self.timer.today = today
            self.timer._init_new_day()
            self.update_display()


# Add this at the bottom of the file, after all classes
def main():
    root = tk.Tk()
    try:
        icon_image = tk.PhotoImage(file="assets/time-organization.png")
        root.iconphoto(False, icon_image)
    except:
        pass  # Skip if icon not found
    
    app = PomodoroTimerGUI(root)
    try:
        root.mainloop()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        os._exit(0)

if __name__ == "__main__":
    main()