# AI Quiz Generator

![AI Quiz Generator](https://img.shields.io/badge/AI-Quiz%20Generator-blueviolet?style=for-the-badge&logo=appveyor)

## Overview

AI Quiz Generator is a powerful and user-friendly web application that leverages advanced AI models to generate custom quizzes on any topic. Whether you want to create multiple-choice questions, true/false quizzes, or short answer tests, this app has you covered. It supports multiple languages and allows quiz generation from both user input topics and PDF documents.

Built with Streamlit and Groq LLM, this app offers an interactive experience to create, play, and download quizzes with ease.

---

## Features

- Generate quizzes on any topic using AI-powered language models.
- Supports multiple question types: Multiple Choice (MCQ), True/False, and Short Answer.
- Multilingual support with over 15 languages including English, French, Japanese, Arabic, Hindi, and more.
- PDF-based quiz generation: upload your own PDF documents and generate quizzes based on the content.
- Play saved quizzes with instant scoring and detailed feedback.
- Download quizzes as professionally formatted PDF files with or without answers.
- Intuitive and modern user interface powered by Streamlit.
- Session state management for seamless user experience.

---

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd AI_Quiz_genrator
```

2. Create and activate a virtual environment (optional but recommended):

```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. Install the required dependencies:

```bash
pip install -r requirement.txt
```

4. Set up environment variables:

Create a `.env` file in the project root and add your Groq API key:

```
GROQ_API_KEY=your_groq_api_key_here
```

---

## Usage

Run the Streamlit app:

```bash
streamlit run streamlit.py
```

The app opens in your default web browser. Use the sidebar to navigate between modes:

### Modes

- **Generate Quiz**: Create quizzes by specifying topic, difficulty, language, question type, and number of questions.
- **PDF-Based Quiz**: Upload a PDF document and generate quizzes based on its content using Retrieval-Augmented Generation (RAG).
- **Play Quiz**: Play saved quizzes, answer questions, and get instant scoring with feedback.

### Quiz Interaction

- Generate quizzes instantly using AI.
- Preview quizzes before playing or downloading.
- Download quizzes as PDF files with options to include answers.
- Play quizzes online with interactive question answering.

---

## Project Structure

- `Main.py`: Core quiz generation logic using Groq LLM.
- `streamlit.py`: Streamlit app providing the user interface and interaction.
- `pdf_rag_utils.py`: Utilities for PDF text extraction, vector store creation, and RAG-based quiz generation.
- `pdf_utils.py`: Utilities for generating downloadable PDF quiz files and buttons.
- `requirement.txt`: Python dependencies.
- `.gitignore`: Git ignore rules.

---

## Dependencies

Key dependencies include:

- Streamlit
- Langchain and related packages
- Groq LLM SDK
- PyMuPDF (fitz)
- FAISS for vector search
- ReportLab for PDF generation
- python-dotenv for environment variable management

Refer to `requirement.txt` for the full list.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- Powered by Groq LLM and Langchain.
- PDF processing with PyMuPDF and FAISS.
- PDF generation with ReportLab.
- Built with Streamlit for rapid web app development.

---

## Contact

For questions or feedback, please open an issue or contact the maintainer.

---

*Thank you for using AI Quiz Generator!*
