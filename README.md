# LaTeX CV Generator

A customizable, data-driven LaTeX CV generator built with Python and Jinja2. This project streamlines CV creation by combining structured data sources with LaTeX templates to produce a professional, dynamic CV.

---

## Features
- **Dynamic Content Integration**:
  - Automatically updates activities from online CSV files.
  - Parses and integrates publication data from BibTeX files.
- **Customizable Layout**:
  - Multi-column LaTeX templates powered by Jinja2.
- **Automation**:
  - Simple `make` command compiles everything into a polished PDF.
- **Extensible**:
  - Easily add new sections or customize templates to suit your needs.

---

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/username/latex-cv-generator.git
    cd latex-cv-generator
    ```

2. Install the required Python packages:
    ```bash
    pip3 install -r requirements.txt
    ```

3. Prepare your data:
    - Edit `data/cv.yaml` with your personal details, sections, and layout.
    - Place your publications in `data/publications.bib`.
    - Host your activities CSV file online or adjust the URL in `getactivities.py`.

s---

## LaTeX Templates Documentation

### **`section_tmpl.tex`**
This template renders individual sections of the CV, such as "Education," "Work Experience," or "Publications."

#### Features
- **Customizable Section Headers**: Dynamically inserts section titles.
- **Flexible Layout**: Supports list and table formats.
- **LaTeX Compatibility**: Escapes special characters.

#### Template Usage
The template uses placeholders for:
- `name`: Title of the section.
- `contents`: Items to display in the section.
- `kind`: Determines the layout ("list" or "table").

#### Example Snippet
```tex
\section*{~{{ name }}~}
\ifx~{{ kind }}~list
    \begin{itemize}
        ~{%- for item in contents %}
        \item ~{{ item }}
        ~{%- endfor %}
    \end{itemize}
\else
    \begin{tabularx}{\textwidth}{X r}
        ~{%- for row in contents %}
        ~{{ row[0] }} & ~{{ row[1] }} \\
        ~{%- endfor %}
    \end{tabularx}
\fi
```

---

### **`home_tmpl.tex`**
This template creates the main structure of the CV, including metadata, a cover statement, and a three-column layout.

#### Features
- **Dynamic Metadata**: Automatically fills in name, contact details, and links.
- **Three-Column Layout**: Organizes CV sections across three columns.
- **Customizable Keywords**: Includes keywords for emphasis.

#### Template Usage
The template uses placeholders for:
- `name`: Candidate's name.
- `phone`, `email`, `site`, `github`: Contact information.
- `currentposition`: Current job/academic position.
- `coverstatement`: Introductory statement.
- `body1`, `body2`, `body3`: Content for each column.

#### Example Snippet
```tex
\documentclass[10pt]{article}
\usepackage{geometry, xcolor, hyperref}

\begin{document}
\begin{center}
    {\LARGE ~{{ name }}~}\\[0.2cm]
    \textbf{~{{ currentposition }}~}\\[0.2cm]
    \href{mailto:~{{ email }}~}{~{{ email }}~} | 
    ~{{ phone }}~ | 
    \href{~{{ site }}~}{~{{ site }}~} | 
    \href{https://github.com/~{{ github }}~}{~{{ github }}~}
\end{center}

\vspace{1cm}

~{{ coverstatement }}~

\columnbreak

~{{ body1 }}~
\columnbreak

~{{ body2 }}~
\columnbreak

~{{ body3 }}~
\end{document}
```

---

## Usage

1. **Generate the CV**:
    Run the Makefile to process your data and generate a LaTeX CV:
    ```bash
    make
    ```

2. **View the Output**:
    - The compiled PDF will be available in the `gen/` directory:
      ```bash
      open gen/cv.pdf
      ```

---

## Roadmap
- Improve readability and speed of the generated CV.
- Add ATS-friendly formatting.
- Develop a localized Italian version.
- Introduce summary tables for teaching and other activities.
- Autogenerate `publications.tex` from the BibTeX file with a CV-compatible style.

---

## Acknowledgments
- Inspired by [bamos/cv](https://github.com/bamos/cv). Special thanks for sharing the inspiration for this project.
- Thanks to **ChatGPT** for helping to improve the project documentation and providing suggestions for better code structuring and clarity.

---
