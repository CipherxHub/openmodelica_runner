# OpenModelica Simulation Runner

A **PyQt6 desktop application** that launches compiled OpenModelica executables
with configurable `startTime` / `stopTime` parameters, streams simulation output
in real-time, and enforces the constraint **0 ≤ startTime < stopTime < 5**.

---

## Screenshot

```
┌───────────────────────────────────────────────────────────────────────────┐
│  ⚙  OpenModelica Simulation Runner                                        
├───────────────────────────────────────────────────────────────────────────┤
│  ┌ Simulation Parameters ────────────────────────────────────────────┐    │
│  │  Application (Executable)                                         │    │
│  │  [ /path/to/TwoConnectedTanks                         ] [Browse]  │    │
│  │  Start Time (0 ≤ start < stop < 5)  Stop Time                     │    │
│  │  [ 0 ▲▼ ]                           [ 3 ▲▼ ]                      │    │
│  │  [▶ Run Simulation]   [Clear Output]                             
│  └───────────────────────────────────────────────────────────────────┘    │
│  ┌ Simulation Output ─────────────────────────────────────────────────┐   │
│  │  $ /path/to/TwoConnectedTanks -override startTime=0,stopTime=3     │   │
│  │  LOG_SUCCESS       | info    | The initialization finished …       │   │
│  │  [SUCCESS] Simulation completed (exit 0).                          │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│  Simulation finished successfully.                                        │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## Features

| Feature | Detail |
|---|---|
| **Executable picker** | Browse dialog + manual path entry |
| **Integer time controls** | QSpinBox widgets clamped to valid range |
| **Input validation** | User-friendly error messages before launch |
| **Non-blocking execution** | `QThread` worker keeps GUI responsive |
| **Live output streaming** | Colour-coded console (info / success / error) |
| **OOP architecture** | `MainWindow`, `SimulationRunner`, `SimulationInputValidator`, `SimulationWorker`, `OutputConsole`, `ExecutableSelector` |
| **PEP 8 compliant** | Formatted with `black`; linted with `ruff` |

---

## Technologies

- **Python 3.10+**
- **PyQt6** — GUI framework
- **OpenModelica** — model compilation & generated executable
- **pytest** — unit tests
- **subprocess** — process launch & streaming

---

## Project Structure

```
openmodelica_runner/
├── app/
│   ├── main.py                # Entry point + MainWindow (PyQt6)
│   ├── simulation_runner.py   # SimulationRunner (subprocess logic)
│   └── validators.py          # SimulationInputValidator
├── tests/
│   └── test_simulation_runner.py
├── model_executable/          # Place compiled OM files here (see below)
│   ├── TwoConnectedTanks      # compiled binary (Linux) or .exe (Windows)
│   └── TwoConnectedTanks_init.xml
├── requirements.txt
└── README.md
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/cipherxhub/openmodelica-simulation-runner.git
cd openmodelica-simulation-runner
```

### 2. Create and activate a virtual environment (recommended)

```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate.bat       # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install OpenModelica (for compiling the model)

Download from https://openmodelica.org/download/download-linux/ or the Windows
installer. The GUI app itself does **not** require OM at runtime — only the
compiled executable is needed.

---

## Compiling the TwoConnectedTanks Model

1. Open **OMEdit** (installed with OpenModelica).
2. **File → Load Model Package** → select the downloaded `.mo` file.
3. In the Model Browser, right-click `TwoConnectedTanks` → **Simulate**.
4. After simulation, go to **Tools → Open Working Directory**.
5. Copy the executable (`TwoConnectedTanks` / `TwoConnectedTanks.exe`) and all
   generated files into `model_executable/`.

---

## Running the App

```bash
cd app
python main.py
```

### Usage

1. Click **Browse** and select the compiled `TwoConnectedTanks` executable.
2. Set **Start Time** (integer, 0–3).
3. Set **Stop Time** (integer, must be > Start and < 5).
4. Click **▶ Run Simulation**.
5. Watch live output in the console panel.

### How arguments are passed

The app passes time values using OpenModelica's `-override` flag:

```
./TwoConnectedTanks -override startTime=0,stopTime=3
```

Reference: https://openmodelica.org/doc/OpenModelicaUsersGuide/latest/simulationflags.html#simflag-override

---

## Running the Tests

```bash
pytest tests/ -v
```

Expected output:

```
tests/test_simulation_runner.py::TestSimulationRunnerBuildCommand::test_basic_command_structure PASSED
tests/test_simulation_runner.py::TestSimulationRunnerBuildCommand::test_extra_flags_appended PASSED
...
9 passed in 0.34s
```

---

## OOP Design

```
MainWindow (QMainWindow)
│
├── ExecutableSelector (QWidget)   — file browse composite
├── OutputConsole (QTextEdit)      — colour-coded log display
└── SimulationWorker (QThread)
        │
        └── SimulationRunner       — subprocess + command builder
                │
                └── (uses) SimulationInputValidator — pure validation logic
```

Each class has a single responsibility and communicates via Qt signals or
return values — no global state.

---

## Constraint Enforced

```
0 ≤ startTime < stopTime < 5
```

The validator returns descriptive error strings; the worker thread is never
launched if validation fails.

---

## License

MIT © 2026 CipherxHub 
