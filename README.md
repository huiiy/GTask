# Tasks TUI

A simple, fast, and intuitive Terminal User Interface (TUI) for Google Tasks.

## Disclaimer
This application only runs natively on MacOs and Linus boxes due to its dependencies on Python's Curses. I am working to migrate this application over to Uni-Curses to support cross-platform. 
## Features

*   View your Google Tasks directly in the terminal
*   Add new tasks and lists.
*   Mark tasks as complete.
*   Rename tasks and lists.
*   Switch between your task lists.
*   Add due dates, notes, or subtasks
*   Vim-style keybindings for navigation.

## Screenshots
<img width="1365" height="742" alt="image" src="https://github.com/user-attachments/assets/4c51a8ba-eac3-4a02-ab62-060d91150941" />



## Installation

1.  **Install via pip:**

    ```bash
    pip install tasks-tui-app
    ```

2.  **Clone the repository (optional, for development):**

    ```bash
    git clone https://github.com/your-username/Gtask.git
    cd Gtask
    ```

3.  **Install the dependencies (if cloning for development):**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Enable the Google Tasks API and download your `client_secrets.json` file:**

    *   Go to the [Google API Console](https://console.developers.google.com/).
    *   Create a new project.
    *   Enable the **Google Tasks API** for your project.
    *   Create an **OAuth 2.0 Client ID** for a **Desktop application**.
    *   Download the JSON file and rename it to `client_secrets.json`.
    *   Place the `client_secrets.json` file in the ~/.gtask.

## Usage

To run the application, use the following command:

```bash
tasks-tui
```

### Keyboard Shortcuts

| Key          | Action                                  |
| :----------- | :-------------------------------------- |
| `q`          | Quit application                        |
| `w`          | Write and Sync                          |
| `↑` / `k`    | Move selection up                       |
| `↓` / `j`    | Move selection down                     |
| `←` / `h`    | Exit selection                          |
| `→` / `l`    | Enter selection                         |
| `o`          | Open new selection                      |
| `d`          | Delete selection                        |
| `r`          | Rename selection                        |
| `c`          | Toggle task completion                  |
| `a`          | Add due date            |
| `i`          | Insert/view task note   |
| `p`          | Paste from buffer       |
| `?`          | Toggle Help                             |

### Task Status Symbols

| Symbol | Meaning                                                                     |
| :----- | :--------------                                                             |
| `[ ]`  | Task needs action                                                           |
| `[X]`  | Task completed                                                              |
| `*`    | Task has notes                                                              |
| `>`    | Task has subtasks (subtasks of subtasks do not display in web Google Tasks) |

When you run the application for the first time, it will open a web browser and ask you to authorize the application to access your Google Tasks. After you authorize the application, it will create a `token.json` file in the `~/.gtask` directory. This file contains your access and refresh tokens, so you won't have to authorize the application every time you run it.

## Contributing

Contributions are welcome! If you have any ideas, suggestions, or bug reports, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
