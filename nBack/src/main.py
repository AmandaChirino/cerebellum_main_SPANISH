#./src/main.py
"""
Application entry point.

This module initializes the application environment and starts the main execution flow.
All core logic is delegated to other modules.
"""


from core.experiment_flow import run


if __name__ == "__main__":
    run()
