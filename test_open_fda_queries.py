"""
This module tests the important routines used to fetch results using the Open FDA API.
Testing is limited to methods for query construction.
Copyright © 2024 Kevin Garwood. This software has been open-sourced through the MIT license, whose text is
specified at: https://mit-license.org/.
"""
from open_fda_queries import get_search_query_url
from open_fda_queries import SearchType
import open_fda_queries as open_fda_queries


def test_get_search_query_url():
    """
    Ensure that Open FDA query construction works correctly
    :return:
    """
    open_fda_queries.RESULTS_PER_BATCH = 500
    actual_detect_algorithms_query =\
        get_search_query_url(SearchType.DETECT_ALGORITHM, 500)
    expected_detect_algorithm_query =\
        (f"https://api.fda.gov/device/event.json?search=algorithm*"
         f"&limit=500&skip=500")
    assert expected_detect_algorithm_query == actual_detect_algorithms_query

    actual_detect_diagnostic_algorithm_query =\
        get_search_query_url(SearchType.DETECT_DIAGNOSTIC_ALGORITHM)
    expected_detect_diagnostic_algorithm_query =\
        (f"https://api.fda.gov/device/event.json?search=algorithm*+AND+(diagnostic*+OR+diagnosis*)"
         f"&limit=500")
    assert expected_detect_diagnostic_algorithm_query == actual_detect_diagnostic_algorithm_query

    actual_detect_ai_query =\
        get_search_query_url(SearchType.DETECT_ARTIFICIAL_INTELLIGENCE, 500)
    expected_detect_ai_query =\
        (f"https://api.fda.gov/device/event.json?search=%22artificial+intelligence*%22+OR+%22machine+learning*%22"
         f"&limit=500&skip=500")
    assert expected_detect_ai_query == actual_detect_ai_query
