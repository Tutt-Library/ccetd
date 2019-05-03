__author__ = "Jeremy Nelson"

PREFIX = """PREFIX bf: <http://id.loc.gov/ontologies/bibframe/>
PREFIX cc_fac: <https://www.coloradocollege.edu/ns/faculty/>
PREFIX cc_info: <https://www.coloradocollege.edu/ns/info/>
PREFIX etd: <http://catalog.coloradocollege.edu/ns/etd#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema: <http://schema.org/>"""

ADDL_NOTES = PREFIX + """
SELECT DISTINCT ?note
WHERE {{
    ?thesis etd:slug "{0}" .
    ?thesis etd:additional-note ?note .
}}"""

ADVISOR_EMAIL = PREFIX + """
SELECT DISTINCT ?email
WHERE {{
    <{0}> schema:email ?email .
}}"""

ADVISOR_NAME = PREFIX + """
SELECT DISTINCT ?name
WHERE {{
    <{0}> rdfs:label ?name .
}}"""

COLLECTION_PID = PREFIX + """
SELECT DISTINCT ?pid
WHERE {{
    ?thesis etd:slug "{0}" ;
            etd:fedora38-pid ?pid .
     ?theses etd:theses ?thesis ;
            schema:superEvent ?dept_year .
    ?dept_year schema:superEvent ?academic_year .
    ?academic_year schema:startDate ?start_date .
    ?academic_year schema:endDate ?end_date .
    FILTER (?start_date < "{1}"^^xsd:dateTime)
    FILTER (?end_date > "{1}"^^xsd:dateTime)
}}"""

DEGREE_INFO = PREFIX + """
SELECT DISTINCT ?type ?name
WHERE {{
    ?thesis etd:slug "{0}" .
    ?thesis etd:degree-name ?name .
    ?thesis etd:degree-type ?type .
}}"""

DEPARTMENT_FACULTY = PREFIX + """
SELECT DISTINCT ?person_iri ?name
WHERE {{
    ?person_iri rdfs:label ?name .
    ?person_iri schema:familyName ?lname .
    ?dept_year schema:organizer ?org .
    ?dept_year schema:superEvent ?academic_year .
    ?academic_year schema:startDate ?start_date .
    ?academic_year schema:endDate ?end_date .
    ?etd schema:organizer ?org .
    {{ ?dept_year cc_fac:assistant-professor ?person_iri }}
    UNION
    {{ ?dept_year cc_fac:associate-professor ?person_iri }}
    UNION
    {{ ?dept_year cc_fac:professor ?person_iri }}
    UNION
    {{ ?dept_year cc_fac:visiting-assistant-professor ?person_iri }}
    UNION
    {{ ?etd cc_fac:faculty ?person_iri }}
    FILTER (?start_date < "{1}"^^xsd:dateTime)
    FILTER (?end_date > "{1}"^^xsd:dateTime)
    FILTER NOT EXISTS {{ ?etd etd:exclude ?person_iri . }}
    BIND(<{0}> as ?org)
}} ORDER BY ?lname
"""

DEPARTMENT_IRI = PREFIX + """
SELECT DISTINCT ?iri
WHERE {{
    ?thesis etd:slug "{0}" .
    ?year etd:theses ?thesis .
    ?year schema:organizer ?iri .
}}"""


DEPARTMENT_NAME = PREFIX + """
SELECT DISTINCT ?name
WHERE {{
    ?thesis etd:slug "{0}" .
    ?year etd:theses ?thesis .
    ?year schema:organizer ?iri .
    ?iri rdfs:label ?name .
}}"""

DEPARTMENT_STAFF = PREFIX + """
SELECT DISTINCT ?name ?email
WHERE {{
    ?thesis etd:slug "{0}" .
    ?workflow etd:theses ?thesis .
    ?workflow etd:contact ?person .
    ?person rdfs:label ?name .
    ?person schema:email ?email .
}}"""

FACULTY_EXCLUDE = PREFIX + """
SELECT DISTINCT ?person
WHERE {{
    ?dept_year schema:organizer ?org .
    ?dept_year schema:superEvent ?academic_year .
    ?academic_year schema:startDate ?start_date .
    ?academic_year schema:endDate ?end_date .
    ?etd schema:organizer ?org ;
         etd:exclude ?person .
    FILTER (?start_date < "{1}"^^xsd:dateTime)
    FILTER (?end_date > "{1}"^^xsd:dateTime)
    BIND(<{0}> as ?org)
}}"""

GRAD_DATES = PREFIX + """
SELECT DISTINCT ?date ?label
WHERE {{
     ?year schema:organizer <{0}> .
     ?year schema:superEvent ?academic_year .
     ?academic_year cc_info:graduation ?grad .
     ?grad rdf:value ?date .
     ?grad rdfs:label ?label .
     ?academic_year schema:startDate ?start_date .
     ?academic_year schema:endDate ?end_date .
     FILTER (?start_date < "{1}"^^xsd:dateTime)
     FILTER (?end_date > "{1}"^^xsd:dateTime)

}} ORDER BY ?date
"""

LANG_LABEL = PREFIX + """
SELECT DISTINCT ?language
WHERE {{
    <{0}> rdfs:label ?language .
}}"""

THESIS_LANGUAGES = PREFIX + """
SELECT DISTINCT ?iri ?label
WHERE {{
    ?thesis etd:slug "{0}" .
    ?thesis etd:language ?iri .
    ?iri rdfs:label ?label .
}} ORDER BY ?label
"""

THESES_LIST = PREFIX + """

SELECT DISTINCT ?dept_name ?label ?slug
WHERE {
    ?dept_year etd:theses ?thesis .
    ?dept_year schema:organizer ?dept .
    ?dept rdfs:label ?dept_name .
    ?thesis etd:slug ?slug .
    OPTIONAL { ?thesis rdfs:label ?label }
} ORDER BY ?dept_name
"""

THESIS_NOTE = PREFIX + """
SELECT DISTINCT ?note
WHERE {{
    ?thesis etd:slug "{0}" .
    ?thesis etd:thesis-note ?note .
}}"""
