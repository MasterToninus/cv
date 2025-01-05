# LaTeX CV Generator

A customizable, data-driven LaTeX CV generator built with Python and Jinja2. This project streamlines CV creation by combining structured data sources with LaTeX templates to produce a professional, dynamic CV.

- [Link to my Cv](https://www.dropbox.com/scl/fi/fy1xy3re0xixm8ejwhitt/cv.pdf?rlkey=jtdw6jw8bmh3ctr7u0xwj0kzh&dl=0)

---

## Features
- **Dynamic Content Integration**: Automatically updates activities from online CSV files and integrates publication data from BibTeX files.
- **Web Scraping**: Fetches author information and metrics from Scopus using the pybliometrics API.
- **Customizable Layout**: Multi-column LaTeX templates powered by Jinja2.
- **Automation**: Simple `make` command compiles everything into a polished PDF.
- **Extensible**: Easily add new sections or customize templates to suit your needs.

---

## Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/username/latex-cv-generator.git
    cd latex-cv-generator
    ```

2. **Install the required Python packages**:
    ```bash
    pip3 install -r requirements.txt
    ```

    The `requirements.txt` file includes:
    - `pyyaml>=5.4`
    - `Jinja2>=3.1.4`
    - `pybtex>=0.24.0,<1.0`
    - `pybliometrics>=3.4.0`

3. **Configure pybliometrics**:
    Follow the instructions in the [pybliometrics documentation](https://pybliometrics.readthedocs.io/en/stable/configuration.html) to set up your API key.

4. **Prepare your data**:
    - Edit `data/cv.yaml` with your personal details, sections, and layout.
    - Place your publications in `data/publications.bib`.
    - Host your activities CSV file online or adjust the URL in `getactivities.py`.

---

## Folder Structure

```
latex-cv-generator/
├── data/
│   ├── cv.yaml
│   ├── publications.bib
├── gen/
│   ├── cv.pdf
├── tmpl/
│   ├── home_tmpl.tex
│   ├── section_tmpl.tex
├── getactivities.py
├── Makefile
├── README.md
├── requirements.txt
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
Perspective features:
- [ ] Add ATS-friendly formatting.
- [ ] Develop a localized Italian version.
- [x] Introduce summary tables for teaching and other activities.
    - [x] Publications: published, preprints, in preparations
    - [x] Dissemination: invited, contributed, posters, organizations
    - [x] Teaching: corsi, ore di frontale
    - [ ] Others: supervised students, citations, h-index, referee reports, research stay,commitees/jury
- [ ] Autogenerate `publications.tex` from the BibTeX file with a CV-compatible style, import as a standalone in `gen`.
- [x] Create a splashpage with "at glance" numeric information.
    - [x] Move affiliation and awards.
- [x] Suitable entry for career break 2010-2013.
- [ ] Scrape bibliometrics through APIs.
    - [ ] Scopus
    - [ ] Researchgate: https://laccei.org/LEIRD2024-VirtualEdition/papers/Contribution_721_a.pdf
- [ ] [Secret](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions) with signatures and phone number (Italy format) 
- [ ] [Github action](https://github.com/marketplace/actions/github-action-for-latex) to generate last version

Suggestions:
- Remove "departmental duties"
- Remove the meaningless, keep the meaningful. (e.g. don't need to specify KU Leuven, Leuven, Belgium.)




---

## Acknowledgments
- Early versions due to [VittorioErba](https://github.com/vittorioerba).
- Inspired by [bamos/cv](https://github.com/bamos/cv).
- Thanks to **ChatGPT** for helping to improve the project documentation and providing suggestions for better code structuring.

---

## Troubleshooting

### Scopus 401 Error

If you encounter the following error:
```
pybliometrics.scopus.exception.Scopus401Error: The requestor is not authorized to access the requested view or fields of the resource
```
This indicates that the API key you are using does not have the necessary permissions to access the requested data from Scopus.

To resolve this issue, follow these steps:

1. **Verify API Key**:
   Ensure that you have a valid API key from Scopus. You can obtain an API key by registering on the [Elsevier Developer Portal](https://dev.elsevier.com/).

2. **Check API Key Permissions**:
   Make sure that your API key has the necessary permissions to access the Scopus data. Some API keys may have restricted access based on the subscription level.

3. **Configure pybliometrics**:
   Ensure that you have correctly configured `pybliometrics` with your API key. You can do this by creating a configuration file as described in the [pybliometrics documentation](https://pybliometrics.readthedocs.io/en/stable/configuration.html).

   Here is an example of how to configure `pybliometrics`:

   - Create a file named `config.ini` in the `.pybliometrics` directory in your home directory.
   - Add the following content to the `config.ini` file:

     ```ini
     [Authentication]
     API_KEY = your_api_key_here
     ```

4. **Check API Usage Limits**:
   Ensure that you have not exceeded the usage limits for your API key. The Scopus API has rate limits, and exceeding these limits can result in authorization errors.

5. **Test API Key**:
   Test your API key with a simple request to ensure that it is working correctly. You can use the following code snippet to test your API key:

   ```python
   from pybliometrics.scopus import AuthorRetrieval

   author_id = '57218509273'
   author = AuthorRetrieval(author_id)
   print(author.given_name, author.surname)
   ```

If you have verified all the above steps and are still encountering the error, you may need to contact Elsevier support for further assistance with your API key and permissions.

For more detailed information, refer to the [pybliometrics access documentation](https://pybliometrics.readthedocs.io/en/stable/access.html).

---
