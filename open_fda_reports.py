"""
This module contains routines for generating the reports used for the investigation. I debated
whether I could benefit from using BeautifulSoup, but the HTML reports are so simple I thought
it was simpler to just put some simple hand-crafted HTML.

Copyright © 2024 Kevin Garwood. This software has been open-sourced through the MIT license, whose text is
specified at: https://mit-license.org/.
"""
import datetime
import logging
import os
from pathlib import Path

import pandas as pd


class OutputManager:
    def __init__(self):
        current_run_directory_path = os.getcwd()
        current_time = datetime.datetime.now()

        self.output_run_directory_path = Path(current_run_directory_path,
                                              "investigation_results",
                                              f"run_{current_time.strftime("%Y-%m-%d-%H%M%S")}")

        self.output_run_directory_path.mkdir(exist_ok=True)

        logging_file_path = Path(self.output_run_directory_path, "audit_trail.log")
        logging.basicConfig(filename=logging_file_path, level=logging.INFO)

    def write_excel_report(self, results_df: pd.DataFrame, base_file_name: str) -> None:
        """
        Writes the data frame to an Excel Workbook
        :param results_df:
        :param base_file_name:
        :return:
        """
        output_file_path = Path(self.output_run_directory_path, f"{base_file_name}.xlsx")
        # output_file_path = os.path.join(self.output_run_directory_path, f"{base_file_name}.xlsx")
        writer = pd.ExcelWriter(output_file_path, engine='xlsxwriter')
        results_df.to_excel(writer, sheet_name="Main Results")
        writer.close()

    def write_html_report(self, df: pd.DataFrame, base_file_name: str, title: str,
                          description: str, filtering_criteria_list: list,
                          reference_prefix: str) -> None:

        """
        Writes an HTML report and tries to highlight the search terms in the main comments section of the
        device reports.
        :param df:
        :param base_file_name:
        :param title:
        :param description:
        :param filtering_criteria_list:
        :param reference_prefix: this is a code used to label results so that they can be referenced
        in the analyses. Results are labelled based on the convention
        [reference_prefix]-[number]
        :return:
        """

        output_file_path = Path(self.output_run_directory_path, f"{base_file_name}.html")
        with open(output_file_path, mode='w', encoding='utf-8') as file:
            file.write(f"<html><head><title>{title}</title></head><body>")
            file.write(f"<h1>{title}</h1>")
            file.write("<p>")
            file.write(("Copyright © 2024 Kevin Garwood. This software and its outputs have been open-sourced "
                        "through the <a href=\"https://mit-license.org/\">MIT license</a>."))
            file.write("</p>")
            file.write(f"<h2>Description</h2>{description}")

            file.write("<h2>Filtering Criteria</h2>")
            file.write("The following criteria were applied in successive order:")
            file.write("<ol>")
            for filtering_criterion in filtering_criteria_list:
                file.write(f"<li>{filtering_criterion}</li>")
            file.write("</ol>")


            file.write("<h2>Results</h2>")
            file.write("<p>")
            file.write("If you would like to see the original search query that yielded a result, click on the ")
            file.write("result number hyperlink. Please note all the results are labelled using the naming ")
            file.write(f"convention of \'{reference_prefix}\'-[number]")
            file.write("</p>")

            ith_result = 0
            for index, row in df.iterrows():
                ith_result = ith_result + 1
                file.write(f"<h3 id=\"{row['Result Label']}\">Result {row['Result Label']}</h3>")
                file.write(f"<p><a href=\"{row['Source URL']}\" target=\"blank\">Original Source Query</a></p>")
                file.write(f"<p><b>Event Date</b>:{row['Event Date']}     "
                           f"<b>Report ID</b>:{row['Report ID']}     "
                           f"<b>Report Source Code</b>:{row['Report Source Code']}</p>")

                file.write(f"<p><b>Device Specialty Area</b>:{row['Device Specialty Area']}     "
                           f"<b>Device Class</b>:{row['Device Class']}</p>")

                file.write(f"<p><b>Device Reg Number</b>:{row['Device Reg Number']}     "
                           f"<b>Device Name</b>:{row['Device Name']}</p>")
                file.write(f"<p><b>Device Model Number</b>:{row['Device Model Number']}     "
                           f"<b>Device Catalogue Number</b>:{row['Device Catalogue Number']}     "
                           f"<b>Device Lot Number</b>: {row['Device Lot Number']}</p>")

                file.write("<p></p>")
                file.write(f"<p><b>Product Problems</b>:{row['Product Problems']}</p>")
                file.write(f"<p><b>Patient Problems</b>:{row['Patient Problems']}</p>")
                file.write(f"<p><b>Event Main Comments</b>:{highlight_terms(row['Event Main Comments'])}</p>")
                file.write("<p><b>Event Manufacturer Comments</b>:")
                file.write(f"{highlight_terms(row['Event Manufacturer Comments'])}</p>")
                file.write("<hr>")

            file.write("</body></html>")
        file.close()


def generate_result_labels(original_df: pd.DataFrame, search_result_prefix: str) -> pd.DataFrame:
    """
    Adds a column to a data frame result with a semi-mnemonic identifier that can be easily and uniquely
    referenced in analyses reports.
    :param original_df: the data frame containing results
    :param search_result_prefix: the prefix that should be used to label each result.
    :return: a copy of the original data frame that also has a Result Label column containing the
    labels for results.
    """
    df = original_df.copy()
    total_number_results = len(df)
    df.insert(0, 'Result Label', range(1, 1 + total_number_results))
    maximum_digits = len(str(total_number_results))
    df['Result Label'] = df['Result Label'].apply(lambda x: generate_result_label(search_result_prefix,
                                                                                  maximum_digits,
                                                                                  x))
    return df


def generate_result_label(search_result_prefix: str, maximum_digits_width: int, result_number: int) -> str:
    """
    Generate a result label based on a prefix and a result number that is padded with leading zeros based on
    the maximum digits that are in the total number of results.
    :param search_result_prefix:
    :param maximum_digits_width:
    :param result_number:
    :return: a result identifier that makes it easy to reference in analysis articles.
    """
    return f"{search_result_prefix}-{str(result_number).zfill(maximum_digits_width)}"


TERMS_TO_HIGHLIGHT = ['machine learning', 'algorithm', ' ai ', 'artificial intelligence', 'diagnostic', 'diagnosis']


def highlight_terms(original_text: str) -> str:
    """
    Replaces occurrences of search terms with HTML highlighted versions of them
    :param original_text:
    :return:
    """
    text = original_text
    for term_to_highlight in TERMS_TO_HIGHLIGHT:
        replace_with_text = f"<b style=\'color:red;\'>{term_to_highlight}</b>"
        text = text.replace(term_to_highlight, replace_with_text)

    return text
