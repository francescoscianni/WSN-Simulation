# WSN Simulation Framework 

This is a python-based project originally developed by Prof. Utz Roedig at the University College Cork¹.
The code simulates a wireless sensor network composed of Sinks and Sensors.
The simulator is being used with Prof. Roedig's authorization for the "Mobile Networks" course by Prof. Matthias Hollick at the Technical University of Darmstadt².

> **Important:** Instructions for specific assignments or tasks are provided separately in the accompanying exercise PDF. This README contains only framework-level documentation.

## Setup

This project uses `pyproject.toml` with the **hatchling** build backend.
The simulation has the following requirements:

- Python>=3.9.0
- pip>=21.3 
- simpy==4.1.1

You can install the requirements by performing the manual installation as described below.

### Manual installation

1. Open the terminal and set up a virtual environment:

    ```bash
    # On linux/macos:
    python3 -m venv venv
    ```

    ```powershell
    # On windows (MS Store):
    python -m venv venv

    # On windows (Standalone):
    py -m venv venv
    ```

    > **Note for Python novices:** A virtual environment is a folder which holds all libraries and scripts which are required for a specific Python application to run. By using it, you do not need to install all libraries globally. That would be a problem if you develop different applications which need the libraries in different versions. The folder that will created by the command above is called `venv` and resides in the project directory.
    >
    > You then can "activate" the virtual environment, which makes it active only for your current shell/terminal. All calls to tools like `python` or `pip` then happen in that environment.

2. Activate virtual environment

    ```bash
    # On linux/macos:
    source venv/bin/activate
    ```

    ```powershell
    # On windows (PowerShell):
    .\venv\Scripts\activate
    ```

    > You can leave the virtual environment again by closing the terminal or calling `deactivate`.

3. Install the simulator and its dependencies (e.g. simpy):

    ```bash
    # All operating systems
    pip install -e .
    ```

    > Note: This project relies on PEP 660 editable installs (`pip install -e .`),
    > which require **pip ≥ 21.3**. Some Python installations ship with an older pip
    > version. If installation fails, upgrade pip **inside the virtual environment**:
    >
    > ```bash
    > pip install --upgrade pip
    > ```

## Running the Simulator 

After installation, the simulation can be started with:

```bash
# First, make sure to activate the virtual environment as mentioned above
# (how to do it depends on your OS)
#
# Then run:
simulate
```
or equivalently:

```bash
# Alternatively, you can execute the package directly:
python -m wsn_simulation
```

> In the background that will run the `__main__.py` module in the `wsn_simulation` Python package. A Python package is a folder with a `__init__.py` module in it, so the `wsn_simulation` directory in the `src/` directory is a Python package.
> If you run a package (using `python -m package_name`), this will look for a `__main__.py` file in the package (the default entry point for the program) and then execute it like a normal Python script. In this package, the `__main__.py` module simply imports and calls the `main` function of the `core.py` module.

## Command-Line Interface

The simulator exposes a command-line interface to configure network size, timing, and loss parameters.

Use:

```bash
simulate -h
```
to see all available options and their descriptions.

These parameters are intended to support repeatable experiments, batch runs, and statistical evaluation.

##  Code Structure

- The `media`, `manager`, and `results` modules provide infrastructure.
- Node behavior is defined in the `node` subpackage.
- The simulation logic itself is protocol-agnostic.

## Getting Started

With that information, you can start playing around and watch how the simulation behaves. 
> ***Expert tip:*** Initialize a git repository in your exercise folder and commit all files (`git init`, `git add -A`, then `git commit -m "initial code"`), so you see what you have changed.

After a simulation run, aggregated results are computed based on the final network state.
These results can be used programmatically for further processing, visualization, or statistical analysis.

The exact interpretation of results depends on the experiment being conducted and is described in the accompanying exercise material.

## License

Contact Prof. Roedig¹ for authorization to re-use this code.

## References

¹ Prof. Utz Roedig. School of Computer Science and Information Technology. University College Cork. URL: <https://research.ucc.ie/en/persons/utz-roedig/>

² Prof. Matthias Hollick. Department of Computer Science. Technical University of Darmstadt. URL: <https://www.seemoo.tu-darmstadt.de/team/mhollick/>
