# final edit 16/01/25 replace simple audio with pygame and add rain sound feature
import tkinter as tk
from ttkbootstrap import Style, ttk
from tkinter import messagebox
import threading
import time
import pygame
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque
import datetime
import json
import os
import chime
import sys


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
        self.load_settings()
        self.today = datetime.date.today()
        self.sessions_completed = 0  # Add this line
        self.load_state()  # Load today's state first
        self.historical_data = self.load_historical_data()
        self.auto_switch = False
        self._cached_daily_time = 0  # Add caching
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
                    self.auto_switch = state.get("auto_switch", self.auto_switch)  # Add this line
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
        except FileNotFoundError:
            self.pomodoro_time = 25 * 60
            self.short_break_time = 5 * 60
            self.long_break_time = 15 * 60
            self.mega_goal = 4 * 3600  # 4 hours in seconds
            self.auto_switch = False
            self.sound_enabled = True

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
        self.auto_switch_var = tk.BooleanVar()  # Remove initial value
        self.setup_gui()

        self.rain_sound = os.path.join(
            os.path.dirname(__file__), "assets/rain_sound.mp3"
        )
        
        self.timer_thread = None
        self.is_running = False
        self.is_paused = False
        self.should_stop = threading.Event()
        self.is_playing = False
        self.is_user_playsound = False
        self.play_obj = None
        self.play_thread = None
        self.stop_playback = threading.Event()
        self.pygame_initialized = False  # Add pygame initialization flag
        chime.theme("big-sur")
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.check_date()  # Add date check on startup
        self.update_initial_display()  # Add this line to update display on startup
        self._display_update_pending = False
        self._last_display_update = 0
        self.display_update_interval = 0.5  # Update display every 0.5 seconds

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
        def _init_pygame():
            if not self.pygame_initialized:
                try:
                    original_stdout = sys.stdout
                    sys.stdout = open(os.devnull, "w")
                    pygame.mixer.init()
                    sys.stdout = original_stdout
                    self.pygame_initialized = True
                    return True
                except Exception as e:
                    print(f"Failed to initialize sound system: {e}")
                    messagebox.showerror("Sound Error", "Failed to initialize sound system")
                    return False
            return True

        try:
            if not os.path.exists(self.rain_sound):
                messagebox.showerror("File Error", "Rain sound file not found")
                return

            if not _init_pygame():
                return

            pygame.mixer.music.load(self.rain_sound)
            pygame.mixer.music.play(-1)
            self.is_playing = True
            self.play_sound_button.config(text="Stop Sound", style="danger.TButton")
        except Exception as e:
            print(f"Error playing sound: {e}")
            messagebox.showerror("Sound Error", "Failed to play sound")
            self.is_playing = False

    def change_volume(self, value):
        volume = float(value) / 100
        self.timer.sound_volume = volume
        pygame.mixer.music.set_volume(volume)
        self.timer.save_settings()

    # replace below method with new
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
            self.is_running = True
            self.is_paused = False
            chime.info()
            self.start_button.config(text="Pause")
            self.timer_thread = threading.Thread(target=self.run_timer)

            self.timer_thread.start()
        self.timer.save_state()  # Save state after timer changes

    def run_timer(self):
        """Optimized timer with better error handling"""
        accumulated_time = 0
        last_update = time.time()
        
        try:
            while not self.should_stop.is_set() and self.timer.current_time > 0:
                if not self.is_paused:
                    try:
                        current = time.time()
                        elapsed = current - last_update
                        accumulated_time += elapsed
                        
                        if accumulated_time >= 1.0:
                            seconds_to_subtract = int(accumulated_time)
                            self.timer.current_time = max(0, self.timer.current_time - seconds_to_subtract)
                            if self.timer.mode == "Pomodoro":
                                self.timer.total_pomodoro_time += seconds_to_subtract
                            accumulated_time -= seconds_to_subtract
                            safe_operation(
                                lambda: self.master.after(0, self.update_display),
                                "Failed to update display"
                            )
                        
                        last_update = current
                    except Exception as e:
                        print(f"Timer iteration error: {e}")
                        time.sleep(0.1)  # Prevent rapid error loops
                time.sleep(0.05)

        except Exception as e:
            print(f"Critical timer error: {e}")
            messagebox.showerror("Error", "Timer encountered an error and had to stop")
        finally:
            if not self.should_stop.is_set():
                safe_operation(
                    lambda: self.master.after(0, self.timer_completed),
                    "Failed to complete timer normally"
                )

    def reset_timer(self):
        self.is_running = False
        self.is_paused = False
        self.should_stop.set()
        chime.success()
        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.join(timeout=1)
        self.should_stop.clear()
        self.timer.current_time = self.timer.get_mode_time()
        self.start_button.config(text="Start")
        self.update_display()

    def change_mode(self, *args):
        chime.warning()
        self.timer.mode = self.mode_var.get()
        self.reset_timer()

    def update_display(self):
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

            # Update session progress only if in Pomodoro mode
            if self.timer.mode == "Pomodoro":
                daily_time = self.timer._daily_time + self.timer.total_pomodoro_time
                sessions_done = self.timer.sessions_completed  # Use saved sessions instead of calculating
                total_sessions = int((self.timer.mega_goal / 3600) * 2)
                
                # Update session counter and progress bar
                self.session_label.config(
                    text=f"Sessions: {sessions_done}/{total_sessions}",
                    foreground="lime" if sessions_done >= total_sessions else "white"
                )
                self.session_progress["value"] = min(100, (sessions_done / total_sessions) * 100)
                
                # Update progress dots with saved session state
                for i, dot in enumerate(self.progress_dots):
                    if i < total_sessions:
                        dot.configure(
                            foreground="lime" if i < sessions_done else "gray",
                            text="●"
                        )
                    else:
                        dot.configure(text=" ")

                # Check for goal completion
                if not hasattr(self, '_goal_reached') and daily_time >= self.timer.mega_goal:
                    self._goal_reached = True
                    messagebox.showinfo("Congratulations!", "You've reached your daily mega goal! 🎉")
            
            # Update total time label
            self.update_total_time_label()

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

    def timer_completed(self):
        if self.timer.mode == "Pomodoro":
            self.timer.pomodoro_count += 1
            # Increment sessions_completed when a Pomodoro is finished
            if self.timer.total_pomodoro_time >= 1800:  # 30 minutes (one session)
                self.timer.sessions_completed += 1
                self.timer.total_pomodoro_time = 0  # Reset for next session
            next_mode = "Long Break" if self.timer.pomodoro_count % 4 == 0 else "Short Break"
            self.pomodoro_count_label.config(text=f"Pomodoros: {self.timer.pomodoro_count}")
            self.stop_rain_sound()
            chime.success()
            if self.timer.auto_switch:
                self.switch_mode(next_mode)
            else:
                messagebox.showinfo(
                    "Pomodoro Complete",
                    "Well done! Time for a break!"
                )
                self.switch_mode(next_mode)
            self.update_historical_data()
            self.timer.save_state()  # Save the updated state
        else:
            self.stop_rain_sound()
            chime.success()
            if self.timer.auto_switch:
                self.switch_mode("Pomodoro")
            else:
                messagebox.showinfo(
                    "Break Complete",
                    "Break finished! Time to work!"
                )
                self.switch_mode("Pomodoro")
        
        if self.is_user_playsound:
            self.play_rain_sound()
        self.timer.save_state()  # Save state after completion

    def switch_mode(self, new_mode):
        self.timer.mode = new_mode
        self.mode_var.set(new_mode)
        self.reset_timer()
        self.toggle_timer()

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
        settings_window = tk.Toplevel(self.master)
        settings_window.title("Settings")
        settings_window.geometry("300x500")

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
        if not self.master.winfo_exists():
            return

        try:
            total_seconds = self.timer.total_pomodoro_time
            formatted_time = time.strftime("%H:%M:%S", time.gmtime(total_seconds))
            self.total_time_label.config(text=f"Total Time:{formatted_time}")

        except tk.TclError:
            pass

    def open_history(self):
        if not self.timer.historical_data:
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
                    pygame.mixer.quit()
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