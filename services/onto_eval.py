import json
import requests
from requests.exceptions import HTTPError
import rdflib
import pandas as pd

class eval:

    """
    Service aiming to evaluate an ontology file. It offers two kinds of evaluations. 
    Input: 
    Capabilities: 
    - Load the ontology file 
    - Run the OOPS! evaluation tool via API, check the content and retrieve results
    - Run the FOOOPs! tool via API, check the meetadata and retrieve results
    Output: Evaluation ontology-based pitfalls and FAIR metrics

    """


    @staticmethod
    def eval_foops_api(uri, output_excel="foops_results.xlsx"):
        try:
            #with open(filepath, "r", encoding="utf-8") as f:
                # owl_content = f.read()

            headers = {
                "Content-Type": "application/json; charset=utf-8"
            }
            data = {
                #"ontologyContent": filepath,
                "ontologyUri" : uri,
                "ontologyFormat": "rdfxml"
            }

            response_foops = requests.post(
                url="https://foops.linkeddata.es/assessOntology",
                headers=headers,
                json=data
            )

            if response_foops.status_code != 200:
                print(f"Erreur HTTP {response_foops.status_code}")
                print(response_foops.text)
                return None

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

            print(f"Résultats FOOPS exportés dans {output_excel}")
            return df

        except Exception as e:
            print(f"Erreur FOOPS: {e}")
            return None



    @staticmethod
    def eval_oops_api(filepath, output_excel="oops_results.xlsx"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                owl_content = f.read()

            xml_body = f"""<?xml version="1.0" encoding="UTF-8"?>
            <OOPSRequest>
                <OntologyUrl></OntologyUrl>
                <OntologyContent><![CDATA[
{owl_content}
                ]]></OntologyContent>
                <Pitfalls></Pitfalls>
                <OutputFormat>RDF/XML</OutputFormat>
            </OOPSRequest>
            """

            headers = {
                "Content-Type": "application/xml",
                "Accept": "application/xml"
            }

            response = requests.post("https://oops.linkeddata.es/rest", data=xml_body.encode("utf-8"), headers=headers)

            if response.status_code != 200:
                print(f"Erreur HTTP {response.status_code}")
                print(response.text)
                return None

            g = rdflib.Graph()
            g.parse(data=response.text, format="xml")

            rows = []
            for s in g.subjects(rdflib.RDF.type, rdflib.URIRef("http://oops.linkeddata.es/def#pitfall")):
                rows.append({
                    "Code": str(g.value(s, rdflib.URIRef("http://oops.linkeddata.es/def#hasCode"))),
                    "Pitfall": str(g.value(s, rdflib.URIRef("http://oops.linkeddata.es/def#hasName"))),
                    "Importance": str(g.value(s, rdflib.URIRef("http://oops.linkeddata.es/def#hasImportanceLevel"))),
                    "Description": str(g.value(s, rdflib.URIRef("http://oops.linkeddata.es/def#hasDescription"))),
                    "Affected Elements": str(g.value(s, rdflib.URIRef("http://oops.linkeddata.es/def#hasNumberAffectedElements")))
                })

            df = pd.DataFrame(rows)
            with pd.ExcelWriter(output_excel) as writer:
                df.to_excel(writer, index=False, sheet_name="OOPS Results")
                pd.DataFrame([{
                    "Tool": "OOPS",
                    "Total Pitfalls": len(df)
                }]).to_excel(writer, index=False, sheet_name="Summary")

            print(f"Résultats OOPS exportés dans {output_excel}")
            return df

        except Exception as e:
            print(f"Erreur OOPS: {e}")
            return None
