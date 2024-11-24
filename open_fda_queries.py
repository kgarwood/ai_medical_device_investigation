"""
This module tries to isolate the code used to execute a query applied to the Open FDA Device API. The queries
here support an investigation of identifying the kinds of operational issues that may be associated with
AI-driven medical devices.

Open FDA can support sophisticated queries, but I've chosen simple ones for the sake of making a simple
demonstration. Trying to identify search terms that would return results about artificial intelligence proved
challenging.

Using phrases like 'artificial intelligence' or 'AI' or 'machine learning' or 'ML' returned too
many results. AI and ML are vague, with AI sometimes describing application interface and ML describing millilitre.
Of the few search results that match on 'machine learning' or 'artificial intelligence', most of the reports are
manufacture reports that try to respond to a new piece of research literature that happens to have these phrases in
the journal title.

Searching for 'algorithm' generated too many results, with many of the reports likely to describe software problems
for devices that were not about 'artificial intelligence' or 'machine learning'. However, algorithm does provide
insights into problems for software-driven medical devices in general.

I finally decided to focus on results that mentioned 'algorithm' and either 'diagnostic' or 'diagnosis'. This limits
the kinds of device contexts I encountered, but this approach yielded results that were large enough to show variety
but small enough to process by eye.

Copyright © 2024 Kevin Garwood. This software has been open-sourced through the MIT license, whose text is
specified at: https://mit-license.org/.
"""
from enum import Enum
from enum import auto
import json
from urllib.request import urlopen


class SearchType(Enum):
    """
    Defines search themes that are used in the investigation of Open FDA Device API's device reports
    that relate to AI-driven devices.
    """

    # Match on results that mention 'machine learning' or 'artificial intelligence' in a device report
    DETECT_ARTIFICIAL_INTELLIGENCE = auto()

    # Match on results that mention 'algorithm' in a device report.
    DETECT_ALGORITHM = auto()

    # Match on results that mention both 'algorithm' and either 'diagnosis' or 'diagnostic' in an adverse event
    # report
    DETECT_DIAGNOSTIC_ALGORITHM = auto()


def get_result_label_prefix(search_type: SearchType) -> str:
    match search_type:
        case SearchType.DETECT_ARTIFICIAL_INTELLIGENCE:
            return 'AI'
        case SearchType.DETECT_ALGORITHM:
            return 'ALG'
        case SearchType.DETECT_DIAGNOSTIC_ALGORITHM:
            return 'ALG-DIAG'


# This constant is used to help the script traverse through a large number of search results. It is used to
# provide values for both 'limit' and 'skip' variables that appear in a query URL. 'limit' indicates how many
# results should be returned for a result page. 'skip' is the total number of records from the first that the
# query should skip. Note that Open FDA APIs support a maximum value of 1000 results returned in a single
# query call.
RESULTS_PER_BATCH = 500


def get_query_result_batch(search_type: SearchType, number_records_to_skip: int = 0):
    """
    Returns JSON responses for a query URL that is based on the search type
    :param search_type: describes the theme of the search, which determines how the query URL is constructed.
    :param number_records_to_skip:
    :return: the method returns two values. First it returns the URL for the search query. It is returned so
    that in the reporting of results, a result can be linked back to the original URL that would have contained it.
    Second, it returns the JSON response from the Open FDA Device API
    """
    current_url = get_search_query_url(search_type, number_records_to_skip)
    json_response = json.loads(urlopen(current_url).read())
    return current_url, json_response


def get_search_query_url(search_type: SearchType, number_records_to_skip: int = 0):
    """
    Returns a collection of results that describe device reports which mention terms
    relevant to the specified search type
    :param search_type: describes different search themes that determine what kind of specialised
    query routine to call.
    :param number_records_to_skip: the number of records from the first that the Open FDA Device API should
    skip. This value is used to help the program process batches in an often large collection of returned results.
    :return: the URL for a search query that can be applied to the Open FDA Device API
    """
    match search_type:
        case SearchType.DETECT_ARTIFICIAL_INTELLIGENCE:
            return __get_artificial_intelligence_search_query_url(number_records_to_skip)
        case SearchType.DETECT_ALGORITHM:
            return __get_algorithm_only_search_query_url(number_records_to_skip)
        case SearchType.DETECT_DIAGNOSTIC_ALGORITHM:
            return __get_diagnostic_algorithm_api_url(number_records_to_skip)


def __get_algorithm_only_search_query_url(number_records_to_skip: int = 0) -> str:
    """
    Uses the Open FDA Device API by searching for any device reports that contain case-insensitive
    matches for 'algorithm'. Note that the API interprets an '*' as a request for case-insensitive searches.
    :param number_records_to_skip: the number of search results to skip.
    :return: the URL for a search query that can be applied to the Open FDA Device API
    """
    if number_records_to_skip == 0:
        return (f"https://api.fda.gov/device/event.json?search="
                f"algorithm*&limit={RESULTS_PER_BATCH}")
    else:
        return (f"https://api.fda.gov/device/event.json?search="
                f"algorithm*"
                f"&limit={RESULTS_PER_BATCH}&skip={str(number_records_to_skip)}")


def __get_diagnostic_algorithm_api_url(number_records_to_skip: int = 0) -> str:
    """
    Uses the Open FDA Device API by searching for any device reports that contain case-insensitive
    matches for 'algorithm' and either 'diagnostic' or 'diagnosis'. Note that the API interprets an '*' as a
    request for case-insensitive searches.
    :param number_records_to_skip: the number of search results to skip.
    :return: the URL for a search query that can be applied to the Open FDA Device API
    """
    if number_records_to_skip == 0:
        return (f"https://api.fda.gov/device/event.json?search="
                f"algorithm*+AND+(diagnostic*+OR+diagnosis*)"
                f"&limit={RESULTS_PER_BATCH}")
    else:
        return (f"https://api.fda.gov/device/event.json?search="
                f"algorithm*+AND+(diagnostic*+OR+diagnosis*)"
                f"&limit={RESULTS_PER_BATCH}&skip={str(number_records_to_skip)}")


def __get_artificial_intelligence_search_query_url(number_records_to_skip: int = 0) -> str:
    """
    Uses the Open FDA Device API by searching for any device reports that contain case-insensitive
    matches either 'artificial intelligence' or 'machine learning'.  Note that the API interprets an '*' as a
    request for case-insensitive searches.
    :param number_records_to_skip: the number of search results to skip.
    :return: the URL for a search query that can be applied to the Open FDA Device API
    """
    if number_records_to_skip == 0:
        return (f"https://api.fda.gov/device/event.json?search="
                f"%22artificial+intelligence*%22+OR+%22machine+learning*%22"
                f"&limit={RESULTS_PER_BATCH}")
    else:
        return (f"https://api.fda.gov/device/event.json?search="
                f"%22artificial+intelligence*%22+OR+%22machine+learning*%22"
                f"&limit={RESULTS_PER_BATCH}&skip={str(number_records_to_skip)}")
