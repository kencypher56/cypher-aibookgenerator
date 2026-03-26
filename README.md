We'll now create a comprehensive `README.md` that includes HTML and icons, describes the updated features (genre selection, conda/venv setup), and serves as a complete guide for the project.

---

## `README.md`

```html
<!-- markdownlint-disable MD033 -->
<h1 align="center">
  <img src="https://raw.githubusercontent.com/yourusername/cypher-aibookgenerator/main/assets/logo.png" width="80" alt="Cypher AI Book Generator Logo"><br>
  Cypher AI Book Generator
</h1>

<p align="center">
  <strong>AI-Powered Book Writing Assistant</strong><br>
  Generate professional books with a single prompt using local LLMs.
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#tech-stack">Tech Stack</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#project-structure">Project Structure</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10-blue.svg" alt="Python 3.10">
  <img src="https://img.shields.io/badge/ollama-llama3.2:3b-green" alt="Ollama">
  <img src="https://img.shields.io/badge/license-MIT-yellow.svg" alt="License">
</p>

---

## ✨ Features

- 📖 **Intelligent Book Generation** – Creates coherent, well-structured books using **Llama 3.2:3b** via Ollama.
- 🎨 **Genre Support** – Choose from 27+ genres to tailor the narrative style and content.
- 🧠 **Local & Private** – Runs entirely on your machine – no API keys, no data sent to the cloud.
- 💻 **Cross‑Platform** – Works on Windows, macOS, and Linux (CPU or GPU).
- 📄 **Professional Output** – Generates polished PDF or DOCX files with proper formatting.
- 🎛️ **Interactive CLI** – Rich, user‑friendly interface with colored prompts and validation.
- ⚙️ **One‑Click Setup** – Automated environment creation using `venv` or `conda`.
- 🔧 **Modular Architecture** – Easy to extend and maintain.

---

## 🛠️ Tech Stack

| Component          | Technology                         |
|--------------------|------------------------------------|
| Language           | Python 3.10                        |
| LLM Runtime        | [Ollama](https://ollama.com)       |
| Model              | `llama3.2:3b`                      |
| PDF Generation     | ReportLab                          |
| DOCX Generation    | python-docx                        |
| CLI                | Rich, Colorama                     |
| Environment        | venv / conda (user choice)         |

---

## 🚀 Installation

### Prerequisites

- Python 3.10 or higher
- [Ollama](https://ollama.com/download) (will be installed automatically if missing)
- [Git](https://git-scm.com/) (optional, for cloning)

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/cypher-aibookgenerator.git
cd cypher-aibookgenerator
```

### Step 2: Run the Setup Script

The setup script handles everything:

```bash
python setup.py
```

You will be asked to choose between **venv** (virtual environment) or **conda** (Anaconda/Miniconda).  
The script will:

- Create the chosen environment.
- Install all Python dependencies.
- Install Ollama (if not present).
- Pull the required model (`llama3.2:3b`).
- Start the Ollama server (if not running).

After successful setup, you're ready to generate books!

---

## 📖 Usage

Run the generator:

```bash
python run.py
```

Follow the interactive prompts:

1. **Book title**
2. **Author name**
3. **Genre** – choose from the list (e.g., Horror, Sci‑Fi, Romance, etc.)
4. **Book prompt** – up to 5000 characters, describing the story/theme.
5. **Chapter handling** – either provide chapter names or let the AI generate them automatically.
6. **Output format** – PDF or DOCX.

The generated book will be saved to your **Desktop** with the filename `<BookTitle>.<format>`.

### Example Session

```text
📘 Cypher AI Book Generator
Welcome! Let's create a professional book using AI.

Book title: The Quantum Garden
Author name: Jane Doe
Genre: Sci Fi
Prompt: A botanist discovers a garden that exists in multiple quantum states...
Number of chapters: 5
Output format: PDF

✨ Generating your book... This may take a few minutes.
✓ Book generated successfully! Saved to Desktop.
```

---

## 📁 Project Structure

```
cypher-aibookgenerator/
├── run.py                 # Entry point
├── setup.py               # Environment setup (venv/conda)
├── cli.py                 # Interactive CLI interface
├── prompt_processing.py   # Input sanitization & validation
├── processors.py          # Ollama communication layer
├── generation.py          # Book generation logic
├── output.py              # Output routing
├── output_pdf.py          # PDF generation
├── output_docx.py         # DOCX generation
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

---

## 🧪 Requirements

All Python dependencies are listed in `requirements.txt`:

- `rich` – beautiful CLI formatting
- `colorama` – cross‑platform colored output
- `requests` – HTTP calls to Ollama
- `python-docx` – DOCX creation
- `reportlab` – PDF generation
- `psutil` – system utilities

These are installed automatically by the setup script.

---

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request.  
Make sure to follow the existing code style and add tests for new features.

---

## 📄 License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- [Ollama](https://ollama.com) for the amazing local LLM runtime.
- [Meta AI](https://ai.meta.com/llama/) for the Llama 3.2 models.
- The open‑source Python libraries that made this project possible.

---

<p align="center">
  Made with ❤️ by the Cypher AI team.
</p>
```