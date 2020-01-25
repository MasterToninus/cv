all: gen/cv.pdf

clean: 
	rm -r gen/*

gen/cv.tex: data/cv.yaml generate.py \
	tmpl/home_tmpl.tex tmpl/section_tmpl.tex
	./generate.py

gen/cv.pdf: gen/cv.tex
	cd gen && \
	pdflatex.exe cv -interaction=batchmode && \
	bibtex cv && \
	pdflatex.exe cv -interaction=batchmode
