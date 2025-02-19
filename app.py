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
        self.load_settings()
        self.current_time = self.pomodoro_time
        self.timer_running = False
        self.pomodoro_count = 0
        self.mode = "Pomodoro"
        self.total_pomodoro_time = 0
        self.historical_data = self.load_historical_data()

    def load_settings(self):
        try:
            with open("settings.json", "r") as f:
                settings = json.load(f)
                self.pomodoro_time = settings["pomodoro"] * 60
                self.short_break_time = settings["short_break"] * 60
                self.long_break_time = settings["long_break"] * 60
        except FileNotFoundError:
            self.pomodoro_time = 25 * 60
            self.short_break_time = 5 * 60
            self.long_break_time = 15 * 60

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
                return deque(
                    [(datetime.date.fromisoformat(d), count) for d, count in data],
                    maxlen=7,
                )
        except (FileNotFoundError, json.JSONDecodeError):
            return deque(maxlen=7)

    def save_historical_data(self):
        data = [(d.isoformat(), count) for d, count in self.historical_data]
        with open("pomodoro_history.json", "w") as f:
            json.dump(data, f)

    def save_settings(self):
        settings = {
            "pomodoro": self.pomodoro_time // 60,
            "short_break": self.short_break_time // 60,
            "long_break": self.long_break_time // 60,
        }
        with open("settings.json", "w") as f:
            json.dump(settings, f)


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

        self.play_sound_button = ttk.Button(
            self.master,
            text="Play Sound",
            command=self.toggle_rain_sound,
            style="primary.TButton",
        )
        self.play_sound_button.pack(pady=20)

    def toggle_rain_sound(self):
        if self.is_playing:
            self.is_user_playsound = False  # edit 19/02/25
            self.stop_rain_sound()
        else:
            self.is_user_playsound = True  # edit 19/02/25
            self.play_rain_sound()

    def play_rain_sound(self):
        def play():
            try:
                pygame.mixer.music.load(self.rain_sound)
                pygame.mixer.music.play(-1)  # Loop indefinitely
                while pygame.mixer.music.get_busy() and not self.stop_playback.is_set():
                    time.sleep(0.1)
                pygame.mixer.music.stop()
                self.is_playing = False
                self.play_sound_button.config(text="Play Sound")
            except Exception as e:
                print(f"Error playing sound: {e}")

        self.stop_playback.clear()
        self.play_thread = threading.Thread(target=play, daemon=True)
        self.play_thread.start()
        self.is_playing = True
        self.play_sound_button.config(text="Stop Sound", style="danger.TButton")

    def stop_rain_sound(self):
        self.stop_playback.set()
        pygame.mixer.music.stop()
        self.is_playing = False
        self.play_sound_button.config(text="Play Sound", style="primary.TButton")

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
        while not self.should_stop.is_set() and self.timer.current_time > 0:
            if not self.is_paused:
                self.timer.current_time -= 1
                if self.timer.mode == "Pomodoro":
                    self.timer.total_pomodoro_time += 1
                self.master.after(0, self.update_display)
                time.sleep(1)
            else:
                time.sleep(0.1)

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
        self.timer_label.config(text=self.format_time(self.timer.current_time))
        self.progress_bar["value"] = (
            1 - self.timer.current_time / self.timer.get_mode_time()
        ) * 100
        self.update_total_time_label()

    # can be deleted

    def timer_completed(self):
        if self.timer.mode == "Pomodoro":
            self.timer.pomodoro_count += 1
            self.timer.mode = (
                "Long Break" if self.timer.pomodoro_count % 4 == 0 else "Short Break"
            )
            self.update_historical_data()
        else:
            self.timer.mode = "Pomodoro"
            # edit 16/01/25 add below to stop rain sound then nofity and on click ok it again start rain sound
            # edit 19/02/25 fix bug : it start audio after complete one podomoro when user even not start bg music
            self.stop_rain_sound()
        chime.success()
        messagebox.showinfo(
            "Pomodoro Timer",
            (
                "let get to work!"
                if self.timer.mode == "Pomodoro"
                else "well done take a break!"
            ),
        )
        if self.is_user_playsound:
            self.play_rain_sound()  # edit 16/01/25
        self.mode_var.set(self.timer.mode)
        self.pomodoro_count_label.config(text=f"Pomodoros: {self.timer.pomodoro_count}")
        self.reset_timer()

    def update_historical_data(self):
        today = datetime.date.today()
        if self.timer.historical_data and self.timer.historical_data[-1][0] == today:
            self.timer.historical_data[-1] = (
                today,
                self.timer.historical_data[-1][1] + 1,
            )
        else:
            self.timer.historical_data.append((today, 1))
        self.timer.save_historical_data()

    def open_settings(self):
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
                self.timer.pomodoro_time = int(pomodoro_entry.get()) * 60
                self.timer.short_break_time = int(short_break_entry.get()) * 60
                self.timer.long_break_time = int(long_break_entry.get()) * 60
                chime.success()
                self.timer.save_settings()
                self.reset_timer()

                settings_window.destroy()
            except ValueError:
                chime.error()
                messagebox.showerror(
                    "Invalid Input", "Please enter valid numbers for all durations."
                )

        ttk.Button(settings_window, text="Save", command=save_settings).pack(pady=10)

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
        history_window = tk.Toplevel(self.master)
        history_window.title("Pomodoro History")
        history_window.geometry("750x500")

        # Set up the plot with a dark theme
        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(8, 5))
        fig.patch.set_facecolor("#2b2b2b")  # Dark grey background
        ax.set_facecolor("#2b2b2b")  # Dark grey background for the plot area

        canvas = FigureCanvasTkAgg(fig, master=history_window)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=True)

        data = list(self.timer.historical_data)
        dates = [item[0] for item in data]
        counts = [item[1] for item in data]
        chime.error()
        bars = ax.bar(dates, counts, color="#1e90ff")  # Dodger blue bars

        # Customize the plot
        ax.set_xlabel("Date", color="white", fontweight="bold")
        ax.set_ylabel("Pomodoros Completed", color="white", fontweight="bold")
        ax.set_title("Pomodoro History", color="white", fontweight="bold", fontsize=14)

        # Customize x-axis
        plt.xticks(rotation=45, ha="right", color="white")

        # Customize y-axis
        plt.yticks(color="white")

        # Add value labels on top of each bar
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{int(height)}",
                ha="center",
                va="bottom",
                color="white",
            )

        # Remove top and right spines
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # Color the remaining spines white
        ax.spines["bottom"].set_color("white")
        ax.spines["left"].set_color("white")

        plt.tight_layout()
        canvas.draw()

    @staticmethod
    def format_time(seconds):
        minutes, secs = divmod(seconds, 60)
        return f"{minutes:02d}:{secs:02d}"

    def on_closing(self):
        self.is_running = False
        self.should_stop.set()
        if self.timer_thread and self.timer_thread.is_alive():
            self.timer_thread.join(timeout=1)
        self.master.quit()
        self.stop_rain_sound()
        self.master.destroy()
        os._exit(0)  # Force Python to exit


if __name__ == "__main__":
    root = tk.Tk()
    icon_image = tk.PhotoImage(
        file="assets/time-organization.png"
    )  # use some logo i give what you like # Ensure logo.png is in the same directory
    root.iconphoto(False, icon_image)
    app = PomodoroTimerGUI(root)
    try:
        root.mainloop()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        os._exit(0)  # Ensure the application exits even if an exception occurs
