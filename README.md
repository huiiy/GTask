# Tasks TUI

A simple, fast, and intuitive Terminal User Interface (TUI) for Google Tasks.

## Features

*   View your Google Tasks lists and tasks in a two-panel layout.
*   Add new tasks to your lists.
*   Mark tasks as complete.
*   Switch between your task lists.
*   Vim-style keybindings for navigation.

## Screenshots

*(Add a screenshot or GIF of your application here)*

## Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/Gtask.git
    cd Gtask
    ```

2.  **Install the dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Enable the Google Tasks API and download your `client_secrets.json` file:**

    *   Go to the [Google API Console](https://console.developers.google.com/).
    *   Create a new project.
    *   Enable the **Google Tasks API** for your project.
    *   Create an **OAuth 2.0 Client ID** for a **Desktop application**.
    *   Download the JSON file and rename it to `client_secrets.json`.
    *   Place the `client_secrets.json` file in the `tasks-tui` directory.

## Usage

To run the application, use the following command:

```bash
python3 -m tasks_tui.main
```

When you run the application for the first time, it will open a web browser and ask you to authorize the application to access your Google Tasks. After you authorize the application, it will create a `token.json` file in the `tasks-tui` directory. This file contains your access and refresh tokens, so you won't have to authorize the application every time you run it.

## Contributing

Contributions are welcome! If you have any ideas, suggestions, or bug reports, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
