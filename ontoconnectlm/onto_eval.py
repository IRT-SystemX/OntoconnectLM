import requests
import rdflib
import pandas as pd
import os

FOOPS_URL = "https://foops.linkeddata.es/assessOntology"
OOPS_URL = "https://oops.linkeddata.es"
OOPS_URI = "http://oops.linkeddata.es"
OOPS_QUERY_FILEPATH = "ontology_evaluation/oops_query_template.txt"


class Onto_Evaluator:

    """
    Evaluate an ontology file. It offers two kinds of evaluations. 
    Input: 
    Capabilities: 
    - Load the ontology file 
    - Run the OOPS! evaluation tool via API, check the content and retrieve results
    - Run the FOOOPs! tool via API, check the meetadata and retrieve results
    Output: Evaluation ontology-based pitfalls and FAIR metrics

    """

    def __init__(self, ontology_content : str ,ontology_uri : str):

        self.foops_url = FOOPS_URL
        self.oops_url = OOPS_URL
        self.oops_uri = OOPS_URI
        self.oops_query_filepath = OOPS_QUERY_FILEPATH
        self.ontology_conrtent = ontology_content
        self.onto_uri = ontology_uri


    def eval_fair(self, output_excel: str) -> pd.DataFrame:
        try:
            headers = {
                "Content-Type": "application/json; charset=utf-8"
            }
            data = {
                "ontologyContent": self.ontology_conrtent,
                "ontologyUri" : self.onto_uri,
                "ontologyFormat": "rdfxml"
            }

            response_foops = requests.post(
                url=self.foops_url,
                headers=headers,
                json=data
            )

            if response_foops.status_code != 200:
                print(f"Erreur HTTP {response_foops.status_code}")
                print(response_foops.text)
                return pd.DataFrame()

            response_data_foops = response_foops.json()
            overall_score_foops = response_data_foops.get("overall_score", 0) * 100

            rows = []
            for check in response_data_foops.get("checks", []):
                total_tests = check.get("total_tests_run", 0)
                passed_tests = check.get("total_passed_tests", 0)
                current_metric_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
                status = "FAILED" if check.get("status") == "error" and passed_tests == 0 else "PASSED"

                rows.append({
                    "Principle": check.get("principle_id", "unknown"),
                    "Metric": check["id"],
                    "Score (%)": current_metric_score,
                    "Status": status,
                    "Description": check.get("description", ""),
                    "Explanation": check.get("explanation", "")
                })

            df = pd.DataFrame(rows)
            with pd.ExcelWriter(output_excel) as writer:
                df.to_excel(writer, index=False, sheet_name="FOOPS Results")
                pd.DataFrame([{
                    "Tool": "FOOPS",
                    "Overall Score (%)": overall_score_foops
                }]).to_excel(writer, index=False, sheet_name="Summary")

            # print(f"Résultats FOOPS exportés dans {output_excel}")
            return df

        except Exception as e:
            print(f"Erreur FOOPS: {e}")
            return pd.DataFrame()



    def eval_oops(self, output_excel: str) -> pd.DataFrame:
        try:

            path = os.path.join(os.path.dirname(__file__), self.oops_query_filepath)

            with open(path, 'r') as read_file:
                query = read_file.read()

            formatted_query = query.format(owl_content = self.ontology_conrtent)
            # print("Formatted query : ")
            # print(formatted_query)

            headers = {
                "Content-Type": "application/xml",
                "Accept": "application/xml"
            }

            response = requests.post(self.oops_url + "/rest", data=formatted_query.encode("utf-8"), headers=headers)
            # print(response.text)

            if response.status_code != 200:
                print(f"Erreur HTTP {response.status_code}")
                print(response.text)
                return pd.DataFrame()

            g = rdflib.Graph()
            g.parse(data=response.text, format="xml")

            rows = []
            for s in g.subjects(rdflib.RDF.type, rdflib.URIRef(self.oops_uri + "/def#pitfall")):
                rows.append({
                    "Code": str(g.value(s, rdflib.URIRef(self.oops_uri + "/def#hasCode"))),
                    "Pitfall": str(g.value(s, rdflib.URIRef(self.oops_uri + "/def#hasName"))),
                    "Importance": str(g.value(s, rdflib.URIRef(self.oops_uri + "/def#hasImportanceLevel"))),
                    "Description": str(g.value(s, rdflib.URIRef(self.oops_uri + "/def#hasDescription"))),
                    "Affected Elements": str(g.value(s, rdflib.URIRef(self.oops_uri + "/def#hasNumberAffectedElements")))
                })

            df = pd.DataFrame(rows)
            with pd.ExcelWriter(output_excel) as writer:
                df.to_excel(writer, index=False, sheet_name="OOPS Results")
                pd.DataFrame([{
                    "Tool": "OOPS",
                    "Total Pitfalls": len(df)
                }]).to_excel(writer, index=False, sheet_name="Summary")

            # print(f"Résultats OOPS exportés dans {output_excel}")
            return df

        except Exception as e:
            print(f"Erreur OOPS: {e}")
            return pd.DataFrame()
