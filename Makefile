# Makefile for compiling LaTeX CV
# Usage:
#   make       - Compile the CV
#   make clean - Remove generated files

# Default target to generate the PDF
all: gen/cv.pdf

# Clean target to remove generated files
clean: 
	rm -r gen/*

# Target to generate the LaTeX file from the YAML data
gen/cv.tex: data/cv.yaml generate.py \
	tmpl/home_tmpl.tex tmpl/section_tmpl.tex
	./generate.py

# Target to compile the LaTeX file to PDF
gen/cv.pdf: gen/cv.tex
	cd gen && \
	latexmk cv.tex -interaction=batchmode && \
	biber cv && \
	latexmk cv.tex -interaction=batchmode && \
	latexmk cv.tex -interaction=batchmode
