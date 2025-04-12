# Configuration

## Logging System

The game uses Python's built-in logging system to help with debugging and monitoring. Change the logging level in the `logging.basicConfig` function at the beginning of each file from which you want to follow the logs.

Examples: `logger.debug("Debug message")`, `logger.info("Info message")`, `logger.warning("Warning message")`, `logger.error("Error message")`, `logger.critical("Critical message")`.

Available log levels (from most to least verbose):

- DEBUG: Detailed information for debugging.
- INFO: General information about game operation.
- WARNING: Indicates potential issues.
- ERROR: Serious problems that need attention.
- CRITICAL: Critical errors that prevent the game from running.

Logs are displayed in the console and include timestamps, module name, and log level.

## Configuration Files

The game's configuration is managed through a structured mapping system defined in the following files:

- `common/config.py`: The main configuration class that loads and validates the JSON configuration file.
- `common/client_config.py`: Contains all client-specific configuration options like connection details, display settings, game mode, and timeout values.
- `common/server_config.py`: Contains all server-specific configuration options like room size, game rules, respawn times, and AI agent settings.

Students are encouraged to read these files to understand what each configuration option does and its default value. The configuration system uses Pydantic models to provide clear documentation, type validation, and default values for all settings.

Add constants from the client and server config files to the config.json file to customize your game.