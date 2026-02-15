"""
Ontology Schema Definition
Defines the ISPS ontology using RDFLib with classes and properties for
strategic plan entities and their relationships.
"""
from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS, OWL, XSD

# Namespace
ISPS = Namespace("http://isps.greenfield.ac.uk/ontology#")


def create_ontology_graph() -> Graph:
    """Create a new RDF graph with the ISPS ontology schema."""
    g = Graph()
    g.bind("isps", ISPS)
    g.bind("owl", OWL)
    g.bind("rdfs", RDFS)
    
    # ─── Classes ─────────────────────────────────────────────────────────────
    classes = [
        ("StrategicPlan", "A comprehensive strategic plan document"),
        ("ActionPlan", "An action plan document implementing a strategic plan"),
        ("StrategicObjective", "A high-level strategic objective"),
        ("Action", "A specific action item in the action plan"),
        ("KPI", "A key performance indicator with targets"),
        ("Milestone", "A timeline milestone within an objective"),
        ("Risk", "A risk identified in the action plan"),
        ("Department", "An organizational department"),
        ("Person", "An individual responsible for actions"),
    ]
    
    for class_name, description in classes:
        uri = ISPS[class_name]
        g.add((uri, RDF.type, OWL.Class))
        g.add((uri, RDFS.label, Literal(class_name)))
        g.add((uri, RDFS.comment, Literal(description)))
    
    # ─── Object Properties ───────────────────────────────────────────────────
    object_properties = [
        ("hasObjective", "StrategicPlan", "StrategicObjective", "Links plan to its objectives"),
        ("hasAction", "ActionPlan", "Action", "Links action plan to its actions"),
        ("hasKPI", "StrategicObjective", "KPI", "Links objective to its KPIs"),
        ("hasMilestone", "StrategicObjective", "Milestone", "Links objective to milestones"),
        ("hasRisk", "ActionPlan", "Risk", "Links action plan to identified risks"),
        ("supportsObjective", "Action", "StrategicObjective", "Links an action to the objective it supports"),
        ("supportsKPI", "Action", "KPI", "Links an action to the KPI it supports"),
        ("ownedBy", "Action", "Person", "Assigns ownership of an action"),
        ("belongsToDepartment", "Person", "Department", "Links person to their department"),
        ("dependsOn", "Action", "Action", "Dependency between actions"),
        ("mitigates", "Action", "Risk", "Links action to risk it mitigates"),
    ]
    
    for prop_name, domain, range_, description in object_properties:
        uri = ISPS[prop_name]
        g.add((uri, RDF.type, OWL.ObjectProperty))
        g.add((uri, RDFS.domain, ISPS[domain]))
        g.add((uri, RDFS.range, ISPS[range_]))
        g.add((uri, RDFS.label, Literal(prop_name)))
        g.add((uri, RDFS.comment, Literal(description)))
    
    # ─── Datatype Properties ─────────────────────────────────────────────────
    datatype_properties = [
        ("hasTitle", "StrategicObjective", XSD.string, "Title of the objective"),
        ("hasDescription", "StrategicObjective", XSD.string, "Description text"),
        ("hasTarget", "KPI", XSD.string, "Target value for the KPI"),
        ("hasBaseline", "KPI", XSD.string, "Baseline value for the KPI"),
        ("hasCurrentValue", "KPI", XSD.string, "Current measured value"),
        ("hasDeadline", "Action", XSD.date, "Deadline for the action"),
        ("hasStatus", "Action", XSD.string, "Current status of the action"),
        ("hasProgress", "Action", XSD.integer, "Progress percentage (0-100)"),
        ("hasBudget", "Action", XSD.string, "Budget allocated to the action"),
        ("hasPriority", "Action", XSD.string, "Priority level (High/Medium/Low)"),
        ("hasRiskLevel", "Risk", XSD.string, "Risk severity level"),
        ("hasLikelihood", "Risk", XSD.string, "Risk likelihood"),
        ("alignmentScore", "Action", XSD.float, "Computed alignment score (0-1)"),
        ("alignmentLevel", "StrategicObjective", XSD.string, "Full/Partial/Weak/Missing"),
    ]
    
    for prop_name, domain, range_, description in datatype_properties:
        uri = ISPS[prop_name]
        g.add((uri, RDF.type, OWL.DatatypeProperty))
        g.add((uri, RDFS.domain, ISPS[domain]))
        g.add((uri, RDFS.range, range_))
        g.add((uri, RDFS.label, Literal(prop_name)))
        g.add((uri, RDFS.comment, Literal(description)))
    
    return g
