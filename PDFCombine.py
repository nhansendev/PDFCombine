import os
from pdfrw import PdfReader, PdfWriter, PageMerge
import pdfplumber
from multiprocessing import Pool
from functools import partial
import math


ENDSTRINGS = ["Referen", "Bibliog", "Acknowl"]


def calc_best_packing(t, A=8.5, B=11):
    R = A / B

    options = []
    for n in range(1, t + 1):
        m = math.ceil(t / n)

        # 90 deg, short edge
        C = B / n
        D = C / R
        if D * m <= A:
            options.append(["1", n, m, C * D, C, D])

        # 0 deg, short edge
        D = B / n
        C = D * R
        if C * m <= A:
            options.append(["2", n, m, C * D, C, D])

        # 0 deg, long edge
        C = A / m
        D = C / R
        if D * n <= B:
            options.append(["3", n, m, C * D, C, D])

        # 90 deg, long edge
        D = A / m
        C = D * R
        if C * n <= B:
            options.append(["4", n, m, C * D, C, D])

    options.sort(key=lambda x: x[3], reverse=True)

    return options


def get_ref_page(path, file, verbose=True):
    ESCAP = [S.upper() for S in ENDSTRINGS]
    ESLOW = [S.lower() for S in ENDSTRINGS]
    found = False
    with pdfplumber.open(os.path.join(path, file)) as pdf:
        for page in pdf.pages:
            if page.page_number >= 5:
                line = ""
                for c in page.chars:
                    # Only use "normal" characters
                    if len(c["text"]) == 1:
                        line += c["text"]
                        # Moving text window
                        if len(line) > 7:
                            line = line[-7:]
                        if line in ENDSTRINGS or line in ESCAP or line in ESLOW:
                            found = True
                            if verbose:
                                print(f'{file}: Page {page.page_number}, "{line}"')
                            return page.page_number
    if not found:
        if verbose:
            print(f"{file}: NOT FOUND")
        # Return a large number representing the last page
        return 100000


def combine_pdfs(
    path,
    new_filename="combined.pdf",
    subset=None,
    exclude=None,
    page_subsets=None,
    remove_refs=True,
    pages_per_page=4,
    scaler=0.92,
    verbose=True,
):
    if subset is not None and len(subset) == 1:
        new_filename = "summarized_" + subset[0]

    files = [
        f
        for f in os.listdir(path)
        if ".pdf" in f
        and (subset is None or f in subset)
        and (exclude is None or f not in exclude)
    ]
    if verbose:
        print(f"> Found {len(files)} files to combine...\n")

    # Search for the References section of the paper(s) and get the first page number of that section
    # This will be the last page that we include
    reference_pages = None
    if remove_refs:
        if verbose:
            print("> Searching for ENDSTRINGS...")
        grf = partial(get_ref_page, path, verbose=verbose)
        pool = Pool()
        reference_pages = pool.map(grf, files)
        pool.close()

    # Collect pages, excluding references and including subsets, if defined
    total_pages = 0
    pages = []
    for idx, f in enumerate(files):
        temp = PdfReader(os.path.join(path, f)).pages
        total_pages += len(temp)
        indexes = set(range(len(temp)))

        if page_subsets is not None:
            if page_subsets[idx] is not None:
                indexes = indexes.intersection(page_subsets[idx])

        if reference_pages is not None:
            indexes = indexes.intersection(set(range(reference_pages[idx])))

        indexes = list(indexes)
        indexes.sort()
        for index in indexes:
            pages += [temp[index]]

    _, n, m = calc_best_packing(pages_per_page)[0][:3]

    if verbose:
        print(f"\n> Packing parameters: {n} x {m}")

    new_pages = []
    if pages_per_page > 1:
        # This is consistent as long as the pdf pages are standard 8.5x11
        w_def = 612 * scaler
        h_def = 792 * scaler

        count = 0
        temp = PageMerge()
        for page in pages:
            temp.add(page)
            temp[-1].x = w_def * (count % n)
            temp[-1].y = h_def * (m - 1 - count // n)
            count += 1
            if count >= pages_per_page:
                count = 0
                new_pages.append(temp.render())
                temp = PageMerge()

        # If there was a leftover page (odd number of pages)
        if len(temp) > 0 and len(temp) < pages_per_page:
            new_pages.append(temp.render())

    else:
        # Single page per sheet
        for idx, page in enumerate(pages):
            temp = PageMerge()
            temp.add(page)
            new_pages.append(temp.render())

    PdfWriter(os.path.join(path, new_filename)).addpages(new_pages).write()
    if verbose:
        print(
            f"\nFinal Sheets ({pages_per_page} pages/sheet): {len(new_pages)} of {math.ceil(total_pages/pages_per_page)} ({100-len(new_pages)/max(1, math.ceil(total_pages/pages_per_page))*100:.1f}% reduced)"
        )
        print(f"Output to: {os.path.join(path, new_filename)}")


if __name__ == "__main__":
    combine_pdfs("D:\\Papers", "combined.pdf", pages_per_page=4, verbose=True)
