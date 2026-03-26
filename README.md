<!-- markdownlint-disable MD033 -->
<h1 align="center">
  Cypher AI Book Generator
</h1>

<p align="center">
  <strong>📖 AI-Powered Book Writing Assistant</strong><br>
  Generate professional books with a single prompt using local LLMs.
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#genres">Genres</a> •
  <a href="#tech-stack">Tech Stack</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#project-structure">Structure</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10-blue.svg" alt="Python 3.10">
  <img src="https://img.shields.io/badge/ollama-llama3.2:3b-green" alt="Ollama">
  <img src="https://img.shields.io/badge/license-MIT-yellow.svg" alt="License">
  <img src="https://img.shields.io/badge/environment-venv%20%7C%20conda-blue" alt="Environment">
</p>

---

## ✨ Features

- 🧠 **Local & Private** – Runs entirely on your machine – no API keys, no data sent to the cloud.
- 📚 **Intelligent Book Generation** – Creates coherent, well-structured books using **Llama 3.2:3b** via Ollama.
- 🎨 **Genre Support** – Choose from **27+ genres** to tailor the narrative style and content.
- 💻 **Cross‑Platform** – Works on Windows, macOS, and Linux with automatic GPU detection.
- 📄 **Professional Output** – Generates polished PDF or DOCX files with proper formatting.
- 🎛️ **Interactive CLI** – Rich, user‑friendly interface with colored prompts and validation.
- ⚙️ **One‑Click Setup** – Automated environment creation using **venv** or **conda**.
- 🔧 **Modular Architecture** – Easy to extend and maintain.

---

## 🎭 Genres

The generator can adapt to any of the following genres (select from the interactive list):

<details>
<summary><strong>Click to expand genre list</strong></summary>

| Genre                | Genre                | Genre                |
|----------------------|----------------------|----------------------|
| Horror               | Sci Fi               | Philosophical        |
| Documentary          | Dark Romance         | Romance              |
| Fantasy              | Comedy               | Sad                  |
| Love Stories         | Love and Drama       | Adventure and Power  |
| Historical           | Fiction              | Murder Mystery       |
| Mystery              | Thriller             | Historical Fiction   |
| Young Adult          | Literary Fiction     | Memoir / Auto Biography |
| Biography            | Self Help            | True Crime           |
| Dystopian            | Paranormal Activity  | Paranormal Romance   |
| Investigative Journalism |                    |                      |

</details>

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

- **Python 3.10** or higher
- **Git** (optional, for cloning)
- **Internet connection** (to download model and dependencies)

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/cypher-aibookgenerator.git
cd cypher-aibookgenerator
```

### Step 2: Run the Setup Script

The setup script automates everything:

```bash
python setup.py
```

You will be prompted to choose your preferred environment:

- **`venv`** – standard Python virtual environment
- **`conda`** – if you have Anaconda/Miniconda installed

The script will then:

- Create and activate the chosen environment
- Install all Python dependencies from `requirements.txt`
- Check for Ollama installation and install it if missing (cross‑platform)
- Pull the `llama3.2:3b` model if not already present
- Start the Ollama server (if not running)

**Note:** On Windows, the Ollama installer may require administrator privileges. If the automatic installation fails, please install Ollama manually from [ollama.com](https://ollama.com) and run `python setup.py` again.

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
├── generation.py          # Book generation logic (includes genre handling)
├── output.py              # Output routing
├── output_pdf.py          # PDF generation
├── output_docx.py         # DOCX generation
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

---

## 🧪 Requirements

All Python dependencies are listed in `requirements.txt` and are installed automatically:

- `rich` – beautiful CLI formatting
- `colorama` – cross‑platform colored output
- `requests` – HTTP calls to Ollama
- `python-docx` – DOCX creation
- `reportlab` – PDF generation
- `psutil` – system utilities

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/amazing-feature`.
3. Commit your changes: `git commit -m 'Add some amazing feature'`.
4. Push to the branch: `git push origin feature/amazing-feature`.
5. Open a Pull Request.

Make sure to adhere to the existing code style and include tests if applicable.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 🙏 Acknowledgements

- [Ollama](https://ollama.com) – for making local LLMs accessible.
- [Meta AI](https://ai.meta.com/llama/) – for the Llama 3.2 models.
- All open‑source libraries that made this project possible.

---

<p align="center">
  Made with ❤️ by the Cypher AI team.
</p>
