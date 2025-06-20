from owlready2 import get_ontology
from rdflib import Graph


class OntologyChangeTracker:

    """
    Service aiming to encoding changes between ontology versions 
    Input: older ontology version and newer one
    Capabilities:
    * Load the ontology and graph content
    * Compare entities, relations and individuals
    * Report the changes 
    Output: display entity changes and triple changes 
    """
       
    def __init__(self, old_onto_path, new_onto_path):
        self.old_path = old_onto_path
        self.new_path = new_onto_path
        self.onto1 = get_ontology(self.old_path).load()
        self.onto2 = get_ontology(self.new_path).load()
        self._load_entities()

    def _load_entities(self):
        self.classes_v1 = {cls.name for cls in self.onto1.classes()}
        self.classes_v2 = {cls.name for cls in self.onto2.classes()}

        self.properties_v1 = {prop.name for prop in self.onto1.properties()}
        self.properties_v2 = {prop.name for prop in self.onto2.properties()}

        self.individuals_v1 = {ind.name for ind in self.onto1.individuals()}
        self.individuals_v2 = {ind.name for ind in self.onto2.individuals()}

        self.graph1 = Graph()
        self.graph1.parse(self.old_path, format="xml")

        self.graph2 = Graph()
        self.graph2.parse(self.new_path, format="xml")

        self.triplets_v1 = set(self.graph1)
        self.triplets_v2 = set(self.graph2)

    def compare_entities(self):
        return {
            "added_classes": self.classes_v2 - self.classes_v1,
            "removed_classes": self.classes_v1 - self.classes_v2,
            "added_properties": self.properties_v2 - self.properties_v1,
            "removed_properties": self.properties_v1 - self.properties_v2,
            "added_individuals": self.individuals_v2 - self.individuals_v1,
            "removed_individuals": self.individuals_v1 - self.individuals_v2,
        }

    def compare_triples(self):
        return {
            "added_triples": self.triplets_v2 - self.triplets_v1,
            "removed_triples": self.triplets_v1 - self.triplets_v2
        }

    def report_changes(self):      
        triples_diff = self.compare_triples()

        entities_diff = self.compare_entities()
        triples_diff = self.compare_triples()

        print("***ENTITY CHANGES***")
        for key, value in entities_diff.items():
            print(f"{key.title()}: {len(value)}")
            #if value:
            # print("  ", value)
            
        print("***TRIPLE CHANGES***")
        print(f"Added Triples: {len(triples_diff['added_triples'])}")
        #for triple in triples_diff['added_triples']:
        #  print("  ", triple)
        print(f"Removed Triples: {len(triples_diff['removed_triples'])}")
        #{for triple in triples_diff['removed_triples']:
        #  print("  ", triple)

