"""
setup.py
Full environment setup for cypher-aibookgenerator.

Responsibilities:
  - Detect OS (Windows / macOS / Linux)
  - Ask user: conda environment OR Python venv
  - If conda: create + activate conda env "cypher-aibookgenerator" and install deps
  - If venv:  create .venv and install deps
  - Install Ollama if not present
  - Pull llama3.2:3b model (only if missing)
  - Detect GPU and report backend

Run with:
  python setup.py
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


# ─────────────────────────────────────────────
# Terminal colors (zero dependencies)
# ─────────────────────────────────────────────

class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    CYAN   = "\033[96m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    DIM    = "\033[2m"
    WHITE  = "\033[97m"


def ok(msg: str):   print(f"{C.GREEN}  ✔  {msg}{C.RESET}")
def info(msg: str): print(f"{C.CYAN}  ℹ  {msg}{C.RESET}")
def warn(msg: str): print(f"{C.YELLOW}  ⚠  {msg}{C.RESET}")
def err(msg: str):  print(f"{C.RED}  ✘  {msg}{C.RESET}")
def hdr(msg: str):
    bar = "─" * 52
    print(f"\n{C.BOLD}{C.CYAN}{bar}\n  {msg}\n{bar}{C.RESET}")


# ─────────────────────────────────────────────
# OS helpers
# ─────────────────────────────────────────────

SYSTEM = platform.system()   # "Windows", "Darwin", "Linux"

def is_windows() -> bool: return SYSTEM == "Windows"
def is_macos()   -> bool: return SYSTEM == "Darwin"
def is_linux()   -> bool: return SYSTEM == "Linux"

CONDA_ENV_NAME = "cypher-aibookgenerator"
VENV_DIR       = ".venv"
MODEL          = "llama3.2:3b"
OLLAMA_URL     = "http://localhost:11434"


def run_cmd(
    cmd: list,
    check: bool = True,
    capture: bool = False,
    env: dict = None,
    **kwargs,
) -> subprocess.CompletedProcess:
    """Run a subprocess, print stderr on failure."""
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=capture,
            text=True,
            env=env or os.environ.copy(),
            **kwargs,
        )
        return result
    except subprocess.CalledProcessError as exc:
        err(f"Command failed: {' '.join(str(c) for c in cmd)}")
        if exc.stderr:
            print(f"  {C.DIM}{exc.stderr.strip()}{C.RESET}")
        raise
    except FileNotFoundError:
        err(f"Executable not found: {cmd[0]}")
        raise


# ─────────────────────────────────────────────
# 1. Python version check
# ─────────────────────────────────────────────

def check_python_version():
    hdr("Checking Python Version")
    major, minor = sys.version_info[:2]
    info(f"Python {major}.{minor} detected.")
    if major < 3 or (major == 3 and minor < 10):
        err(f"Python 3.10+ required. You have {major}.{minor}.")
        err("Upgrade: https://www.python.org/downloads/")
        sys.exit(1)
    ok(f"Python {major}.{minor} — compatible.")


# ─────────────────────────────────────────────
# 2. Environment type selection
# ─────────────────────────────────────────────

def ask_env_type() -> str:
    """
    Ask the user whether to use conda or venv.
    Returns "conda" or "venv".
    """
    hdr("Choose Environment Type")

    conda_available = shutil.which("conda") is not None

    print(f"""
  {C.BOLD}Select how to set up the Python environment:{C.RESET}

    {C.CYAN}[1] conda{C.RESET}  — Creates conda env '{CONDA_ENV_NAME}'
              Recommended if you use Anaconda / Miniconda
              {'(conda detected ✔)' if conda_available else f'{C.YELLOW}(conda NOT found — install from https://docs.conda.io){C.RESET}'}

    {C.CYAN}[2] venv{C.RESET}   — Creates a standard Python .venv folder
              Works with any Python installation
""")

    while True:
        choice = input(f"  {C.BOLD}Enter 1 (conda) or 2 (venv) [default: 1 if conda found, else 2]: {C.RESET}").strip()

        if choice == "" :
            default = "conda" if conda_available else "venv"
            info(f"Using default: {default}")
            return default
        elif choice == "1":
            if not conda_available:
                warn("conda not found on PATH.")
                install = input("  Install Miniconda automatically? (y/n) [y]: ").strip().lower()
                if install in ("", "y", "yes"):
                    install_miniconda()
                else:
                    warn("Falling back to venv.")
                    return "venv"
            return "conda"
        elif choice == "2":
            return "venv"
        else:
            warn("Please enter 1 or 2.")


# ─────────────────────────────────────────────
# 3a. Conda environment
# ─────────────────────────────────────────────

def _conda_env_exists() -> bool:
    """Return True if the conda env already exists."""
    result = run_cmd(["conda", "env", "list"], capture=True, check=False)
    if result.returncode != 0:
        return False
    return CONDA_ENV_NAME in result.stdout


def _get_conda_python() -> str:
    """Return the path to python inside the conda env."""
    result = run_cmd(
        ["conda", "run", "-n", CONDA_ENV_NAME, "python", "-c",
         "import sys; print(sys.executable)"],
        capture=True,
        check=False,
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    # Fallback: guess path
    if is_windows():
        base = Path(os.environ.get("CONDA_PREFIX", Path.home() / "miniconda3"))
        return str(base / "envs" / CONDA_ENV_NAME / "python.exe")
    else:
        base = Path(os.environ.get("CONDA_PREFIX", Path.home() / "miniconda3"))
        return str(base / "envs" / CONDA_ENV_NAME / "bin" / "python")


def setup_conda() -> tuple[str, str]:
    """
    Create conda env 'cypher-aibookgenerator' if it doesn't exist,
    install requirements inside it.
    Returns (pip_path, python_path) inside the env.
    """
    hdr(f"Setting Up Conda Environment: {CONDA_ENV_NAME}")

    if _conda_env_exists():
        ok(f"Conda env '{CONDA_ENV_NAME}' already exists.")
    else:
        info(f"Creating conda env '{CONDA_ENV_NAME}' with Python 3.10...")
        run_cmd([
            "conda", "create",
            "-n", CONDA_ENV_NAME,
            "python=3.10",
            "-y",
            "--quiet",
        ])
        ok(f"Conda env '{CONDA_ENV_NAME}' created.")

    # Get python/pip paths inside the env
    python_path = _get_conda_python()
    info(f"Conda Python: {python_path}")

    # Upgrade pip inside the env
    info("Upgrading pip inside conda env...")
    run_cmd([
        "conda", "run", "-n", CONDA_ENV_NAME,
        "pip", "install", "--upgrade", "pip", "--quiet",
    ])

    # Install requirements
    req_file = Path("requirements.txt")
    if not req_file.exists():
        err("requirements.txt not found. Run setup.py from the project root directory.")
        sys.exit(1)

    info(f"Installing requirements into conda env '{CONDA_ENV_NAME}'...")
    run_cmd([
        "conda", "run", "-n", CONDA_ENV_NAME,
        "pip", "install", "-r", str(req_file), "--quiet",
    ])
    ok("All dependencies installed in conda env.")

    # Derive pip path (used for display only; we call via conda run)
    if is_windows():
        pip_path = str(Path(python_path).parent / "pip.exe")
    else:
        pip_path = str(Path(python_path).parent / "pip")

    return pip_path, python_path


def install_miniconda():
    """Download and install Miniconda for the current OS/arch."""
    hdr("Installing Miniconda")
    arch = platform.machine().lower()

    if is_linux():
        suffix = "Linux-x86_64" if "x86_64" in arch else "Linux-aarch64"
        url = f"https://repo.anaconda.com/miniconda/Miniconda3-latest-{suffix}.sh"
        dest = Path.home() / "miniconda_installer.sh"
        info(f"Downloading {url} ...")
        urllib.request.urlretrieve(url, str(dest))
        dest.chmod(0o755)
        info("Running Miniconda installer (non-interactive)...")
        run_cmd(["bash", str(dest), "-b", "-p", str(Path.home() / "miniconda3")])
        dest.unlink(missing_ok=True)
        # Add to PATH for this process
        conda_bin = str(Path.home() / "miniconda3" / "bin")
        os.environ["PATH"] = conda_bin + os.pathsep + os.environ["PATH"]
        ok("Miniconda installed. You may need to restart your shell after setup.")

    elif is_macos():
        arch_tag = "arm64" if "arm" in arch else "x86_64"
        url = f"https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-{arch_tag}.sh"
        dest = Path.home() / "miniconda_installer.sh"
        info(f"Downloading {url} ...")
        urllib.request.urlretrieve(url, str(dest))
        dest.chmod(0o755)
        run_cmd(["bash", str(dest), "-b", "-p", str(Path.home() / "miniconda3")])
        dest.unlink(missing_ok=True)
        conda_bin = str(Path.home() / "miniconda3" / "bin")
        os.environ["PATH"] = conda_bin + os.pathsep + os.environ["PATH"]
        ok("Miniconda installed.")

    elif is_windows():
        url = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe"
        dest = Path.home() / "Downloads" / "Miniconda3-latest-Windows-x86_64.exe"
        info(f"Downloading {url} ...")
        urllib.request.urlretrieve(url, str(dest))
        info("Running Miniconda installer (silent)...")
        run_cmd([
            str(dest), "/InstallationType=JustMe",
            "/RegisterPython=0", "/S",
            f"/D={Path.home() / 'miniconda3'}",
        ])
        conda_bin = str(Path.home() / "miniconda3" / "Scripts")
        os.environ["PATH"] = conda_bin + os.pathsep + os.environ["PATH"]
        ok("Miniconda installed.")
    else:
        err(f"Auto-install not supported on {SYSTEM}. Install manually: https://docs.conda.io")
        sys.exit(1)

    if not shutil.which("conda"):
        warn("conda not yet on PATH in this shell session.")
        warn("Please restart your terminal and re-run: python setup.py")
        sys.exit(0)


# ─────────────────────────────────────────────
# 3b. venv environment
# ─────────────────────────────────────────────

def setup_venv() -> tuple[str, str]:
    """
    Create .venv and install requirements.
    Returns (pip_path, python_path).
    """
    hdr("Setting Up Python venv")
    venv_path = Path(VENV_DIR)

    if venv_path.exists():
        ok(f"'{VENV_DIR}' already exists — skipping creation.")
    else:
        info(f"Creating virtual environment at ./{VENV_DIR} ...")
        run_cmd([sys.executable, "-m", "venv", str(venv_path)])
        ok("Virtual environment created.")

    # Paths inside venv
    if is_windows():
        pip_path    = str(venv_path / "Scripts" / "pip.exe")
        python_path = str(venv_path / "Scripts" / "python.exe")
    else:
        pip_path    = str(venv_path / "bin" / "pip")
        python_path = str(venv_path / "bin" / "python")

    if not Path(pip_path).exists():
        err(f"pip not found at {pip_path}. venv may be corrupted — delete .venv and retry.")
        sys.exit(1)

    info("Upgrading pip...")
    run_cmd([pip_path, "install", "--upgrade", "pip", "--quiet"])

    req_file = Path("requirements.txt")
    if not req_file.exists():
        err("requirements.txt not found. Run setup.py from the project root directory.")
        sys.exit(1)

    info("Installing packages from requirements.txt...")
    run_cmd([pip_path, "install", "-r", str(req_file), "--quiet"])
    ok("All dependencies installed in venv.")

    return pip_path, python_path


# ─────────────────────────────────────────────
# 4. Ollama installation
# ─────────────────────────────────────────────

def _is_ollama_installed() -> bool:
    return shutil.which("ollama") is not None


def _install_ollama_linux():
    info("Downloading Ollama Linux installer via curl...")
    try:
        run_cmd(["bash", "-c", "curl -fsSL https://ollama.com/install.sh | sh"])
        ok("Ollama installed on Linux.")
    except Exception:
        warn("curl installer failed. Attempting direct binary download...")
        binary_url = "https://github.com/ollama/ollama/releases/latest/download/ollama-linux-amd64"
        dest = Path("/usr/local/bin/ollama")
        info(f"Downloading to {dest} ...")
        urllib.request.urlretrieve(binary_url, str(dest))
        dest.chmod(0o755)
        ok("Ollama binary placed at /usr/local/bin/ollama.")


def _install_ollama_macos():
    if shutil.which("brew"):
        info("Installing Ollama via Homebrew...")
        try:
            run_cmd(["brew", "install", "ollama"])
            ok("Ollama installed via Homebrew.")
            return
        except Exception:
            warn("Homebrew install failed. Trying .zip download...")
    url  = "https://ollama.com/download/Ollama-darwin.zip"
    dest = Path.home() / "Downloads" / "Ollama-darwin.zip"
    info(f"Downloading {url} ...")
    urllib.request.urlretrieve(url, str(dest))
    ok(f"Downloaded to {dest}.")
    warn("Open the downloaded file and install Ollama, then re-run setup.py.")
    sys.exit(0)


def _install_ollama_windows():
    url  = "https://ollama.com/download/OllamaSetup.exe"
    dest = Path.home() / "Downloads" / "OllamaSetup.exe"
    info(f"Downloading Ollama installer to {dest} ...")
    urllib.request.urlretrieve(url, str(dest))
    info("Running installer (UAC prompt may appear)...")
    run_cmd(["powershell", "-Command", f"Start-Process '{dest}' -Wait"])
    ok("Ollama installation complete.")


def install_ollama():
    hdr("Checking Ollama")
    if _is_ollama_installed():
        res = run_cmd(["ollama", "--version"], capture=True, check=False)
        v   = res.stdout.strip() if res.returncode == 0 else "unknown version"
        ok(f"Ollama already installed ({v}).")
        return

    warn("Ollama not found on PATH. Installing now...")
    if is_linux():
        _install_ollama_linux()
    elif is_macos():
        _install_ollama_macos()
    elif is_windows():
        _install_ollama_windows()
    else:
        err(f"Unsupported OS: {SYSTEM}. Install manually: https://ollama.com/download")
        sys.exit(1)

    if not _is_ollama_installed():
        err("Ollama install could not be verified. Restart your terminal and re-run setup.py.")
        sys.exit(1)
    ok("Ollama ready.")


# ─────────────────────────────────────────────
# 5. Start Ollama server + pull model
# ─────────────────────────────────────────────

def _ollama_is_running() -> bool:
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=5):
            return True
    except Exception:
        return False


def _start_ollama_server():
    info("Starting Ollama server in background...")
    if is_windows():
        subprocess.Popen(
            ["ollama", "serve"],
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    for _ in range(15):
        time.sleep(1)
        if _ollama_is_running():
            ok("Ollama server started.")
            return
    err("Ollama server did not start within 15 seconds.")
    sys.exit(1)


def _is_model_pulled() -> bool:
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=10) as r:
            data   = json.loads(r.read().decode())
            models = [m.get("name", "") for m in data.get("models", [])]
            return any(MODEL in name for name in models)
    except Exception:
        return False


def pull_model():
    hdr(f"Checking AI Model: {MODEL}")

    if not _ollama_is_running():
        _start_ollama_server()

    if _is_model_pulled():
        ok(f"Model '{MODEL}' already available locally. Skipping pull.")
        return

    info(f"Pulling '{MODEL}' — this may take several minutes on first run...")
    try:
        proc = subprocess.Popen(
            ["ollama", "pull", MODEL],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        for line in proc.stdout:
            line = line.strip()
            if line:
                print(f"  {C.DIM}{line}{C.RESET}")
        proc.wait()
        if proc.returncode != 0:
            err(f"Model pull exited with code {proc.returncode}.")
            sys.exit(1)
        ok(f"Model '{MODEL}' ready.")
    except FileNotFoundError:
        err("'ollama' not found. Ensure Ollama is installed and on PATH.")
        sys.exit(1)
    except Exception as exc:
        err(f"Unexpected error during pull: {exc}")
        sys.exit(1)


# ─────────────────────────────────────────────
# 6. GPU detection
# ─────────────────────────────────────────────

def detect_hardware():
    hdr("Hardware Detection")

    if shutil.which("nvidia-smi"):
        res = run_cmd(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            capture=True, check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            info_line = res.stdout.strip().split("\n")[0]
            ok(f"NVIDIA GPU: {info_line}")
            info("Ollama will use CUDA acceleration automatically.")
            return

    if shutil.which("rocm-smi"):
        ok("AMD GPU / ROCm detected. Ollama will use ROCm if supported.")
        return

    if is_macos():
        res = run_cmd(["system_profiler", "SPDisplaysDataType"], capture=True, check=False)
        if res.returncode == 0 and "Metal" in res.stdout:
            ok("Apple Silicon / Metal GPU detected. Ollama will use Metal.")
            return

    warn("No discrete GPU detected — Ollama will run on CPU (slower).")
    info("CPU mode is fully supported.")


# ─────────────────────────────────────────────
# 7. Print activation instructions
# ─────────────────────────────────────────────

def print_activation_instructions(env_type: str):
    hdr("Setup Complete")

    if env_type == "conda":
        if is_windows():
            activate_cmd = f"conda activate {CONDA_ENV_NAME}"
        else:
            activate_cmd = f"conda activate {CONDA_ENV_NAME}"

        print(f"""
  {C.GREEN}{C.BOLD}✔  Everything is ready!{C.RESET}

  {C.CYAN}Activate your conda environment and run the app:{C.RESET}

    {C.WHITE}{activate_cmd}{C.RESET}
    {C.WHITE}python run.py{C.RESET}

  {C.DIM}Note: The conda env is named '{CONDA_ENV_NAME}'.
  Packages were installed with: conda run -n {CONDA_ENV_NAME} pip install ...
  Logs saved to: cypher_aibookgenerator.log{C.RESET}
""")
    else:
        if is_windows():
            activate_cmd = r".venv\Scripts\activate"
        else:
            activate_cmd = "source .venv/bin/activate"

        print(f"""
  {C.GREEN}{C.BOLD}✔  Everything is ready!{C.RESET}

  {C.CYAN}Activate your virtual environment and run the app:{C.RESET}

    {C.WHITE}{activate_cmd}{C.RESET}
    {C.WHITE}python run.py{C.RESET}

  {C.DIM}Logs saved to: cypher_aibookgenerator.log{C.RESET}
""")


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    print(f"\n{C.BOLD}{C.CYAN}")
    print("╔══════════════════════════════════════════════╗")
    print("║    cypher-aibookgenerator  ·  Setup v2       ║")
    print("╚══════════════════════════════════════════════╝")
    print(C.RESET)

    check_python_version()
    detect_hardware()

    # ── Ask user: conda or venv ──────────────────
    env_type = ask_env_type()

    if env_type == "conda":
        pip_path, python_path = setup_conda()
    else:
        pip_path, python_path = setup_venv()

    install_ollama()
    pull_model()
    print_activation_instructions(env_type)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{C.YELLOW}  Setup interrupted by user.{C.RESET}\n")
        sys.exit(0)