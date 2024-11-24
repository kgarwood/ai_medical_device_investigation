"""
This module contains

The fields returned by the Open FDA Device API are described at:
https://open.fda.gov/apis/device/event/searchable-fields/

Copyright © 2024 Kevin Garwood. This software has been open-sourced through the MIT license, whose text is
specified at: https://mit-license.org/.
"""
UNKNOWN = "unknown"


def process_result_batch(current_url: str, json_response) -> list:
    """
    Processes a collection of results that are returned by a search query applied to Open FDA's Device API.
    The size of the collection depends on the value specified in the 'limit' parameter of the search query URL.
    :param current_url: the URL for the search query that will be applied to Open FDA's Device API to return
    results.
    :param json_response: the JSON code that is returned by the Open FDA Device API, which will describe a
    collection of query results.
    :return: a list of dictionary instances, each of which describes characteristics of a single adverse
    event report
    """
    result_record_list = list()
    json_results = json_response['results']

    for json_result in json_results:
        result_dct = dict()
        result_dct['Source URL'] = current_url
        set_field_value(json_result, 'report_number',
                        result_dct, 'Report ID')

        # Create a base Report ID that makes it easier to group them together in analyses
        # Each report appears to have the format [basic report number]-[full year]-[number]
        result_dct['Base Report ID'] = result_dct['Report ID'].split('-')[0]

        set_field_value(json_result, 'date_of_event',
                        result_dct, 'Event Date')
        set_field_value(json_result, 'adverse_event_flag',
                        result_dct, 'Adverse Event Flag')
        set_field_value(json_result, 'report_source_code',
                        result_dct, 'Report Source Code')

        set_device_field_values(json_result, result_dct)
        set_product_problem_field_values(json_result, result_dct)
        set_patient_problem_field_values(json_result, result_dct)
        set_comment_field_values(json_result, result_dct)

        result_record_list.append(result_dct)

    return result_record_list


def set_field_value(json_record: any, json_field_name: str, result_dct: dict, result_field_name: str) -> None:
    """
    Extracts a field from a JSON record and assigns the value to a dictionary variable
    :param json_record: contains a JSON record from a larger JSON response that is returned by Open FDA's Device API.
    :param json_field_name: the name of the tag found within the JSON record.
    :param result_dct: the dictionary that is collects all the relevant field values for describing an adverse
    event report.
    :param result_field_name: the name of the dictionary variable that will be hold the relevant
    json_record field value.
    :return:
    """
    result_dct[result_field_name] = UNKNOWN
    if json_field_name in json_record:
        json_field_value = json_record[json_field_name]
        if json_field_value != "":
            result_dct[result_field_name] = json_record[json_field_name].lower()


def set_device_field_values(json_record: any, result_dct: dict) -> None:
    """
    Extracts information from the 'device' sub-record that is part of the description for a
    device report.

    :param json_record:
    :param result_dct:
    :return:
    """
    result_dct['Device Reg Number'] = UNKNOWN
    result_dct['Device Name'] = UNKNOWN
    result_dct['Device Specialty Area'] = UNKNOWN
    result_dct['Device Class'] = UNKNOWN
    result_dct['Device Expiration Date'] = UNKNOWN
    if 'device' in json_record:
        current_devices = json_record['device']

        if current_devices:
            current_device = current_devices[0]
            set_field_value(current_device, 'expiration_date_of_device',
                            result_dct, 'Device Expiration Date')

            set_field_value(current_device, 'model_number',
                            result_dct, 'Device Model Number')
            set_field_value(current_device, 'catalog_number',
                            result_dct, 'Device Catalogue Number')
            set_field_value(current_device, 'lot_number',
                            result_dct, 'Device Lot Number')

            if 'openfda' in current_device:
                openfda = current_device['openfda']

                if 'registration_number' in openfda:
                    result_dct['Device Reg Number'] = openfda['registration_number'][0]

                set_field_value(openfda, 'device_name',
                                result_dct, 'Device Name')
                set_field_value(openfda, 'medical_specialty_description',
                                result_dct, 'Device Specialty Area')
                set_field_value(openfda, 'device_class',
                                result_dct, 'Device Class')


def set_product_problem_field_values(json_record: any, result_dct: dict) -> None:
    """
    Concatenates a list of product problems using an upright '|' character. The list is
    flattened into a single value to make it more convenient to display in tables.
    :param json_record:
    :param result_dct:
    :return:
    """
    result_dct['Product Problems'] = UNKNOWN
    if 'product_problems' in json_record:
        product_problems = json_record['product_problems']
        product_problems.sort()
        result_dct['Product Problems'] = ("|".join(product_problems)).lower()


def set_patient_problem_field_values(json_record: any, result_dct: dict) -> None:
    """
    Concatenates a list of patient problems using an upright '|' character. The list is
    flattened into a single value to make it more convenient to display in tables.
    :param json_record:
    :param result_dct:
    :return:
    """
    result_dct['Patient Problems'] = UNKNOWN
    if 'patient' in json_record:
        patient_list = json_record['patient']
        if patient_list:
            if 'patient_problems' in patient_list[0]:
                patient_problem_list = patient_list[0]['patient_problems']
                patient_problem_list.sort()
                result_dct['Patient Problems'] = ("|".join(patient_problem_list)).lower()


def set_comment_field_values(json_record: any, result_dct: dict) -> None:
    """
    Sets values for the two main comment fields that hold most of the descriptive content for the
    device report. 'Event Main Comments' concatenates the list of comments that comprise the
    original event description. 'Event Manufacturer Comments' captures the list of comments that comprise
    notes that the manufacturer further provides.
    :param json_record:
    :param result_dct:
    :return:
    """
    result_dct['Event Main Comments'] = UNKNOWN
    result_dct['Event Manufacturer Comments'] = UNKNOWN
    if 'mdr_text' in json_record:
        comments = json_record['mdr_text']

        result_dct['Event Main Comments'] = ""
        result_dct['Event Manufacturer Comments'] = ""

        event_main_comments_list = list()
        event_additional_comments_list = list()

        for comment in comments:
            if comment['text_type_code'] == "Description of Event or Problem":
                event_main_comments_list.append(comment['text'])
            elif comment['text_type_code'] == "Additional Manufacturer Narrative":
                event_additional_comments_list.append(comment['text'])

        event_main_comments_list.sort()
        result_dct['Event Main Comments'] = '.'.join(event_main_comments_list)
        result_dct['Event Main Comments'] = result_dct['Event Main Comments'].lower()
        event_additional_comments_list.sort()
        result_dct['Event Manufacturer Comments'] = '.'.join(event_additional_comments_list)
        result_dct['Event Manufacturer Comments'] = result_dct['Event Manufacturer Comments'].lower()
