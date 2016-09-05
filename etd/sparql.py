__author__ = "Jeremy Nelson"

PREFIX = """PREFIX bf: <http://id.loc.gov/ontologies/bibframe/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> 
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
PREFIX schema: <http://schema.org/>"""

DEPARTMENT_LIST = PREFIX + """
SELECT DISTINCT ?iri ?label
WHERE {{
    ?iri rdf:type schema:CollegeDepartment .
    ?iri rdfs:label ?label .
}} ORDER BY ?label
"""
