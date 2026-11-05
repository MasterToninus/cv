# Document creation years

The year prefix of existing documents in `hand-tailored/` and `old-tailored/` records the first Git introduction of that document variant. It is not the latest revision date. We follow renames (`Rxxx`) but stop at an addition (`A`) or copy (`Cxxx`), so a copied CV does not inherit its ancestor's creation year. The year comes from that introducing commit's committer timestamp; author timestamps were also checked and agree on the year for these documents.

| Current source | Year | Committer timestamp | Introducing commit | Kind |
| --- | --- | --- | --- | --- |
| [hand-tailored/2025-Cv-Giusy.tex](../hand-tailored/2025-Cv-Giusy.tex) | 2025 | `2025-10-14T12:15:24+02:00` | `070de0acf354296437a58e17aa76ac4c91bd5275` | `A` |
| [hand-tailored/2026-Selected-Publications-Commented.tex](../hand-tailored/2026-Selected-Publications-Commented.tex) | 2026 | `2026-09-04T13:22:19+02:00` | `170c2d601f64e26bc6965001d5c32f4ae8e40164` | `A` |
| [hand-tailored/2025-Selected-Publications.tex](../hand-tailored/2025-Selected-Publications.tex) | 2025 | `2025-08-28T18:24:31+02:00` | `7e6d7dcd9b49b9a42bb070effe6253c392130255` | `C057` |
| [old-tailored/2020-All-Publications.tex](../old-tailored/2020-All-Publications.tex) | 2020 | `2020-11-07T18:29:01+01:00` | `72a851ce994c85409ce451d9374ded8345528a84` | `A` |
| [old-tailored/2025-Cv-1Page.tex](../old-tailored/2025-Cv-1Page.tex) | 2025 | `2025-03-31T11:38:43+02:00` | `766fc754debb9c7bc1150355cee7d395b12fdb28` | `A` |
| [old-tailored/2025-Cv-AleStyle.tex](../old-tailored/2025-Cv-AleStyle.tex) | 2025 | `2025-01-07T14:07:09+01:00` | `69b97a905ab3ff6908535f16529219ac8ecbb45e` | `A` |
| [old-tailored/2025-Cv-Dossier-Publications.tex](../old-tailored/2025-Cv-Dossier-Publications.tex) | 2025 | `2025-04-09T15:18:03+02:00` | `df5851c44f10dfce1800e2e480593e03de829b86` | `C098` |
| [old-tailored/2024-Cv-FR.tex](../old-tailored/2024-Cv-FR.tex) | 2024 | `2024-03-19T12:51:52+01:00` | `a8d855c122fad54aacce5de0e7d2e49e7c5c05b0` | `A` |
| [old-tailored/2021-Cv-Tony-Industry.tex](../old-tailored/2021-Cv-Tony-Industry.tex) | 2021 | `2021-06-14T11:02:22+02:00` | `6c2f4f0fdc5a74d5daa15ab836fef09f4c500aee` | `A` |
| [old-tailored/mcf-temp/2026-Bibliography-New.bib](../old-tailored/mcf-temp/2026-Bibliography-New.bib) | 2026 | `2026-04-02T23:20:17+02:00` | `f309c4896d309740f72d9f3410ec91d34b869db2` | `A` |
| [old-tailored/mcf-temp/2026-Bibliography-Old.bib](../old-tailored/mcf-temp/2026-Bibliography-Old.bib) | 2026 | `2026-04-02T23:20:17+02:00` | `f309c4896d309740f72d9f3410ec91d34b869db2` | `A` |
| [old-tailored/mcf-temp/2026-Cv-Analytical-MCF.tex](../old-tailored/mcf-temp/2026-Cv-Analytical-MCF.tex) | 2026 | `2026-04-02T19:28:45+02:00` | `7923b19c56a3e8d0560274728765234934d5b2a2` | `C064` |
| [old-tailored/2024-Teaching.tex](../old-tailored/2024-Teaching.tex) | 2024 | `2024-11-13T16:11:12+01:00` | `a4a33a7b4c8c59a63a32782166b0df1e18ecc54b` | `A` |
| [old-tailored/2025-Titoli.tex](../old-tailored/2025-Titoli.tex) | 2025 | `2025-07-05T20:46:42+02:00` | `6d378b9e60de4eb9b3d5a8a232c6fed3ddb0d1ef` | `A` |

At the naming review on 4 November 2026, `old-tailored/2027-Cv-Tony-ERC.tex` had no Git introduction from which to derive a year. Its `2027` prefix was therefore retained as an explicit call-year exception. The source was subsequently introduced in commit `f5051eeb2ee050c51544c7b4377d4349a8b0aec2` on 4 November 2026 (`2026-11-04T22:16:35+01:00`). The filename continues to identify the call rather than a Git-derived year; the extracted CV body remains verbatim.

README files, generated auxiliaries and build directories are not dated documents. The MCF bibliography sources have their own first-introduction prefixes and the TeX resource references were updated accordingly.

[Documentation index](README.md)
