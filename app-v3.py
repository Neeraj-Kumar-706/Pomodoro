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


class PomodoroTimer:
    def __init__(self):
        self.load_settings()  # This already loads mega_goal
        self.current_time = self.pomodoro_time
        self.timer_running = False
        self.pomodoro_count = 0
        self.mode = "Pomodoro"
        self.total_pomodoro_time = 0
        self.historical_data = self.load_historical_data()
        self._daily_time = 0  # Track current day's time
        self.auto_switch = False  # Add auto switch feature

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
        chime.theme("big-sur")
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Suppress pygame welcome message
        original_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")
        pygame.mixer.init()
        sys.stdout = original_stdout

    def setup_gui(self):

        self.master.title("Pomodoro Timer")
        self.master.geometry("300x550")
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

        self.mode_var = tk.StringVar(value="Pomodoro")
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

        # Simple rain sound button
        self.play_sound_button = ttk.Button(
            self.master,
            text="Play Sound",
            command=self.toggle_rain_sound,
            style="primary.TButton",
        )
        self.play_sound_button.pack(pady=20)

        # Add Mega Goal Progress
        mega_frame = ttk.LabelFrame(self.master, text="Daily Mega Goal", padding=10)
        mega_frame.pack(pady=10, padx=5, fill="x")

        self.mega_progress = ttk.Progressbar(
            mega_frame, 
            orient="horizontal",
            length=200,
            mode="determinate",
            style="success.Horizontal.TProgressbar"
        )
        self.mega_progress.pack(pady=5)

        self.mega_label = ttk.Label(
            mega_frame,
            text=f"Progress: 0/{self.timer.mega_goal//3600}h"
        )
        self.mega_label.pack(pady=5)

        # Add separator
        ttk.Separator(self.master, orient="horizontal").pack(fill="x", pady=5)

        # Add auto switch toggle
        auto_switch_frame = ttk.Frame(self.master)
        auto_switch_frame.pack(pady=5, fill="x", padx=20)
        
        self.auto_switch_var = tk.BooleanVar(value=self.timer.auto_switch)
        self.auto_switch_check = ttk.Checkbutton(
            auto_switch_frame,
            text="Auto Switch Modes",
            variable=self.auto_switch_var,
            command=self.toggle_auto_switch
        )
        self.auto_switch_check.pack(side="left")

        # Progress Bars at bottom
        progress_frame = ttk.Frame(self.master)
        progress_frame.pack(side="bottom", fill="x", pady=10, padx=5)

        # Session progress
        self.session_progress = ttk.Progressbar(
            progress_frame,
            orient="horizontal",
            length=200,
            mode="determinate",
            style="info.Horizontal.TProgressbar"
        )
        self.session_progress.pack(fill="x", pady=2)

        # Mega goal progress
        self.mega_goal_progress = ttk.Progressbar(
            progress_frame,
            orient="horizontal",
            length=200,
            mode="determinate",
            style="success.Horizontal.TProgressbar"
        )
        self.mega_goal_progress.pack(fill="x", pady=2)

    def toggle_rain_sound(self):
        if self.is_playing:
            self.is_user_playsound = False
            self.stop_rain_sound()
        else:
            self.is_user_playsound = True
            self.play_rain_sound()

    def play_rain_sound(self):
        try:
            pygame.mixer.music.load(self.rain_sound)
            pygame.mixer.music.play(-1)  # Loop indefinitely
            self.is_playing = True
            self.play_sound_button.config(text="Stop Sound", style="danger.TButton")
        except Exception as e:
            print(f"Error playing sound: {e}")

    def stop_rain_sound(self):
        pygame.mixer.music.stop()
        self.is_playing = False
        self.play_sound_button.config(text="Play Sound", style="primary.TButton")

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

    def run_timer(self):
        """Optimized timer with better performance"""
        last_update = time.time()
        while not self.should_stop.is_set() and self.timer.current_time > 0:
            if not self.is_paused:
                current = time.time()
                elapsed = current - last_update
                if elapsed >= 1.0:  # Only update if a full second has passed
                    self.timer.current_time -= 1
                    if self.timer.mode == "Pomodoro":
                        self.timer.total_pomodoro_time += 1
                    self.master.after(0, self.update_display)
                    last_update = current
            time.sleep(0.1)  # Reduced CPU usage

        if not self.should_stop.is_set():
            self.master.after(0, self.timer_completed)

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
        """Optimized display updates with error handling"""
        try:
            # Cache frequently used values
            current_time = self.timer.current_time
            mode_time = self.timer.get_mode_time()
            
            self.timer_label.config(text=self.format_time(current_time))
            current_progress = (1 - current_time / mode_time) * 100
            self.progress_bar["value"] = current_progress
            
            if self.timer.mode == "Pomodoro":
                daily_time = self.timer._daily_time + self.timer.total_pomodoro_time
                mega_progress = min(100, (daily_time / self.timer.mega_goal) * 100)
                self.mega_goal_progress["value"] = mega_progress
                
            self.update_total_time_label()
            self.update_mega_progress()
        except tk.TclError:
            # Handle widget destruction gracefully
            pass
        except Exception as e:
            print(f"Display update error: {e}")

    def update_mega_progress(self):
        if not self.master.winfo_exists():
            return

        try:
            daily_time = 0
            today = datetime.date.today()
            
            # Get today's total time from historical data
            if self.timer.historical_data and self.timer.historical_data[-1][0] == today:
                daily_time = self.timer.historical_data[-1][2]
            
            # Add current session time if in Pomodoro mode
            if self.timer.mode == "Pomodoro":
                daily_time += self.timer.total_pomodoro_time

            progress = min(100, (daily_time / self.timer.mega_goal) * 100)
            self.mega_progress["value"] = progress
            
            hours_done = daily_time / 3600
            goal_hours = self.timer.mega_goal / 3600
            self.mega_label.config(
                text=f"Progress: {hours_done:.1f}/{goal_hours:.1f}h"
            )

            # Check if goal reached
            if not hasattr(self, '_goal_reached') and daily_time >= self.timer.mega_goal:
                self._goal_reached = True
                messagebox.showinfo("Congratulations!", "You've reached your daily mega goal! 🎉")
        except tk.TclError:
            pass

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

    def toggle_auto_switch(self):
        self.timer.auto_switch = self.auto_switch_var.get()
        self.timer.save_settings()

    def timer_completed(self):
        if self.timer.mode == "Pomodoro":
            self.timer.pomodoro_count += 1
            next_mode = "Long Break" if self.timer.pomodoro_count % 4 == 0 else "Short Break"
            
            # Update pomodoro count label
            self.pomodoro_count_label.config(text=f"Pomodoros: {self.timer.pomodoro_count}")
            
            # Stop sound and show notification
            self.stop_rain_sound()
            chime.success()
            
            # Handle mode switching
            if self.timer.auto_switch:
                self.switch_mode(next_mode)
            else:
                messagebox.showinfo(
                    "Pomodoro Complete",
                    "Well done! Time for a break!"
                )
                self.switch_mode(next_mode)
                
            self.update_historical_data()
            
        else:  # Break completed
            # Stop sound and show notification
            self.stop_rain_sound()
            chime.success()
            
            # Handle mode switching
            if self.timer.auto_switch:
                # In auto mode, just switch with no messages
                self.switch_mode("Pomodoro")
            else:
                # In manual mode, just show info message
                messagebox.showinfo(
                    "Break Complete",
                    "Break finished! Time to work!"
                )
                self.switch_mode("Pomodoro")
        
        # Restart rain sound if it was playing
        if self.is_user_playsound:
            self.play_rain_sound()

    def switch_mode(self, new_mode):
        self.timer.mode = new_mode
        self.mode_var.set(new_mode)
        self.reset_timer()
        self.toggle_timer()  # Auto start the timer

    def update_historical_data(self):
        today = datetime.date.today()
        try:
            if self.timer.historical_data and self.timer.historical_data[-1][0] == today:
                # Unpack all four values: date, count, time, mega_goal
                _, prev_count, prev_time, prev_goal = self.timer.historical_data[-1]
                self.timer.historical_data[-1] = (
                    today,
                    prev_count + 1,
                    prev_time + self.timer.pomodoro_time,
                    self.timer.mega_goal  # Keep current mega goal
                )
            else:
                # Add new entry with current mega goal
                self.timer.historical_data.append(
                    (today, 1, self.timer.pomodoro_time, self.timer.mega_goal)
                )
                # Trim old data (older than 365 days)
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
        settings_window.geometry("300x500")  # Increased height from 400 to 500

        # Main frame for settings
        settings_frame = ttk.Frame(settings_window, padding="20")
        settings_frame.pack(fill="both", expand=True)

        # Settings inputs
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

        # Add auto switch toggle to settings
        ttk.Label(settings_frame, text="Auto Switch Modes:").pack(pady=5)
        auto_switch_var = tk.BooleanVar(value=self.timer.auto_switch)
        ttk.Checkbutton(
            settings_frame,
            variable=auto_switch_var,
            text="Enable automatic mode switching"
        ).pack(pady=5)

        # Button frame for better organization
        button_frame = ttk.Frame(settings_frame)
        button_frame.pack(pady=20, fill="x")

        # Cancel button
        ttk.Button(
            button_frame,
            text="Cancel",
            style="secondary.TButton",
            command=settings_window.destroy
        ).pack(side="left", padx=5, expand=True)

        # Apply button
        ttk.Button(
            button_frame,
            text="Apply",
            style="info.TButton",
            command=lambda: save_settings(False)
        ).pack(side="left", padx=5, expand=True)

        # Save button
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
                
                # Update mega goal only for today's entry
                new_mega_goal = int(mega_goal_entry.get()) * 3600
                if new_mega_goal != self.timer.mega_goal:
                    old_mega_goal = self.timer.mega_goal
                    self.timer.mega_goal = new_mega_goal
                    
                    # Only update today's mega goal
                    today = datetime.date.today()
                    if self.timer.historical_data:
                        last_entry = self.timer.historical_data[-1]
                        if last_entry[0] == today:
                            # Update only today's entry
                            self.timer.historical_data[-1] = (
                                today,
                                last_entry[1],
                                last_entry[2],
                                new_mega_goal  # New mega goal only for today
                            )
                        else:
                            # If not today, add new entry with new mega goal
                            self.timer.historical_data.append((today, 0, 0, new_mega_goal))
                    else:
                        # If no history, start with today
                        self.timer.historical_data.append((today, 0, 0, new_mega_goal))
                        
                    self.timer.save_historical_data()
                    self.timer.save_settings()
                
                self.timer.auto_switch = auto_switch_var.get()
                self.auto_switch_var.set(self.timer.auto_switch)
                
                self.timer.save_settings()
                self.reset_timer()
                chime.success()
                
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
            return  # Stop updating if the window doesn't exist anymore

        try:  # at scene formating for label 12-02-2025
            total_seconds = self.timer.total_pomodoro_time
            formatted_time = time.strftime("%H:%M:%S", time.gmtime(total_seconds))
            self.total_time_label.config(text=f"Total Time:{formatted_time}")

        except tk.TclError:
            # Handle the case where the label no longer exists
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
        mega_goals = [item[3] / 3600 for item in data]  # Get mega goals in hours

        # Top plot: Pomodoro counts
        ax1.plot(dates, counts, color="#1e90ff", marker='o', label="Daily Pomodoros", linewidth=2)
        ax1.set_ylabel("Pomodoros", color="#1e90ff")
        ax1.grid(True, alpha=0.3)
        
        # Bottom plot: Hours with mega goal line
        ax2.plot(dates, total_times, color="lime", marker='s', label="Hours Worked", linewidth=2)
        ax2.plot(dates, mega_goals, color='red', linestyle='--', label='Daily Goals')
        ax2.set_ylabel("Hours", color="lime")
        ax2.grid(True, alpha=0.3)

        # Styling
        for ax in [ax1, ax2]:
            ax.set_facecolor("#2b2b2b")
            ax.tick_params(colors='white')
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            ax.legend(loc='upper left')

        # Add summary statistics in bottom left corner with padding
        stats_text = (f"Total Pomodoros: {sum(counts)}\n"
                     f"Total Hours: {sum(total_times):.1f}\n"
                     f"Daily Average: {sum(total_times)/len(dates):.1f} hours")
        
        # Position text in bottom left with padding
        fig.text(0.05, 0.02, stats_text,
                color='white',
                fontsize=10,
                bbox=dict(facecolor='#2b2b2b',
                         edgecolor='white',
                         alpha=0.7,
                         pad=10))

        # Adjust layout to leave space for stats
        plt.tight_layout(rect=[0, 0.1, 1, 0.95])
        
        canvas = FigureCanvasTkAgg(fig, master=history_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    @staticmethod
    def format_time(seconds):
        """Optimized time formatting"""
        try:
            seconds = max(0, int(seconds))
            if seconds < 3600:
                return time.strftime("%M:%S", time.gmtime(seconds))
            return time.strftime("%H:%M:%S", time.gmtime(seconds))
        except Exception:
            return "00:00"

    def on_closing(self):
        """Enhanced cleanup on exit"""
        try:
            self.is_running = False
            self.should_stop.set()
            if self.is_playing:
                self.stop_rain_sound()
            if self.timer_thread and self.timer_thread.is_alive():
                self.timer_thread.join(timeout=1)
            self.master.quit()
            self.master.destroy()
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
