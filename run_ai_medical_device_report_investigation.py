"""
Welcome to the Open FDA AI Medical Device Investigation. This is the main module
that runs the investigation. It uses the Open FDA Device API to search for three
kinds of medical devices. They include those which:

(1) mention 'artificial intelligence' or 'machine learning'
(2) mention 'algorithm'
(3) mention 'algorithm' and either 'diagnostic' or 'diagnosis'

Copyright © 2024 Kevin Garwood. This software has been open-sourced through the MIT license, whose text is
specified at: https://mit-license.org/.
"""
import http.client
import logging
import time

import pandas as pd

from open_fda_queries import get_query_result_batch
from open_fda_queries import get_result_label_prefix
from open_fda_queries import RESULTS_PER_BATCH
from open_fda_queries import SearchType
from open_fda_reports import generate_result_labels
from open_fda_reports import OutputManager
from open_fda_result_parser import process_result_batch


logger = logging.getLogger(__name__)


def process_device_report_search_query(search_type: SearchType) -> pd.DataFrame:
    """
    Given a search type, iterates through an often large number of results returned from a query
    applied to Open FDA Device API.
    :param search_type:
    :return:
    """
    all_result_records_list = list()

    try:
        current_url, json_response = get_query_result_batch(search_type)

        total_results_returned = json_response['meta']['results']['total']

        logger.info(f"Total results returned from query:{total_results_returned}.")

        if total_results_returned > 25000:
            # You can use the simple 'limit' and 'skip' URL parameters to traverse through a long list
            # of search results, provided the total is less than 25000. Beyond 25000 there is another
            # more complicated mechanism. The goal of the investigation is to explore trends rather than
            # provide exhaustive results. To simplify this demo, I have decided to limit results to
            # a maximum of 25000
            logger.info(f"Limiting total number of results considered to 25000.")
            total_results_returned = 25000

        # Determine the number of batches the total number of results would make. Then iterate through each
        # batch of device reports and keep accumulating them in a list.
        number_result_batches = total_results_returned // RESULTS_PER_BATCH
        all_result_records_list.extend(process_result_batch(current_url, json_response))

        logger.info(f"Executing query: {current_url}")

        ith_result_batch = 1
        while ith_result_batch <= number_result_batches:
            # Adding a three-second delay to pause the program. The delay is imposed to help limit the
            # computational demands the script may make of the Open FDA Device API.
            time.sleep(3)
            number_records_to_skip = ith_result_batch * RESULTS_PER_BATCH

            current_url, json_response = get_query_result_batch(search_type, number_records_to_skip)
            logger.info(f"Executing query: {current_url}")

            all_result_records_list.extend(process_result_batch(current_url, json_response))
            ith_result_batch = ith_result_batch + 1
    except http.client.IncompleteRead as exception:
        logger.error(exception)

    df = pd.DataFrame(all_result_records_list)
    df = df.drop_duplicates(keep=False)
    return get_ordered_device_report_results(df)


def get_ordered_device_report_results(original_df: pd.DataFrame) -> pd.DataFrame:
    """
    Orders the columns and then sorts the rows of device report results.
    :param original_df:
    :return:
    """
    df = original_df.copy()
    df = df[['Base Report ID', 'Report ID', 'Source URL', 'Adverse Event Flag', 'Event Date', 'Report Source Code',
             'Device Specialty Area', 'Device Class', 'Device Reg Number', 'Device Name',
             'Device Model Number', 'Device Catalogue Number', 'Device Lot Number',
             'Patient Problems',
             'Product Problems',
             'Event Main Comments',
             'Event Manufacturer Comments']]

    df = df.sort_values(by='Report ID', ascending=True)
    return df


def filter_machine_learning(original_df: pd.DataFrame) -> pd.DataFrame:
    df = original_df.copy()

    df['Mentions Machine Learning'] =\
        df.apply(lambda x: contains_machine_learning_reference(x['Event Main Comments'],
                                                               x['Event Manufacturer Comments']),
                 axis=1)
    return df


def contains_machine_learning_reference(original_event_comment: str,
                                        original_event_additional_comment: str):
    """
    Filters results
    :param original_event_comment:
    :param original_event_additional_comment:
    :return:
    """
    event_comment = original_event_comment.lower()
    event_additional_comment = original_event_additional_comment.lower()

    if 'machine learning' in event_comment:
        return True
    if 'machine learning' in event_additional_comment:
        return True
    return False


def filter_by_device_is_suspect(original_df: pd.DataFrame) -> pd.DataFrame:
    """
    Consider only records where a device is at least suspected as having influenced an adverse outcome in a device
    user.
    :param original_df:
    :return: filtered data frame
    """
    df = original_df.copy()
    df = df[df['Adverse Event Flag'] == 'y']
    return df


def filter_problem_types(original_df: pd.DataFrame) -> pd.DataFrame:
    """
    Consider only device reports that have been labelled with the following product problem category:
       (1) inadequate or imprecise result or readings
       (2) program or algorithm execution
       (3) patient data problem
    :param original_df:
    :return: filtered data frame
    """
    df = original_df.copy()

    df['Has Relevant Problem Type'] =\
        df['Product Problems'].apply(lambda x: contains_relevant_problem_type(x))
    # df = df[df['Has Relevant Problem Type']]
    return df


def contains_relevant_problem_type(current_product_problem):
    """
    Determines whether the problem type associated with a medical device report is one that
    interests us. There are many categories but these three seem to me like they would
    be most relevant to analyses.
    :param current_product_problem:
    :return:
    """
    canonical_form = current_product_problem.lower()
    if 'inadequate or imprecise result or readings' in canonical_form:
        return True
    if 'program or algorithm execution' in canonical_form:
        return True
    if 'patient data problem' in canonical_form:
        return True
    return False


def examine_device_reports_mentioning_machine_learning(report_output_manager: OutputManager) -> None:
    """
    Examines machine device reports that mention 'artificial intelligence' or 'machine learning'.
    :param report_output_manager: manages writing output files to a current run directory.
    :return:
    """
    logger.info((f"Investigating medical device reports that contain the phrase "
                 "\'artificial intelligence\' or \'machine learning\'..."))

    results_df = process_device_report_search_query(SearchType.DETECT_ARTIFICIAL_INTELLIGENCE)

    filtering_criteria_list = list()
    if len(results_df) == 25000:
        filtering_criteria_list.append((f"There were at least <b>{len(results_df)}</b> adverse events which mentioned "
                                        "either the term \'artificial intelligence\' or \'machine learning\'. The "
                                        "terms \' AI \' and \' ML \' were left out of the search because "
                                        "they are ambiguous abbreviations. For example, \'ai\' can stand for "
                                        "analog interface and \'ml\' can stand for millilitre."))
    else:
        filtering_criteria_list.append((f"There were <b>{len(results_df)}</b> adverse events which mentioned either "
                                        "the term \'artificial intelligence\' or \'machine learning\'. The "
                                        "terms \' AI \' and \' ML \' were left out of the search because "
                                        "they are ambiguous abbreviations. For example, \'ai\' can stand for "
                                        "analog interface and \'ml\' can stand for millilitre."))

    results_df = filter_by_device_is_suspect(results_df)
    filtering_criteria_list.append((f"There were <b>{len(results_df)}</b> adverse events that described "
                                    "incidents where the use of the device is suspected to have "
                                    "resulted in an adverse outcome in a patient. (see "
                                    "\'adverse_event_flag\'=\'y\' in the API "
                                    "<a href=\"https://open.fda.gov/apis/device/event/searchable-fields/\" "
                                    "target=\"blank\">field specification</a>)"))

    title = "Occurrences of Medical Device AEs that Mention Machine Learning"

    description = ("<p>As of August 7, 2024, the FDA has "
                   "<a href=\"https://www.fda.gov/medical-devices/software-medical-device-samd/"
                   "artificial-intelligence-and-machine-learning-aiml-enabled-medical-devices\""
                   "target=\"blank\">"
                   "authorised</a> 950 AI/ML-Enabled devices. This is an "
                   "investigation into the patterns of reported adverse events where it is suspected that "
                   "a device is at least suspected to have resulted in the adverse outcome of a patient.</p>"
                   "<p>The investigation examines adverse events that have been recorded through the "
                   "<a href=\"https://open.fda.gov/apis/\">Open FDA</a>'s "
                   "<a href=\"https://open.fda.gov/apis/device/\">"
                   "Medical Device API Endpoints</a> facility.</p>"
                   "<p>This inquiry is a search for the adverse events associated with a medical "
                   "device where the record has some mention machine learning or artificial intelligence.</p>")

    search_result_prefix = get_result_label_prefix(SearchType.DETECT_ARTIFICIAL_INTELLIGENCE)
    results_df = generate_result_labels(results_df, search_result_prefix)
    report_output_manager.write_html_report(results_df, "open_fda_ml_results", title, description,
                                            filtering_criteria_list, search_result_prefix)
    report_output_manager.write_excel_report(results_df, "open_fda_ml_results")


def examine_device_reports_mentioning_algorithm(report_output_manager: OutputManager) -> None:
    """
    Explores medical device reports that mention the term 'algorithm'
    :param report_output_manager: manages writing output files to a current run directory.
    :return:
    """

    logger.info(f"Investigating medical device reports that contain the phrase \'algorithm\'...")

    filtering_criteria_list = []

    results_df = process_device_report_search_query(SearchType.DETECT_ALGORITHM)
    if len(results_df) == 25000:
        filtering_criteria_list.append((f"There were at least <b>{len(results_df)}</b> adverse events that mentioned "
                                        "the term \"algorithm\""))
    else:
        filtering_criteria_list.append((f"There were <b>{len(results_df)}</b> adverse events that mentioned "
                                        "the term \"algorithm\""))

    results_df = filter_by_device_is_suspect(results_df)
    filtering_criteria_list.append((f"There were <b>{len(results_df)}</b> adverse events that described "
                                    "incidents where the use of the device is suspected to have "
                                    "resulted in an adverse outcome in a patient. (see "
                                    "\'adverse_event_flag\'=\'y\' in the API "
                                    "<a href=\"https://open.fda.gov/apis/device/event/searchable-fields/\" "
                                    "target=\"blank\">field specification</a>)"))

    results_df = filter_problem_types(results_df)
    filtering_criteria_list.append((f"There were <b>{len(results_df)}</b> adverse events that had a "
                                    "product problem that mentioned one of the following "
                                    "phrases that are included in category names: "
                                    "\'Inadequate or Imprecise Result or Readings\',"
                                    "\'Program or Algorithm Execution Failure\',"
                                    "\'Program or Algorithm Execution Problem\',"
                                    "\'Patient Data Problem\',"
                                    "\'Application Program Problem\'. See the field product_problems in  the API "
                                    "<a href=\"https://open.fda.gov/apis/device/event/searchable-fields/\" "
                                    "target=\"blank\">field specification</a>)"))

    title = "Occurrences of Medical Device AEs that Mention Algorithm with Relevant Problem Type"
    description = ("<p>As of August 7, 2024, the FDA has "
                   "<a href=\"https://www.fda.gov/medical-devices/software-medical-device-samd/"
                   "artificial-intelligence-and-machine-learning-aiml-enabled-medical-devices\""
                   "target=\"blank\">"
                   "authorised</a> 950 AI/ML-Enabled devices. This is an "
                   "investigation into the patterns of reported adverse events where it is suspected that "
                   "a device is at least suspected to have resulted in the adverse outcome of a patient.</p>"
                   "<p>The investigation examines adverse events that have been recorded through the "
                   "<a href=\"https://open.fda.gov/apis/\">Open FDA</a>'s "
                   "<a href=\"https://open.fda.gov/apis/device/\">"
                   "Medical Device API Endpoints</a> facility.</p>"
                   "<p>This inquiry is a search for the adverse events associated with a medical "
                   "device where the record has some mention of the term \"algorithm\"."
                   "I've tried to use \"algorithm\" because search results do not return much "
                   "using search terms like \"machine learning\" and \"artificial intelligence\".</p>")

    search_result_prefix = get_result_label_prefix(SearchType.DETECT_ALGORITHM)
    results_df = generate_result_labels(results_df, search_result_prefix)
    report_output_manager.write_html_report(results_df, "open_fda_algorithms_results", title, description,
                                            filtering_criteria_list, search_result_prefix)
    report_output_manager.write_excel_report(results_df,
                                             "open_fda_algorithms_results")


def examine_device_reports_mentioning_algorithm_and_diagnostic(report_output_manager: OutputManager):
    """
    Explores medical device reports that mention 'algorithm' and either 'diagnostic' or 'diagnosis'.
    :param report_output_manager: manages writing output files to a current run directory.
    :return:
    """
    filtering_criteria_list = []

    results_df = process_device_report_search_query(SearchType.DETECT_DIAGNOSTIC_ALGORITHM)

    filtering_criteria_list.append((f"There were <b>{len(results_df)}</b> adverse events that mentioned "
                                    "the term \"algorithm\" and then either \"diagnostic\" or \"diagnosis\"."))

    results_df = filter_by_device_is_suspect(results_df)
    filtering_criteria_list.append((f"There were <b>{len(results_df)}</b> adverse events that described "
                                    "incidents where the use of the device is suspected to have "
                                    "resulted in an adverse outcome in a patient. (see "
                                    "\'adverse_event_flag\'=\'y\' in the API "
                                    "<a href=\"https://open.fda.gov/apis/device/event/searchable-fields/\" "
                                    "target=\"blank\">field specification</a>)"))

    results_df = filter_problem_types(results_df)
    filtering_criteria_list.append((f"There were <b>{len(results_df)}</b> adverse events that had a "
                                    "product problem that mentioned one of the following "
                                    "phrases that are included in category names: "
                                    "\'Inadequate or Imprecise Result or Readings\',"
                                    "\'Program or Algorithm Execution Failure\',"
                                    "\'Program or Algorithm Execution Problem\',"
                                    "\'Patient Data Problem\',"
                                    "\'Application Program Problem\'. See the field product_problems in  the API "
                                    "<a href=\"https://open.fda.gov/apis/device/event/searchable-fields/\" "
                                    "target=\"blank\">field specification</a>)"))

    title = "Occurrences of Medical Device AEs that Mention Algorithm with Relevant Problem Type"
    description = ("<p>As of August 7, 2024, the FDA has "
                   "<a href=\"https://www.fda.gov/medical-devices/software-medical-device-samd/"
                   "artificial-intelligence-and-machine-learning-aiml-enabled-medical-devices\""
                   "target=\"blank\">"
                   "authorised</a> 950 AI/ML-Enabled devices. This is an "
                   "investigation into the patterns of reported adverse events where it is suspected that "
                   "a device is at least suspected to have resulted in the adverse outcome of a patient.</p>"
                   "<p>The investigation examines adverse events that have been recorded through the "
                   "<a href=\"https://open.fda.gov/apis/\">Open FDA</a>'s "
                   "<a href=\"https://open.fda.gov/apis/device/\">"
                   "Medical Device API Endpoints</a> facility.</p>"
                   "<p>This inquiry is a search for the adverse events associated with a medical "
                   "device where the record has some mention of the term \"algorithm\"."
                   "I've tried to use \"algorithm\" because search results do not return much "
                   "using search terms like \"machine learning\" and \"artificial intelligence\".</p>")

    search_result_prefix = get_result_label_prefix(SearchType.DETECT_DIAGNOSTIC_ALGORITHM)
    results_df = generate_result_labels(results_df, search_result_prefix)
    report_output_manager.write_html_report(results_df, "open_fda_algorithms_diagnostic_results",
                                            title, description, filtering_criteria_list, search_result_prefix)

    report_output_manager.write_excel_report(results_df,
                                             "open_fda_algorithms_diagnostic_results")


if __name__ == '__main__':
    print("Running the Open FDA Device API investigation about AI-driven medical devices...")
    output_manager = OutputManager()
    examine_device_reports_mentioning_machine_learning(output_manager)
    examine_device_reports_mentioning_algorithm(output_manager)
    examine_device_reports_mentioning_algorithm_and_diagnostic(output_manager)
    print("Finished!")
