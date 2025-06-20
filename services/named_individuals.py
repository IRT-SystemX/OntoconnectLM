from random import randint
from datetime import datetime

# Objet représentant les noeuds dans le graphe
# Doit etre unique : il possède un id unique dans le graphe
# Le dictionnaire relations indique avec quels autres noeuds il est relié et quelle est la nature de cette relation
class NamedIndividual():
    id : str
    nom : str
    classe : str
    ent_type : str
    relations : dict
    namespace : str

    def __init__(self,nom,classe,ent_type,id,namespace=''):
        self.nom = nom
        self.filter_unwanted_characters()   

        self.classe = classe
        self.ent_type = ent_type
        self.relations = {}
        self.id = id
        self.namespace = namespace

    def add_relation(self,relation,tail):           # Remplissage du dictionnaire relations pour indiquer une relation avec un autre noeud
        if tail not in self.relations.keys():
            self.relations[tail] = relation

    @property
    def full_name(self):
        return "<" + self.namespace + self.id.replace(":","") + ">"

    @staticmethod
    def generate_id(clas,liste_ids) -> str:
        unicity_flag = False
        while not unicity_flag:
            generated_id = clas + str(randint(10,999))
            if generated_id not in liste_ids:
                unicity_flag = True

        return generated_id
    

   
    def filter_unwanted_characters(self):
        # Removes characters which would be wrongly interpreted by the OWL syntax
        
        self.nom = self.nom.replace("<","inférieur à ")
        self.nom = self.nom.replace(">","supérieur à ")

    
    @staticmethod
    def get_named_individuals(triples , OwlGeneratorObject):
        """
        Fonction de récupération de tous les named individuals (ou entités) présentes dans
        le jeu de données de sortie
        """
        all_named_individuals = {}
        liste_ids = []


        for triplet in triples:
            # Si le triplet est complet
            if all([key in triplet.keys() for key in ["label", "head" , "head_type", "tail", "tail_type"]]):
                try:
                    
                    head_name = triplet["head"]
                    clas = OwlGeneratorObject.entity_linking(triplet["head_type"])
                    id = NamedIndividual.generate_id(clas,liste_ids)

                    if head_name not in all_named_individuals.keys():
                        # namespace = Owlcreator_obj.namespaces[clas.split(":")[0]]
                        all_named_individuals[head_name] = NamedIndividual(nom=head_name,classe = clas, ent_type = triplet["head_type"], id=id)
                        liste_ids.append(id)

                    head = all_named_individuals[head_name]

                    tail_name = triplet["tail"]
                    clas = OwlGeneratorObject.entity_linking(triplet["tail_type"])
                    id = NamedIndividual.generate_id(clas,liste_ids)
                    if tail_name not in all_named_individuals.keys():
                        # namespace = Owlcreator_obj.namespaces[clas.split(":")[0]]
                        all_named_individuals[tail_name] = NamedIndividual(nom=tail_name,classe = clas, ent_type=triplet["tail_type"], id=id)
                        liste_ids.append(id) 

                    tail = all_named_individuals[tail_name]
                    # label = "smd:" + triplet["label"].replace(" ","_")
                    label = triplet["label"].replace(" ","_").lower()
                    head.add_relation(label,tail)

                except Exception as E:
                    print("Erreur : ",E," concernant : ",triplet,'\n')

            else:
                print("Skipping incomplete triplet")


        return all_named_individuals




    