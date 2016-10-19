__author__ = "Jeremy Nelson"

PREFIX = """PREFIX bf: <http://id.loc.gov/ontologies/bibframe/>
PREFIX cc_fac: <https://www.coloradocollege.edu/ns/faculty/> 
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> 
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
PREFIX schema: <http://schema.org/>"""

DEPARTMENT_FACULTY = PREFIX + """
SELECT DISTINCT ?person_iri ?name
WHERE {{
    ?person_iri rdfs:label ?name .
    ?person_iri schema:familyName ?lname .
    ?dept_year schema:organizer <{0}> .
    ?dept_year schema:superEvent ?academic_year .
    ?academic_year schema:startDate ?start_date .
    ?academic_year schema:endDate ?end_date .
    {{ ?dept_year cc_fac:assistant-professor ?person_iri }}
    UNION
    {{ ?dept_year cc_fac:associate-professor ?person_iri }}
    UNION
    {{ ?dept_year cc_fac:professor ?person_iri }}
    UNION 
    {{ ?dept_year cc_fac:visiting-assistant-professor ?person_iri }}
    FILTER (?start_date < "{1}")
    FILTER (?end_date > "{1}")
}} ORDER BY ?lname
"""

DEPARTMENT_LIST = PREFIX + """
SELECT DISTINCT ?iri ?label
WHERE {{
    ?iri rdf:type schema:CollegeDepartment .
    ?iri rdfs:label ?label .
}} ORDER BY ?label
"""
