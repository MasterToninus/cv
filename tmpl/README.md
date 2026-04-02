# CV Templates

This folder contains the template files used by the script.



## LaTeX Templates Documentation

### `section_tmpl.tex`
This template renders individual sections of the CV, such as "Education," "Work Experience," or "Publications."

#### Features
- **Customizable Section Headers**: Dynamically inserts section titles.
- **Flexible Layout**: Supports list and table formats.
- **LaTeX Compatibility**: Escapes special characters.

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

### `home_tmpl.tex`
This template creates the main structure of the CV, including metadata, a cover statement, and a three-column layout.

#### Features
- **Dynamic Metadata**: Automatically fills in name, contact details, and links.
- **Three-Column Layout**: Organizes CV sections across three columns.
- **Customizable Keywords**: Includes keywords for emphasis.

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
