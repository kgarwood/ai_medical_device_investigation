"""
This module contains nominal tests that are used to generate reports. There are not many tests
because I have wanted to keep HTML reports simple.

Copyright © 2024 Kevin Garwood. This software has been open-sourced through the MIT license, whose text is
specified at: https://mit-license.org/.
"""
import pandas as pd

import open_fda_reports
from open_fda_reports import generate_result_labels
from open_fda_reports import highlight_terms


def test_generate_result_labels():
    """
    Ensure that each result will have a uniquely generated result ID that will correctly pad the ith result label
    with leading zeros. For example, if there are 25 results and the prefix is 'KG', the first result should be
    KG-01 and not KG-1.
    :return:
    """
    df = pd.DataFrame([{'Result': 1}, {'Result': 2}, {'Result': 3}, {'Result': 4}, {'Result': 5}, {'Result': 6},
                       {'Result': 7}, {'Result': 8}, {'Result': 9}, {'Result': 10}, {'Result': 11}])

    actual_results_df = generate_result_labels(df, 'KG')
    expected_results_df =\
        pd.DataFrame([{'Result Label': 'KG-01', 'Result': 1},
                      {'Result Label': 'KG-02', 'Result': 2},
                      {'Result Label': 'KG-03', 'Result': 3},
                      {'Result Label': 'KG-04', 'Result': 4},
                      {'Result Label': 'KG-05', 'Result': 5},
                      {'Result Label': 'KG-06', 'Result': 6},
                      {'Result Label': 'KG-07', 'Result': 7},
                      {'Result Label': 'KG-08', 'Result': 8},
                      {'Result Label': 'KG-09', 'Result': 9},
                      {'Result Label': 'KG-10', 'Result': 10},
                      {'Result Label': 'KG-11', 'Result': 11}])
    pd.testing.assert_frame_equal(expected_results_df, actual_results_df)


def test_highlight_terms():
    """
    Ensure that when the results are generated that any occurrences of phrases of interest
    e.g. algorithm, machine learning, artificial intelligence will appear highlighted in red for
    easy reading.
    :return: modified text that may contain HTML code for highlighting key phrases defined in
    open_fda_reports.TERMS_TO_HIGHLIGHT.
    """
    open_fda_reports.TERMS_TO_HIGHLIGHT = ['machine learning']
    text_with_no_occurrences = "Some kind of medical device report description without key words"
    actual_highlighted_text = highlight_terms(text_with_no_occurrences)
    assert text_with_no_occurrences == actual_highlighted_text

    text_with_occurrences = "A medical device report that mentions machine learning."
    actual_highlighted_text = highlight_terms(text_with_occurrences)
    expected_highlighted_text =\
        "A medical device report that mentions <b style=\'color:red;\'>machine learning</b>."
    assert expected_highlighted_text == actual_highlighted_text
