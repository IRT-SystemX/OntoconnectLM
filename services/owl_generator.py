from typing import List
from owlapy.iri import IRI
from owlapy.owl_ontology import Ontology
from owlapy.class_expression import OWLClass
from owlapy.owl_property import OWLObjectProperty, OWLDataProperty
from owlapy.owl_literal import OWLLiteral 
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_axiom import OWLDeclarationAxiom , OWLClassAssertionAxiom, OWLObjectPropertyAssertionAxiom, OWLDataPropertyAssertionAxiom, OWLObjectPropertyDomainAxiom, OWLObjectPropertyRangeAxiom, OWLAnnotationProperty, OWLAnnotationAssertionAxiom
from owlapy.util_owl_static_funcs import create_ontology

from named_individuals import NamedIndividual

class OwlGenerator:
    """
    Service aiming to transform triples into owl ontology

    Input : List of triples (entity1 ; relation ; entity2) + configuration file
    Output: Ontology in OWL format
    
    """

    def __init__(self, triples : List[dict], config : dict, onto_uri : str = "http://smd#"):

        self.triples = triples

        # Récupération du dictionnaire de config

        if "entity_linker" in config.keys():
            self.entity_linker = config["entity_linker"]
        else:
            raise KeyError("No entity_linker in config file")
        
        if "additional_classes" in config.keys():
            self.additional_classes = config["additional_classes"]
        else:
            print("No additional_classes found in config.")
            self.additional_classes = []

        if "additional_properties" in config.keys():
            self.additional_properties = config["additional_properties"]
        else:
            print("No additional_properties found in config.")
            self.additional_properties = []

        # Initializing OwlApi objects
        self.ontology = Ontology(IRI.create(onto_uri), load=False)

        self.onto_uri = onto_uri

    # Fonction de récupération de tous les types d'entités trouvés
    def get_entity_types(self) -> list:
        list_types = []
        for triplet in self.triples:
            if triplet["head_type"] not in list_types:
                list_types.append(triplet["head_type"])
            if triplet["tail_type"] not in list_types:
                list_types.append(triplet["tail_type"])

        return list_types
    
    def entity_linking(self, entity_type : str) -> str:
        entity_type = entity_type.lower()

        if entity_type in self.entity_linker.keys():
            return self.entity_linker[entity_type]
        else:
            if "other" in self.entity_linker.keys():
                return self.entity_linker["other"]
            else:
                return "unknown"
    

    def define_classes(self, entity_types : List[str]):
            self.classes = {}

            for ent_type in entity_types:

                nom_classe = self.entity_linking(ent_type)
                iri = IRI(self.onto_uri, nom_classe)

                new_class = OWLClass(iri)
                self.classes[ent_type] = new_class

                new_class_declaration_axiom = OWLDeclarationAxiom(new_class)
                
                self.ontology.add_axiom(new_class_declaration_axiom)

            # Ajout des classes supplémentaires
            for additional_class in self.additional_classes:
                iri = IRI(self.onto_uri, additional_class)

                new_class = OWLClass(iri)
                self.classes[additional_class] = new_class

                new_class_declaration_axiom = OWLDeclarationAxiom(new_class)
                
                self.ontology.add_axiom(new_class_declaration_axiom)

    
    # def define_individuals(self , named_individuals  , onto=None , manager=None , uri_onto="http://smd#") :
    #     individuals = {}

    #     for ni in named_individuals.values():
    #         if ni.ent_type in self.classes.keys():
    #             classe = self.classes[ni.ent_type]

    #             # Définition de l'Individual
    #             new_iri = IRI.create(uri_onto , ni.id)
    #             new_individual = OWLNamedIndividual(new_iri)
    #             individuals[ni.id] = new_individual
    #             class_assertion_axiom = OWLClassAssertionAxiom(new_individual, self.classes[ni.ent_type])
    #             self.onto.add_axiom(class_assertion_axiom)

    #             # Attribution du label de l'individual
    #             label = OWLLiteral(ni.nom)
    #             annotation_iri = OWLDataProperty(IRI("http://www.w3.org/2000/01/rdf-schema#","label"))
                
    #             annotation_axiom = OWLDataPropertyAssertionAxiom(new_individual,annotation_iri,label)
    #             self.onto.add_axiom(annotation_axiom)

    #             # if mode_data == 'data':
    #             #     # Extraction de la valeur data
    #             #     try:
    #             #         use_case_class = NamedIndividual.get_use_case_class(self.use_case_name)
    #             #         valeur_originale , valeur_numérique = use_case_class.parse_datatype_value(ni.nom)
    #             #     except Exception:
    #             #         valeur_originale = ni.nom
    #             #         valeur_numérique = "Value Error"

    #             #     individuals[ni.id] = {"valeur originale" : valeur_originale,
    #             #                         "valeur numérique" : OWLLiteral(valeur_numérique)}


    #         else: 
    #             # Cas où c'est un littéral

    #             # try:
    #             #     use_case_class = NamedIndividual.get_use_case_class(self.use_case_name)
    #             #     valeur_originale , valeur_numérique = use_case_class.parse_datatype_value(ni.nom)
    #             # except Exception :
    #             #     valeur_originale = ni.nom
    #             #     valeur_numérique = "Value Error"

    #             # individuals[ni.id] = {"valeur originale" : valeur_originale,
    #             #                     "valeur numérique" : OWLLiteral(valeur_numérique)}

    #             pass

            
    #     return individuals


    def get_properties(self, named_individuals):
            properties = {}

            # First gets all relations : label / classe ind head / classe ind tail
            all_relations = []
            for ind in named_individuals.values():
                for tail,label_relation in ind.relations.items():
                    if label_relation not in all_relations:
                        all_relations.append(label_relation)
                    
            all_relations = all_relations + [property["name"] for property in self.additional_properties]

            # Suppression des espaces
            all_relations = [ relation.replace(" ","_").lower() for relation in all_relations]

            for relation in all_relations:
                new_obj_prop = OWLObjectProperty(IRI(self.onto_uri, relation))
                properties[relation] = new_obj_prop
                new_obj_prop_declaration_axiom = OWLDeclarationAxiom(new_obj_prop)
                self.ontology.add_axiom(new_obj_prop_declaration_axiom)

            # Adding domain and range of additional properties
            for relation_dict in self.additional_properties:
                relation_dict["name"] = relation_dict["name"].replace(" ","_").lower()

            for property in self.additional_properties:
                domain_axiom = OWLObjectPropertyDomainAxiom(properties[property["name"]], OWLClass(IRI(self.onto_uri, property["domain"])))
                self.ontology.add_axiom(domain_axiom)

                range_axiom = OWLObjectPropertyRangeAxiom(properties[property["name"]], OWLClass(IRI(self.onto_uri, property["range"])))
                self.ontology.add_axiom(range_axiom)

                            
            return properties
    
    def define_dc_annotation_properties(self):
        
        # dc1_props = {}
        # dc_uri1_1 = "http://purl.org/dc/elements/1.1#"
        # for prop_name in ["contributor", "coverage", "creator", "date", "description", "format", "identifier", "language",
        #                   "publisher", "relation", "rights", "source", "subject", "title", "type"]:

        #     new_annotation_property = OWLAnnotationProperty(IRI(dc_uri1_1 , prop_name))
        #     dc1_props[prop_name] = new_annotation_property
        #     annot_axiom = OWLDeclarationAxiom(new_annotation_property)
        #     self.ontology.add_axiom(annot_axiom)

        # dc_uri = "http://purl.org/dc/terms#"

        # other_props = {
        #     "abstract" : {"sub" : "1.1description"}
        # }

        # for prop_name, subclasses in .items():

        #     new_annotation_property = OWLAnnotationProperty(IRI(dc_uri , prop_name))
        #     annot_axiom = OWLDeclarationAxiom(new_annotation_property)
        #     self.ontology.add_axiom(annot_axiom)

        with open("temp.owl" , 'r') as rf:
            text = rf.read()

        onto_text, _ = text.split("</rdf:RDF>")

        dc_text_to_insert = """<owl:AnnotationProperty rdf:about="http://purl.org/dc/elements/1.1/contributor"/>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/elements/1.1/coverage"/>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/elements/1.1/creator"/>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/elements/1.1/date"/>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/elements/1.1/description"/>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/elements/1.1/format"/>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/elements/1.1/identifier"/>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/elements/1.1/language"/>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/elements/1.1/publisher"/>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/elements/1.1/relation"/>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/elements/1.1/rights"/>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/elements/1.1/source"/>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/elements/1.1/subject"/>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/elements/1.1/title"/>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/elements/1.1/type"/>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/abstract">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/description"/>
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/terms/description"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/description">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/description"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/accessRights">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/rights"/>
  <rdfs:range rdf:resource="http://purl.org/dc/terms/RightsStatement"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/alternative">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/title"/>
  <rdfs:range rdf:resource="http://www.w3.org/2000/01/rdf-schema#Literal"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/available">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/date"/>
  <rdfs:range rdf:resource="http://www.w3.org/2000/01/rdf-schema#Literal"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/bibliographicCitation">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/identifier"/>
  <rdfs:range rdf:resource="http://www.w3.org/2000/01/rdf-schema#Literal"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/conformsTo">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/relation"/>
  <rdfs:range rdf:resource="http://purl.org/dc/terms/Standard"/>
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/terms/relation"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/relation">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/relation"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/contributor">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/contributor"/>
  <rdfs:range rdf:resource="http://purl.org/dc/terms/Agent"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/coverage">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/coverage"/>
  <rdfs:range rdf:resource="http://purl.org/dc/terms/LocationPeriodOrJurisdiction"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/created">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/date"/>
  <rdfs:range rdf:resource="http://www.w3.org/2000/01/rdf-schema#Literal"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/creator">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/creator"/>
  <rdfs:range rdf:resource="http://purl.org/dc/terms/Agent"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/date">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/date"/>
  <rdfs:range rdf:resource="http://www.w3.org/2000/01/rdf-schema#Literal"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/dateAccepted">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/date"/>
  <rdfs:range rdf:resource="http://www.w3.org/2000/01/rdf-schema#Literal"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/dateCopyrighted">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/date"/>
  <rdfs:range rdf:resource="http://www.w3.org/2000/01/rdf-schema#Literal"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/dateSubmitted">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/date"/>
  <rdfs:range rdf:resource="http://www.w3.org/2000/01/rdf-schema#Literal"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/extent">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/format"/>
  <rdfs:range rdf:resource="http://purl.org/dc/terms/SizeOrDuration"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/format">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/format"/>
  <rdfs:range rdf:resource="http://purl.org/dc/terms/MediaTypeOrExtent"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/hasFormat">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/relation"/>
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/terms/relation"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/hasPart">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/relation"/>
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/terms/relation"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/hasVersion">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/relation"/>
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/terms/relation"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/identifier">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/identifier"/>
  <rdfs:range rdf:resource="http://www.w3.org/2000/01/rdf-schema#Literal"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/isFormatOf">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/relation"/>
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/terms/relation"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/isPartOf">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/relation"/>
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/terms/relation"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/isReferencedBy">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/relation"/>
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/terms/relation"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/isReplacedBy">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/relation"/>
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/terms/relation"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/isRequiredBy">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/relation"/>
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/terms/relation"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/isVersionOf">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/relation"/>
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/terms/relation"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/issued">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/date"/>
  <rdfs:range rdf:resource="http://www.w3.org/2000/01/rdf-schema#Literal"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/language">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/language"/>
  <rdfs:range rdf:resource="http://purl.org/dc/terms/LinguisticSystem"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/license">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/rights"/>
  <rdfs:range rdf:resource="http://purl.org/dc/terms/LicenseDocument"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/medium">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/format"/>
  <rdfs:range rdf:resource="http://purl.org/dc/terms/PhysicalMedium"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/modified">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/date"/>
  <rdfs:range rdf:resource="http://www.w3.org/2000/01/rdf-schema#Literal"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/publisher">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/publisher"/>
  <rdfs:range rdf:resource="http://purl.org/dc/terms/Agent"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/references">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/relation"/>
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/terms/relation"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/replaces">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/relation"/>
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/terms/relation"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/requires">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/relation"/>
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/terms/relation"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/rights">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/rights"/>
  <rdfs:range rdf:resource="http://purl.org/dc/terms/RightsStatement"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/source">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/source"/>
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/terms/relation"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/spatial">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/coverage"/>
  <rdfs:range rdf:resource="http://purl.org/dc/terms/Location"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/subject">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/subject"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/tableOfContents">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/description"/>
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/terms/description"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/temporal">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/coverage"/>
  <rdfs:range rdf:resource="http://purl.org/dc/terms/PeriodOfTime"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/title">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/title"/>
  <rdfs:range rdf:resource="http://www.w3.org/2000/01/rdf-schema#Literal"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/type">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/type"/>
  <rdfs:range rdf:resource="http://www.w3.org/2000/01/rdf-schema#Class"/>
</owl:AnnotationProperty>

<owl:AnnotationProperty rdf:about="http://purl.org/dc/terms/valid">
  <rdfs:subPropertyOf rdf:resource="http://purl.org/dc/elements/1.1/date"/>
  <rdfs:range rdf:resource="http://www.w3.org/2000/01/rdf-schema#Literal"/>
</owl:AnnotationProperty>"""

        onto_text += dc_text_to_insert
        onto_text += "\n"
        onto_text += "</rdf:RDF>"

        with open("temp.owl" , 'w') as wf:
            wf.write(onto_text)

    

    def define_individuals(self , named_individuals) :
        individuals = {}

        # Définition de la propriété "has text"
        has_text_data_property = OWLDataProperty(IRI(self.onto_uri,"has_text"))
        has_text_declaration_axiom = OWLDeclarationAxiom(has_text_data_property)
        self.ontology.add_axiom(has_text_declaration_axiom)
        
        for ni_text, ni in named_individuals.items():

            # Définition de l'Individual
            new_iri = IRI.create(self.onto_uri , ni.id)
            new_individual = OWLNamedIndividual(new_iri)
            individuals[ni_text] = new_individual
            class_assertion_axiom = OWLClassAssertionAxiom(new_individual, self.classes[ni.ent_type])
            self.ontology.add_axiom(class_assertion_axiom)

            # Attribution du label de l'individual
            label = OWLLiteral(ni.nom)
            annotation_iri = OWLDataProperty(IRI("http://www.w3.org/2000/01/rdf-schema#","label"))
        
            annotation_axiom = OWLDataPropertyAssertionAxiom(new_individual,annotation_iri,label)
            self.ontology.add_axiom(annotation_axiom)

            # Attribution de la propriété 'has text'
            has_text_axiom = OWLDataPropertyAssertionAxiom(new_individual , has_text_data_property , OWLLiteral(ni.nom))
            self.ontology.add_axiom(has_text_axiom)
            
        return individuals
    

    def define_relations(self, found_named_individuals, onto_individuals, object_properties):
        """
        Defines relations for owlready/ontolearn libraries. 

        Parameters:
        found_named_individuals : entities listed in text format in which relations are specified
        onto_individuals : entities in owlapy format
        object_properties : list of owlapy object properties linked to their textual label
        """
    
        for id,owl_named_individual in onto_individuals.items():

            for other_individual,label_relation in found_named_individuals[id].relations.items():

                object_property = object_properties[label_relation]

                position_other_individual = list(found_named_individuals.values()).index(other_individual)
                # id_other_individual = list(found_named_individuals.values())[position_other_individual].id
                # owl_other_individual = onto_individuals[id_other_individual]
                name_other_individual = list(found_named_individuals.values())[position_other_individual].nom
                owl_other_individual = onto_individuals[name_other_individual]


                # Case ObejctProperty
                if isinstance( object_property , OWLObjectProperty):
                    new_axiom = OWLObjectPropertyAssertionAxiom(owl_named_individual , object_property , owl_other_individual)
                    comment_axiom = None                                                         

                # Case DataProperty
                elif isinstance( object_property , OWLDataProperty):
                    if isinstance(owl_other_individual ,dict):
                        new_axiom = OWLDataPropertyAssertionAxiom(owl_named_individual , object_property , owl_other_individual["valeur numérique"])
                        comment_data_property = OWLDataProperty(IRI("http://www.w3.org/2000/01/rdf-schema#","comment"))
                        comment_axiom = OWLDataPropertyAssertionAxiom(owl_named_individual , comment_data_property , OWLLiteral(label_relation + " " + owl_other_individual["valeur originale"]))
                    else:
                        new_axiom = OWLDataPropertyAssertionAxiom(owl_named_individual , object_property , owl_other_individual)
                        comment_axiom = None                                                         
                else:
                    raise ValueError("Wrong type of property for : " + str(object_property))
                                       
                 
                try:
                    self.ontology.add_axiom(new_axiom)
                    if comment_axiom is not None:
                        self.ontology.add_axiom(comment_axiom)
                except Exception:
                    print("Wrong type of property : " + str(object_property) + " linking " + id + " and " + id_other_individual)



    def create_ontology(self):

        entity_types = self.get_entity_types()

        self.define_classes(entity_types=entity_types)

        found_named_individuals = NamedIndividual.get_named_individuals(triples=self.triples , OwlGeneratorObject=self)

        properties = self.get_properties(named_individuals=found_named_individuals)

        self.define_dc_annotation_properties()

        individuals = self.define_individuals(found_named_individuals)

        self.define_relations(found_named_individuals=found_named_individuals,
                               onto_individuals=individuals,
                               object_properties=properties)
        
        # Export : seulement en écriture de fichier
        self.ontology.save("temp.owl" , inplace=False )

        self.define_dc_annotation_properties()

        with open("temp.owl" , "r") as read_file:
            return read_file.read()