
Investigation of device reports Associated with AI-Driven Medical Devices

# Overview
This code project was created to support an investigation of what kinds
of operational issues may be associated with AI-driven medical devices. The 
scripts query the [Open FDA Device API](https://open.fda.gov/apis/device/event/). 
I've developed the scripts to retrieve details of device reports that 
may relate to artificial intelligence. I've applied different search queries in 
an attempt to better understand how AI-driven medical devices could be 
identified in a large body of reports.

# Understanding the Context of Open FDA Device API Data
The medical device reports this project analyses should be regarded with caution.
Just because a report is associated with a particular medical device does not 
mean that the medical device cause an adverse outcome in a device user.

Borrowing from the 
main [Open FDA Device API page](https://open.fda.gov/apis/device/event/):

>The openFDA device adverse event API returns data from Manufacturer and 
User Facility Device Experience (MAUDE), an FDA dataset that contains 
medical device device reports submitted by mandatory 
reporters—manufacturers, importers and device user facilities—and 
voluntary reporters such as health care professionals, patients, and 
consumers. Currently, this data covers publically releasable records 
submitted to the FDA from about 1992 to the present. The data is updated 
weekly.
>
>Each year, the FDA receives several hundred thousand medical device 
reports (MDRs) of suspected device-associated deaths, serious injuries and 
malfunctions. The FDA uses MDRs to monitor device performance, detect 
potential device-related safety issues, and contribute to benefit-risk 
assessments of these products. The MAUDE database houses MDRs submitted 
to the FDA by mandatory reporters (manufacturers, importers and device user 
facilities) and by voluntary reporters (such as health care professionals, 
patients, and consumers).
>
>**Although MDRs are a valuable source of information, this passive surveillance 
system has limitations, including the potential submission of incomplete, 
inaccurate, untimely, unverified, or biased data**. In addition, the incidence 
or prevalence of an event cannot be determined from this reporting system alone 
due to potential under-reporting of events and lack of information about 
frequency of device use. Because of this, MDRs comprise only one of the FDA’s 
several important postmarket surveillance data sources.

# License
I have open-sourced this project under the [MIT open source license](https://opensource.org/license/mit)

# Installation
The project has been made as a PyCharm project.

pandas
