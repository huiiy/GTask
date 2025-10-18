# Tasks TUI

A simple, fast, and intuitive Terminal User Interface (TUI) for Google Tasks.

## Features

*   View your Google Tasks lists and tasks in a two-panel layout.
*   Add new tasks and lists.
*   Mark tasks as complete.
*   Rename tasks and lists.
*   Switch between your task lists.
*   Vim-style keybindings for navigation.
*   Toggleable help panel.

## Screenshots

(A new screenshot is needed)


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

| Key          | Action                                  | Panel      |
| :----------- | :-------------------------------------- | :--------- |
| `q`          | Quit application                        | Any        |
| `w`          | Write and Sync                          | Any        |
| `↑` / `k`    | Move selection up                       | Any        |
| `↓` / `j`    | Move selection down                     | Any        |
| `←` / `h`    | Switch to Lists panel (from Tasks)      | Tasks      |
| `→` / `l`    | Switch to Tasks panel (from Lists)      | Lists      |
| `Tab`        | Toggle between Lists and Tasks panels   | Any        |
| `o`          | Add new task / Add new list             | Tasks/Lists|
| `d`          | Delete selected task / Delete selected list | Tasks/Lists|
| `r`          | Rename selected task / Rename selected list | Tasks/Lists|
| `c`          | Toggle task completion                  | Tasks      |
| `a`          | Add due date to selected task           | Tasks      |
| `i`          | Add notes to selected task              | Tasks      |
| `p`          | Paste task / Paste list                 | Tasks/Lists|
| `?`          | Toggle Help                             | Any        |

When you run the application for the first time, it will open a web browser and ask you to authorize the application to access your Google Tasks. After you authorize the application, it will create a `token.json` file in the `tasks-tui` directory. This file contains your access and refresh tokens, so you won't have to authorize the application every time you run it.

## Contributing

Contributions are welcome! If you have any ideas, suggestions, or bug reports, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
