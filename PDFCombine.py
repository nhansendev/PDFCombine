# Copyright (c) 2023, Nathan Hansen
# All rights reserved.

# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import os
import sys
from pdfrw import PdfReader, PdfWriter, PageMerge
import pdfplumber
from multiprocessing import Pool
from functools import partial
import math


ENDSTRINGS = ["Referen", "Bibliog", "Acknowl"]


def calc_best_packing(t, A=8.5, B=11):
    options = []
    for n in range(1, t + 1):
        m = math.ceil(t / n)

        # 0 deg
        w1 = n * A
        h1 = m * B
        ap1 = w1 * h1 + 2 * w1 + 2 * h1

        # 90 deg
        w2 = n * B
        h2 = m * A
        ap2 = w2 * h2 + 2 * w2 + 2 * h2

        # The most compact has the smallest area and perimeter
        if ap1 < ap2:
            options.append([n, m, ap1])
        else:
            options.append([m, n, ap2])

    options.sort(key=lambda x: x[-1], reverse=False)

    return options[0][:2]


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
    pages_per_page=4,
    subset=None,
    exclude=None,
    page_subsets=None,
    remove_refs=True,
    scaler=0.92,
    verbose=True,
):
    try:
        pages_per_page = int(pages_per_page)
        if pages_per_page < 1:
            raise ValueError
    except ValueError:
        print("Error: Provided <pages_per_page> value must be an integer > 0")
        return

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

    n, m = calc_best_packing(pages_per_page)

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
    if len(sys.argv) > 1:
        combine_pdfs(*sys.argv[1:])
    else:
        print(
            "Usage: python CombinePDFs.py <directory with PDFs> <new filename> <pages per page>"
        )
