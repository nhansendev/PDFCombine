# PDFCombine
A python 3 utility for automatically combining and trimming PDF files 

# Main Functions
## Combine PDFs
Stack multiple PDFs together into one large PDF

![image](https://github.com/nhansendev/PDFCombine/assets/9289200/bceb61f2-4b9c-4887-9ab3-eacad7a01e85)

## Combine Pages
Stack multiple pages (configurable) onto one page to reduce page count and make printing easier

![image](https://github.com/nhansendev/PDFCombine/assets/9289200/942e4f7f-f51d-4f08-b272-54e12345cad4)

## Trim PDFs
Remove pages using manually defined page ranges, and/or by auto-recognizing the References page of scientific papers

![image](https://github.com/nhansendev/PDFCombine/assets/9289200/a170d398-88d4-4c7c-a5b1-de9716197e9f)

# Requirements:
  Python 3.11

    pip install -r requirements.txt
    
- pdfrw
- pdfplumber

# Usage
## Terminal
    python CombinePDFs.py <directory with PDFs> <new filename> <pages per page> ... (other args shown below)

## In Python
    from CombinePDFs import combine_pdfs

    # default kwargs shown
    combine_pdfs(
        path,
        new_filename="combined.pdf", 
        pages_per_page=4,   # can be any integer >= 1
        subset=None,        # which specific PDFs in the directory should be combined?
        exclude=None,       # which specific PDFs in the directory should be ignored?
        page_subsets=None,  # in the same order that the PDFs are found, list their page ranges to use
        remove_refs=True,   # try to automatically find and remove all pages after the "References" page
        scaler=0.92,        # sets the spacing between PDFs on the same page
        verbose=True, 
    )
    
