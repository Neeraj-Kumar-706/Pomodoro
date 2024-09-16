import tkinter as tk
from ttkbootstrap import Style, ttk
from tkinter import messagebox
import os
import threading
import simpleaudio as sa
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque
import datetime
import json


class PomodoroTimerBase:
    """Base class for Pomodoro Timer functionality"""
    #edit
    def load_settings(self):
        """Load settings from settings.json"""
        try:
            with open('settings.json', 'r') as f:
                settings = json.load(f)
                self.pomodoro_time = settings['pomodoro'] * 60
                self.short_break_time = settings['short_break'] * 60
                self.long_break_time = settings['long_break'] * 60
                return self.pomodoro_time, self.short_break_time, self.long_break_time
        except FileNotFoundError:
            pass
       
    def __init__(self):
        #edit
        things=PomodoroTimerBase.load_settings(self)
    
        self.pomodoro_time = things[0]
        self.short_break_time = things[1]
        self.long_break_time = things[2]
        self.current_time = things[0]
        self.timer_running = False
        self.pomodoro_count = 0
        self.mode = "Pomodoro"
        self.total_pomodoro_time = 0
        #self.historical_data = deque(maxlen=7)  # Store data for the last 7 days
        self.historical_data = self.load_historical_data() #edit 

    def start_timer(self):
        """Start the timer"""
        self.timer_running = True

    def stop_timer(self):
        """Stop the timer"""
        self.timer_running = False

    def reset_timer(self):
        """Reset the timer to the current mode's duration"""
        self.timer_running = False
        self.current_time = self.get_mode_time()

    def get_mode_time(self):
        """Get the duration for the current mode"""
        if self.mode == "Pomodoro":
            return self.pomodoro_time
        elif self.mode == "Short Break":
            return self.short_break_time
        elif self.mode == "Long Break":
            return self.long_break_time

    def change_mode(self, new_mode):
        """Change the current mode"""
        self.mode = new_mode
        self.reset_timer()

    def update_time(self):
        """Update the current time (to be called every second)"""
        if self.timer_running and self.current_time > 0:
            self.current_time -= 1
            if self.mode == "Pomodoro":
                self.total_pomodoro_time += 1
            return True
        elif self.current_time <= 0:
            return False
        return True

    def timer_completed(self):
        """Handle timer completion"""
        if self.mode == "Pomodoro":
            self.pomodoro_count += 1
            self.update_historical_data()
            if self.pomodoro_count % 4 == 0:
                self.mode = "Long Break"
            else:
                self.mode = "Short Break"
        else:
            self.mode = "Pomodoro"
        self.reset_timer()

    def update_settings(self, pomodoro, short_break, long_break):
        """Update timer durations"""
        self.pomodoro_time = pomodoro * 60
        self.short_break_time = short_break * 60
        self.long_break_time = long_break * 60
        self.reset_timer()

    def get_total_pomodoro_time(self):
        """Get the total time spent on Pomodoro sessions"""
        return self.total_pomodoro_time

    def update_historical_data(self):
        """Update the historical data with today's Pomodoro count"""
        today = datetime.date.today()
        if self.historical_data and self.historical_data[-1][0] == today:
            self.historical_data[-1] = (today, self.historical_data[-1][1] + 1)
        else:
            self.historical_data.append((today, 1))
        self.save_historical_data()  #edit
    def get_historical_data(self):
        """Get the historical data for plotting"""
        return list(self.historical_data)
    #edit
    
    def load_historical_data(self):
        """Load historical data from a JSON file"""
        try:
            with open('pomodoro_history.json', 'r') as f:
                data = json.load(f)
                return deque([(datetime.date.fromisoformat(d), count) for d, count in data], maxlen=7)
        except (FileNotFoundError, json.JSONDecodeError):
            return deque(maxlen=7)
    
    def save_historical_data(self):
        """Save historical data to a JSON file"""
        data = [(d.isoformat(), count) for d, count in self.historical_data]
        with open('pomodoro_history.json', 'w') as f:
            json.dump(data, f)

class PomodoroTimerGUI:
    """GUI class for Pomodoro Timer"""

    def __init__(self, master):
        self.master = master
        self.timer = PomodoroTimerBase()
        self.setup_gui()
        #edit
        self.pomodoro_sound = os.path.join(os.path.dirname(__file__), 'work.wav')
        self.break_sound = os.path.join(os.path.dirname(__file__), 'rest.wav')
    def setup_gui(self):
        """Set up the GUI elements"""
        self.master.title("Pomodoro Timer")
        self.master.geometry("300x550")  # Increased height to accommodate new button
        self.master.resizable(False, False)

        self.style = Style(theme='darkly')
        #edit
        pmdt=PomodoroTimerBase.load_settings(self)
        #edit
        self.timer_label = ttk.Label(self.master, text=f"{pmdt[0]//60}:00", font=("Helvetica", 48))
        self.timer_label.pack(pady=20)

        self.start_button = ttk.Button(self.master, text="Start", command=self.toggle_timer)
        self.start_button.pack(pady=10)

        self.reset_button = ttk.Button(self.master, text="Reset", command=self.reset_timer)
        self.reset_button.pack(pady=10)

        self.mode_var = tk.StringVar(value="Pomodoro")
        self.mode_menu = ttk.OptionMenu(self.master, self.mode_var, "Pomodoro", "Pomodoro", "Short Break", "Long Break", command=self.change_mode)
        self.mode_menu.pack(pady=10)

        self.progress_bar = ttk.Progressbar(self.master, orient="horizontal", length=200, mode="determinate")
        self.progress_bar.pack(pady=20)

        self.pomodoro_count_label = ttk.Label(self.master, text="Pomodoros: 0")
        self.pomodoro_count_label.pack(pady=10)

        self.total_time_label = ttk.Label(self.master, text="Total Time: 00:00:00")
        self.total_time_label.pack(pady=10)

        # Create a frame for buttons
        button_frame = ttk.Frame(self.master)
        button_frame.pack(pady=10)

        self.settings_button = ttk.Button(button_frame, text="Settings", command=self.open_settings)
        self.settings_button.pack(side=tk.LEFT, padx=5)

        self.history_button = ttk.Button(button_frame, text="History", command=self.open_history)
        self.history_button.pack(side=tk.LEFT, padx=5)

    def toggle_timer(self):
        """Toggle the timer between running and paused states"""
        if self.timer.timer_running:
            self.timer.stop_timer()
            self.start_button.config(text="Resume")
        else:
            self.timer.start_timer()
            self.start_button.config(text="Pause")
            self.update_timer()

    def update_timer(self):
        """Update the timer display"""
        if self.timer.update_time():
            minutes, seconds = divmod(self.timer.current_time, 60)
            self.timer_label.config(text=f"{minutes:02d}:{seconds:02d}")
            self.progress_bar["value"] = (1 - self.timer.current_time / self.timer.get_mode_time()) * 100
            self.update_total_time_label()
            self.master.after(1000, self.update_timer)
        else:
            self.timer_completed()

    def reset_timer(self):
        """Reset the timer"""
        self.timer.reset_timer()
        self.start_button.config(text="Start")
        self.update_display()

    def change_mode(self, *args):
        """Change the current mode"""
        self.timer.change_mode(self.mode_var.get())
        self.reset_timer()

    def update_display(self):
        """Update the timer display"""
        minutes, seconds = divmod(self.timer.current_time, 60)
        self.timer_label.config(text=f"{minutes:02d}:{seconds:02d}")
        self.progress_bar["value"] = 0
        self.update_total_time_label()
    #edit
    def play_sound(self, sound_file):
        """Play a sound file using simpleaudio"""
        def sound_thread():
            try:
                wave_obj = sa.WaveObject.from_wave_file(sound_file)
                play_obj = wave_obj.play()
                play_obj.wait_done()  # Wait for sound to finish playing
            except Exception as e:
                pass
                #print(f"Error playing sound: {e}")
                #print("Unable to play sound. Please check your sound files and system audio settings.")

        # Start sound playback in a separate thread
        threading.Thread(target=sound_thread, daemon=True).start()

    def timer_completed(self):
        """Handle timer completion"""
        self.timer.timer_completed()
        if self.timer.mode == "Pomodoro":
            self.play_sound(self.break_sound)
            messagebox.showinfo("Pomodoro Timer", "Break time is over. Back to work!")
            #edit just exchange messasgeboc weteen up and below
        else:
            self.play_sound(self.pomodoro_sound)
            messagebox.showinfo("Pomodoro Timer", "Time for a break!")
            
        self.mode_var.set(self.timer.mode)
        self.pomodoro_count_label.config(text=f"Pomodoros: {self.timer.pomodoro_count}")
        self.reset_timer()

    def open_settings(self):
        """Open the settings window"""
        settings_window = tk.Toplevel(self.master)
        settings_window.title("Settings")
        settings_window.geometry("300x300")
        settings_window.resizable(False, False)

        ttk.Label(settings_window, text="Pomodoro Duration (minutes):").pack(pady=5)
        pomodoro_entry = ttk.Entry(settings_window)
        pomodoro_entry.insert(0, str(self.timer.pomodoro_time // 60))
        pomodoro_entry.pack(pady=5)

        ttk.Label(settings_window, text="Short Break Duration (minutes):").pack(pady=5)
        short_break_entry = ttk.Entry(settings_window)
        short_break_entry.insert(0, str(self.timer.short_break_time // 60))
        short_break_entry.pack(pady=5)

        ttk.Label(settings_window, text="Long Break Duration (minutes):").pack(pady=5)
        long_break_entry = ttk.Entry(settings_window)
        long_break_entry.insert(0, str(self.timer.long_break_time // 60))
        long_break_entry.pack(pady=5)

        def save_settings():
            try:
                pomodoro = int(pomodoro_entry.get())
                short_break = int(short_break_entry.get())
                long_break = int(long_break_entry.get())
                self.timer.update_settings(pomodoro, short_break, long_break)
                # edit
                with open('settings.json', 'w') as f:
                  json.dump({'pomodoro': pomodoro,'short_break': short_break,'long_break': long_break}, f)
                self.reset_timer()
                settings_window.destroy()
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter valid numbers for all durations.")

        ttk.Button(settings_window, text="Save", command=save_settings).pack(pady=10)

    def update_total_time_label(self):
        """Update the total time spent label"""
        total_seconds = self.timer.get_total_pomodoro_time()
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.total_time_label.config(text=f"Total Time: {hours:02d}:{minutes:02d}:{seconds:02d}")

    def open_history(self):
        """Open the history window with a graph"""
        history_window = tk.Toplevel(self.master)
        history_window.title("Pomodoro History")
        history_window.geometry("700x400")

        fig, ax = plt.subplots(figsize=(8, 5))
        canvas = FigureCanvasTkAgg(fig, master=history_window)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=True)

        data = self.timer.get_historical_data()
        dates = [item[0] for item in data]
        counts = [item[1] for item in data]

        ax.bar(dates, counts)
        ax.set_xlabel("Date")
        ax.set_ylabel("Pomodoros Completed")
        ax.set_title("Pomodoro History (Last 7 Days)")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = PomodoroTimerGUI(root)
    root.mainloop()