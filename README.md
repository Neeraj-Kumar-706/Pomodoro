# Pomodoro Timer (v3)

This repository contains the code for a Pomodoro Timer application. The application allows users to set a timer for a Pomodoro session and provides options to switch between different modes (Pomodoro, Short Break, and Long Break).

## Prerequisites

Before running the application, make sure you have the following installed:
# here is a issue with version of numpy which requires by matplotlib so i highly recommend you install using requirements.txt
- **Python 3.11.2 or 3.11** recomment other might created dependency issuse
- `tkinter` package
- `ttkbootstrap` package
- `pygame` package 
- `matplotlib` package
- `chime` package


## Features

- Pomodoro timer with customizable durations for work sessions, short breaks, and long breaks.
- Historical data tracking to monitor your productivity over time.
- Rain sound feature to play background rain sounds during work sessions.
- Enhanced user interface using `ttkbootstrap` for modern and stylish components.
- Customizable button styles that change color when toggled.
- Suppression of the `pygame` welcome message for a cleaner startup using cmd gving just below 

## Running the Application from terminal cmd
```
python app.py > /dev/null 2>&1 & disown
```
you can replace app.py with app-v3.py for latest version

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/pomodoro-timer.git
    cd pomodoro-timer
    ```

2. Create and activate a virtual environment:
    ```sh
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

4. Run the application:
    ```sh
    python app-v3.py > /dev/null 2>&1 & disown
    ```

## Usage

- **Start**: Click the "Start" button to begin the Pomodoro timer.
- **Pause/Resume**: Click the "Pause" button to pause the timer, and click "Resume" to continue.
- **Reset**: Click the "Reset" button to reset the timer.
- **Settings**: Click the "Settings" button to customize the durations for work sessions, short breaks, and long breaks.
- **History**: Click the "History" button to view your productivity history.
- **Play Sound**: Click the "Play Sound" button to toggle the rain sound feature.

## Usage

1. Run the application: python3 app.py(app-version.py) or if add sh file into bin directory you can run from terminal as ./promodomo or just pomodoro
2. The application will open in a new window with the Pomodoro Timer GUI.

3. You can start a timer by clicking the "Start" button.

4. Switch between different modes using the dropdown menu.

5. Reset the timer by clicking the "Reset" button.

6. View the timer history by clicking the "History" button. save in file as pomodoro_history.json

7. Access the settings by clicking the "Settings" button.save in file as settings.json
8. Toggle the rain sound by clicking the "Play Sound" button.

## New Features (March 2024)

### Daily Mega Goal System
- Set daily work targets in hours
- Visual progress tracking with dual progress bars
- Automatic goal completion notifications
- Per-day goal persistence
- Date-specific goal tracking (goals are preserved for historical data)

### Enhanced History Visualization
- Dual chart view showing daily pomodoros and work hours
- Historical goal tracking (red dotted line)
- Up to 365 days of history stored (not just 30 days)
- Last 30 days displayed in graphs for better readability
- Daily statistics and running averages

### Auto-Switch Mode
- Automatic transition between work and break sessions
- Toggleable in settings
- Persistent setting between sessions
- Optional notification messages

### Background Rain Sound
- Ambient rain sound for focus
- Smart resume after breaks
- One-click toggle
- Automatically pauses during breaks

## Code Structure

The code is divided into three files:

- `app.py`: This file contains the main application code and is responsible for running the Pomodoro Timer.

- `draft.py`: This file contains the draft code for the new Pomodoro Timer implementation. It is used for testing and debugging purposes.
- `rain_sound.mp3`: This file contains the background music so add it to assets folder please and also logo of your desire path /assets/logo.png

## Contributing

If you would like to contribute to this project, please follow these steps:

1. Fork the repository.
2. Create a new branch.
3. Make your changes.
4. Test your changes thoroughly.
5. Commit your changes.
6. Push your changes to your forked repository.
7. Open a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.