"""
processors.py
Ollama communication layer — all API calls to the local Ollama runtime.
"""

import json
import logging
import subprocess
import sys
import time
from typing import Iterator

import requests

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "llama3.2:3b"
REQUEST_TIMEOUT = 300  # seconds per generation request


# ─────────────────────────────────────────────
# Ollama runtime management
# ─────────────────────────────────────────────

def is_ollama_running() -> bool:
    """Check whether the Ollama HTTP server is reachable."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return resp.status_code == 200
    except requests.exceptions.ConnectionError:
        return False
    except Exception as exc:
        logger.debug("Unexpected error checking Ollama: %s", exc)
        return False


def start_ollama() -> bool:
    """
    Attempt to start the Ollama server as a background process.
    Returns True if successfully started within 15 seconds.
    """
    logger.info("Attempting to start Ollama server...")
    try:
        if sys.platform == "win32":
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
    except FileNotFoundError:
        logger.error("Ollama executable not found. Please run setup.py first.")
        return False
    except Exception as exc:
        logger.error("Failed to start Ollama: %s", exc)
        return False

    # Wait for server to become available
    for attempt in range(15):
        time.sleep(1)
        if is_ollama_running():
            logger.info("Ollama server started successfully.")
            return True

    logger.error("Ollama server did not start within 15 seconds.")
    return False


def ensure_ollama_running() -> bool:
    """Ensure Ollama is running; start it if necessary."""
    if is_ollama_running():
        logger.info("Ollama server is already running.")
        return True
    return start_ollama()


# ─────────────────────────────────────────────
# Model management
# ─────────────────────────────────────────────

def is_model_available() -> bool:
    """Check whether llama3.2:3b is already pulled locally."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        if resp.status_code != 200:
            return False
        data = resp.json()
        models = [m.get("name", "") for m in data.get("models", [])]
        # Accept both "llama3.2:3b" and "llama3.2:3b-instruct-..."
        return any(MODEL_NAME in name for name in models)
    except Exception as exc:
        logger.debug("Error checking model availability: %s", exc)
        return False


def pull_model(progress_callback=None) -> bool:
    """
    Pull llama3.2:3b from the Ollama registry.
    progress_callback(status_str) is called with progress updates if provided.
    """
    logger.info("Pulling model %s ...", MODEL_NAME)
    try:
        with requests.post(
            f"{OLLAMA_BASE_URL}/api/pull",
            json={"name": MODEL_NAME, "stream": True},
            stream=True,
            timeout=600,
        ) as resp:
            if resp.status_code != 200:
                logger.error("Pull request failed with status %d", resp.status_code)
                return False

            for raw_line in resp.iter_lines():
                if not raw_line:
                    continue
                try:
                    chunk = json.loads(raw_line)
                    status = chunk.get("status", "")
                    if progress_callback:
                        progress_callback(status)
                    if chunk.get("error"):
                        logger.error("Pull error: %s", chunk["error"])
                        return False
                    if status == "success":
                        logger.info("Model pull complete.")
                        return True
                except json.JSONDecodeError:
                    continue

        # If stream ended without "success" status, check availability
        return is_model_available()

    except Exception as exc:
        logger.error("Exception during model pull: %s", exc)
        return False


def ensure_model_available(progress_callback=None) -> bool:
    """Ensure llama3.2:3b is available; pull only if missing."""
    if is_model_available():
        logger.info("Model %s is already available.", MODEL_NAME)
        return True
    logger.info("Model %s not found locally. Pulling now...", MODEL_NAME)
    return pull_model(progress_callback)


# ─────────────────────────────────────────────
# Text generation
# ─────────────────────────────────────────────

def generate_text(prompt: str, temperature: float = 0.7, stream_callback=None) -> str:
    """
    Send a prompt to llama3.2:3b and return the full generated text.
    Optionally streams tokens to stream_callback(token: str).
    """
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": temperature,
            "num_predict": 2048,
            "top_p": 0.9,
            "repeat_penalty": 1.1,
        },
    }

    full_response = []

    try:
        with requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            stream=True,
            timeout=REQUEST_TIMEOUT,
        ) as resp:
            if resp.status_code != 200:
                raise RuntimeError(
                    f"Ollama generation failed with HTTP {resp.status_code}: {resp.text[:200]}"
                )

            for raw_line in resp.iter_lines():
                if not raw_line:
                    continue
                try:
                    chunk = json.loads(raw_line)

                    if chunk.get("error"):
                        raise RuntimeError(f"Ollama error: {chunk['error']}")

                    token = chunk.get("response", "")
                    if token:
                        full_response.append(token)
                        if stream_callback:
                            stream_callback(token)

                    if chunk.get("done", False):
                        break

                except json.JSONDecodeError as exc:
                    logger.debug("JSON decode error on chunk: %s", exc)
                    continue

    except requests.exceptions.Timeout:
        logger.error("Generation request timed out after %d seconds.", REQUEST_TIMEOUT)
        raise RuntimeError("Generation timed out. The model may be overloaded.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Cannot connect to Ollama. Is it still running?")

    return "".join(full_response)


def detect_gpu() -> dict:
    """
    Detect GPU availability for informational purposes.
    Ollama handles GPU/CPU selection automatically; this is for display only.
    """
    info = {"has_gpu": False, "gpu_name": "None", "backend": "CPU"}

    try:
        # Try nvidia-smi
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            info["has_gpu"] = True
            info["gpu_name"] = result.stdout.strip().split("\n")[0]
            info["backend"] = "CUDA (NVIDIA GPU)"
            return info
    except Exception:
        pass

    try:
        # Try rocm-smi (AMD)
        result = subprocess.run(
            ["rocm-smi", "--showproductname"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            info["has_gpu"] = True
            info["gpu_name"] = "AMD GPU"
            info["backend"] = "ROCm (AMD GPU)"
            return info
    except Exception:
        pass

    try:
        # macOS Metal check
        import platform
        if platform.system() == "Darwin":
            result = subprocess.run(
                ["system_profiler", "SPDisplaysDataType"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if "Metal" in result.stdout:
                info["has_gpu"] = True
                info["gpu_name"] = "Apple Silicon / Metal GPU"
                info["backend"] = "Metal (Apple GPU)"
                return info
    except Exception:
        pass

    return info