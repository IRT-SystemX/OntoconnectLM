import sys
sys.path.insert(0, '/ontoconnectlm/')

import time
import json
import yaml
import ast
import os

from rdflib import Graph
import networkx as nx
from pyvis.network import Network
from stvis import pv_static
import tempfile
import io
import sys
import contextlib
from PIL import Image
from io import BytesIO
from io import StringIO

import streamlit as st
from langchain_ollama import OllamaLLM

from ontoconnectlm.classes_generator import ClassesGenerator
from ontoconnectlm.triplet_extractor import TripletExtractor
from ontoconnectlm.owl_generator import OwlGenerator
from ontoconnectlm.ontology_enrichment.ontology_change_tracker import OntologyChangeTracker

from ontoconnectlm.ontology_enrichment.dbpedia_entity_linking import DBpedia_linking
from ontoconnectlm.ontology_enrichment.wikidata_entity_linking import Wikidata_linking
from ontoconnectlm.ontology_enrichment.onto_updater import Onto_Updater
from ontoconnectlm.onto_eval import Onto_Evaluator


# ######################################
#               FUNCTIONS
# ######################################

def _init_server_config(name: str) -> None:
    with st.form(name):
        st.write("Select LLM server configuration")
        llm_server = st.selectbox(
            "LLM server",
            ["127.0.0.1:11434"],
            index=None,
            placeholder="Select a saved LLM server IP:port or enter a new one",
            accept_new_options=True,
        )

        llm_model_name = st.selectbox(
            "LLM model name",
            ["mistral-small3.1:24b", "gemma3:4b"],
            index=None,
            placeholder="Select a saved LLM model name or enter a new one",
            accept_new_options=True,
        )

        submit_button = st.form_submit_button("Apply", icon=":material/how_to_reg:")
        if submit_button:
            st.write(f"Server selected: {llm_server}")
            st.write(f"Model selected: {llm_model_name}")
            st.session_state["llm"] = OllamaLLM(base_url = llm_server , model=llm_model_name)
            st.session_state["llm_flag"] = True
        if st.session_state["llm_flag"]:
            st.success("Config success!", icon=":material/task_alt:")
        else:
            st.warning("Need configuration", icon=":material/warning:")

def _get_file_contents(file_path: str) -> list[str]:
    with open(file_path, "r") as f:
        data = f.read()
    return data

def _del_file_if_exist(file_path: str) -> None:
    if os.path.exists(file_path):
        os.remove(file_path)

def _get_show_modifiable(title: str, data: dict|list):
        st.markdown(f"#### {title}")
        # Convert data to a JSON string
        default_json_data = json.dumps(data, indent=2, ensure_ascii=False)

        # Show in text area
        modified_json_data = st.text_area("Edit data below:", value=default_json_data, height=200)

        # Try to parse back into a dict or list
        try:
            modified_data = json.loads(modified_json_data)
            return modified_data
        except json.JSONDecodeError as e:
            st.error(f"Invalid format: {e}")

caching_variables_states_dict = {
    "llm" : None,
    "llm_flag" : None,
    "context_description" : None,
    "generator" : None,
    "competency_questions_list" : [],
    "text_data_input_list" : [],
    "og_entiy_linked_type_list" : [],
    "og_entiy_linked_class_list" : [],
    "og_entity_dict": {},
    "triple_file_list" : None,
    "properties_file_list" : None,
    "required_classes_list" : [],
    "required_properties" : {},
    "required_properties_list" : {},
    "onto_upload_file_name" : str,
    "syntaxic_analysis" : None,
    "fair_analysis" : None,
    "entity_types" : None,
    "triples_list_demo" : [],
    "triples_list_demo_2" : [],
    "text_triplet" : [],
    "download_gen_owl" : None,
    "ER_competency_questions" : [],
    "ER_texts" : [],
    "ER_context_description" : [],
    "ER_classes_generator" : [],
    "CONF_FILE" : None,
    "SUCCESS_FLAG" : None,
    "user_input_cnt" : 0,

    }

for cached_var in caching_variables_states_dict:
    if cached_var not in st.session_state:
        st.session_state[cached_var] = caching_variables_states_dict[cached_var]

with st.sidebar:
    st.set_page_config(page_title="SMD Ontology", layout="wide", page_icon="/ontoconnectlm/images/systemxIcon.png")
    st.image("/ontoconnectlm/images/systemxLogo.png")
    # Configuration
    st.markdown("# Configuration")
    _init_server_config("Configuration Ontology")

if st.session_state["SUCCESS_FLAG"] != True:
    yaml_file_path = r"/ontoconnectlm/streamlit/config/config.yaml"
    with open(yaml_file_path, 'r') as file:
        st.session_state["CONF_FILE"] = yaml.safe_load(file)
    st.session_state["SUCCESS_FLAG"] = True

# Sidebar
tab_options = [
    "Step 1: Entity Recognition",
    "Step 2: Triples Extractor",
    "Step 3: Owl Generator",
    "Step 4: Classes Enricher",
    "Step 5: Ontology Evaluator",
    ]
cap_directions = [
    "▼",
    "▼",
    "▼",
    "▼",
    ""
]
selected_tab = st.sidebar.radio("Select a step", tab_options, captions=cap_directions)

# #################################### Step 1: Entity Recognition ####################################
if selected_tab == "Step 1: Entity Recognition":
    st.markdown("# Step 1: Entity Recognition")
    # ER_context_description
    if st.session_state["SUCCESS_FLAG"]:
        st.markdown("#### Context Description")
        st.session_state["ER_context_description"] = st.text_area(f"User Context Description", value=st.session_state["CONF_FILE"]["context_description"], height=2*68)

        # ER_competency_questions
        st.markdown("#### Competency Questions")
        with st.expander("Competency Questions"):
            cq_text = ""
            if st.session_state["CONF_FILE"]["competency_questions"]:
                for cq in st.session_state["CONF_FILE"]["competency_questions"]:
                    cq_text += f"{cq}\n"
                st.session_state["ER_competency_questions"] = st.text_area(f"User Competency Questions", value=cq_text, height=2*68).split("\n")
            else:
                st.session_state["ER_competency_questions"] = st.text_area(f"User Competency Questions", value="", height=2*68).split("\n")

        # ER_texts
        with st.form("ER_texts_form"):
            st.markdown("#### Texts")
            col1, col2 = st.columns(2)
            user_input_txt = ""
            if col1.form_submit_button("Add User Text", icon=":material/add_circle:"):
                st.session_state["user_input_cnt"] += 1
                # st.rerun()
            if col2.form_submit_button("Del User Text", icon=":material/delete:"):
                st.session_state["user_input_cnt"] -= 1
                # st.rerun()

            _list_er_texts = []
            for index in range(0 , st.session_state["user_input_cnt"]):
                _list_er_texts.append(st.text_area(f"User Text #{index + 1}", height=2*68, key=10900+ 36*index))

            class_number = st.number_input("Maximim number of concepts", step=1)

            if st.form_submit_button("Validate", icon=":material/check:"):
                st.session_state["ER_texts"] = _list_er_texts.copy()

        if st.button("Generate", icon=":material/refresh:"):

            with st.spinner("Wait for it...", show_time=False):
                if st.session_state["CONF_FILE"]["competency_questions"]:
                    generator = ClassesGenerator(
                        llm = st.session_state["llm"],
                        context_description=st.session_state["CONF_FILE"]["context_description"],
                        competency_questions=st.session_state["ER_competency_questions"]
                        )
                elif len(st.session_state["ER_competency_questions"]) and st.session_state["ER_competency_questions"][0] == "":
                    generator = ClassesGenerator(
                        llm = st.session_state["llm"],
                        context_description=st.session_state["CONF_FILE"]["context_description"],
                        competency_questions = []
                        )
                st.session_state["ER_classes_generator"] = generator.run(st.session_state["ER_texts"], nb_classes=class_number)

                st.code(st.session_state["ER_classes_generator"], wrap_lines=True, height=None)

# #################################### Step 2: Triples Extractor ####################################
elif selected_tab == "Step 2: Triples Extractor":
    st.markdown("# Step 2: Triples Extractor")
    with st.form("te"):
        col1, col2, col3 = st.columns(3)
        st.markdown(":orange-badge[⚠️ Mandatory step]")
        context_description = st.session_state["ER_context_description"]
        # TODO entity_types = st.session_state["TE_entity_types"]
        entity_types = _get_show_modifiable("entity_types", st.session_state["CONF_FILE"]["entity_types"])
        entity_descriptions = _get_show_modifiable("entity_descriptions", st.session_state["CONF_FILE"]["entity_descriptions"])
        relation_types = _get_show_modifiable("relation_types", st.session_state["CONF_FILE"]["relation_types"])
        relation_descriptions = _get_show_modifiable("relation_descriptions", st.session_state["CONF_FILE"]["relation_descriptions"])
        texts = st.session_state["ER_texts"]

        if st.form_submit_button("Extract Triples", icon=":material/warning:"):
            with st.spinner("Wait for it...", show_time=False):
                extractor = TripletExtractor(
                    llm = st.session_state["llm"],
                    context_description=context_description,
                    entity_types=entity_types,
                    entity_descriptions = entity_descriptions,
                    relation_types=relation_types,
                    relation_descriptions = relation_descriptions
                )
                st.session_state["triples_list_demo"] = extractor.run(texts)
                st.session_state["triples_list_demo_2"] = []
                for i in st.session_state["triples_list_demo"]:
                    for j in i:
                        st.session_state["triples_list_demo_2"].append(j)
                st.code(st.session_state["triples_list_demo_2"], wrap_lines=True, height=None)

# #################################### Step 3: Owl Generator ####################################
elif selected_tab == "Step 3: Owl Generator":
    st.markdown("# Step 3: Owl Generator")
    with st.form("owg"):
        triples = st.session_state["triples_list_demo_2"]
        st.markdown(":orange-badge[⚠️ Mandatory step]")
        if st.form_submit_button("Generate OWL", icon=":material/warning:"):
            if st.session_state["CONF_FILE"]["entity_linker"]:
                entity_linker = st.session_state["CONF_FILE"]["entity_linker"]
            else:
                entity_linker = {}
            if st.session_state["CONF_FILE"]["additional_classes"]:
                additional_classes = st.session_state["CONF_FILE"]["additional_classes"]
            else:
                additional_classes = []
            if st.session_state["CONF_FILE"]["additional_properties"]:
                additional_properties = st.session_state["CONF_FILE"]["additional_properties"]
            else:
                additional_properties = []

            config = {
                "entity_linker" : entity_linker,
                "additional_classes" : additional_classes,
                "additional_properties" : additional_properties
                }
            owl_generator = OwlGenerator(
                triples = triples,
                config=config,
                onto_uri = "http://smd#"
                )

            result_ontology = owl_generator.create_ontology()
            st.session_state["download_gen_owl"] = result_ontology
            with st.status("Show owl generated file..."):
                st.code(st.session_state["download_gen_owl"], language="owl")

            # Draw graph
            g = Graph()
            try:
                g.parse(data=st.session_state["download_gen_owl"], format='xml')
                st.success("OWL content parsed successfully!")
            except Exception as e:
                st.error(f"Failed to parse OWL content: {e}")
                st.stop()

            # Build a NetworkX graph from the RDF triples
            G = nx.DiGraph()
            for subj, pred, obj in g:
                G.add_edge(str(subj), str(obj), label=str(pred))

            # Create a Pyvis network from the NetworkX graph
            net = Network(height="600px", width="100%", directed=True)
            net.from_nx(G)

            # Optional: Add edge labels
            for edge in G.edges(data=True):
                src, dst, data = edge
                net.add_edge(src, dst, title=data.get("label", ""))

            # Save and display the graph in Streamlit
            with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp_file:
                net.save_graph(tmp_file.name)
                tmp_file.close()
                st.components.v1.html(open(tmp_file.name, 'r', encoding='utf-8').read(), height=600, scrolling=True)
                os.unlink(tmp_file.name)

    if st.button("Prepare owl file", icon=":material/refresh:", key="abc"):
        st.download_button(
            label="Download owl file",
            data=st.session_state["download_gen_owl"],
            file_name="result_ontology.owl",
            on_click="ignore",
            type="primary",
            icon=":material/download:",
        )

# #################################### Step 4: Classes Enricher ####################################
elif selected_tab == "Step 4: Classes Enricher":
    st.markdown("# Step 4: Classes Enricher")
    with st.form("oce"):
        if st.form_submit_button("Run Enricher", icon=":material/play_circle:"):
            with st.spinner("Wait for it...", show_time=False):
                classEnricher_directory = r"/ontoconnectlm/streamlit/config/classe_enricher"
                pop_onto = r"/tmp/owlGen_generated.owl"
                enrich_onto = r"/ontoconnectlm/streamlit/config/classe_enricher/enrich_generated.owl"
                if not os.path.exists(classEnricher_directory):
                    os.makedirs(classEnricher_directory)

                with open(pop_onto, "w") as f:
                    f.write(st.session_state["download_gen_owl"])

                # ###################################################################
                st.markdown("#### -> DBpedia metadata collection")
                DB_enricher = DBpedia_linking()
                DB_enricher_results = DB_enricher.dbpedia_enrichment(ontology_content = st.session_state["download_gen_owl"])

                st.markdown("#### -> Wikidata metadata collection")
                Wiki_enricher = Wikidata_linking()
                Wiki_enricher_results = Wiki_enricher.wikidata_enrichment(ontology_content=st.session_state["download_gen_owl"])

                st.markdown("#### -> Enriched OWL ontology generation")
                updater = Onto_Updater(
                    dbpedia_results=DB_enricher_results,
                    wikidata_results=Wiki_enricher_results,
                    ontology_content=st.session_state["download_gen_owl"]
                )
                result_ontology_enricher = updater.update_ontology(enrichment_mode="classes")

                # Write enrich_onto to enrich_onto file path
                with open(enrich_onto, "w") as f:
                    f.write(result_ontology_enricher)

                with st.status("Show owl generate file ..."):
                    # st.code(onto_linker.run(), language="text")
                    st.code(result_ontology_enricher, language="owl")

                g = Graph()
                try:
                    g.parse(data=result_ontology_enricher, format='xml')
                    st.success("OWL content parsed successfully!")
                except Exception as e:
                    st.error(f"Failed to parse OWL content: {e}")
                    st.stop()

                # Build a NetworkX graph from the RDF triples
                G = nx.DiGraph()
                for subj, pred, obj in g:
                    G.add_edge(str(subj), str(obj), label=str(pred))

                # Create a Pyvis network from the NetworkX graph
                net = Network(height="600px", width="100%", directed=True)
                net.from_nx(G)

                # Optional: Add edge labels
                for edge in G.edges(data=True):
                    src, dst, data = edge
                    net.add_edge(src, dst, title=data.get("label", ""))

                # Save and display the graph in Streamlit
                with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp_file:
                    net.save_graph(tmp_file.name)
                    tmp_file.close()
                    st.components.v1.html(open(tmp_file.name, 'r', encoding='utf-8').read(), height=600, scrolling=True)
                    os.unlink(tmp_file.name)

                # Change tracker
                tracker = OntologyChangeTracker(pop_onto, enrich_onto)
                triples_diff, entities_diff = tracker.report_changes()
                removed_list = []
                added_list = []
                for key, value in entities_diff.items():
                    if "Added" in key.title():
                        added_list.append(f":green[{key.title()}: {len(value)}]")
                    elif "Removed" in key.title():
                        removed_list.append(f":red[{key.title()}: {len(value)}]")
                st.markdown("#### ENTITY CHANGES")
                for i in added_list:
                    st.markdown(f":green[{i}]")
                for i in removed_list:
                    st.markdown(f":red[{i}]")

                st.markdown("#### TRIPLE CHANGES")
                st.markdown(f":green[Added Triples: {len(triples_diff['added_triples'])}]")
                st.markdown(f":red[Removed Triples: {len(triples_diff['removed_triples'])}]")

    if st.button("Generate results files", icon=":material/refresh:"):
        enrich_onto = r"/ontoconnectlm/streamlit/config/classe_enricher/enrich_generated.owl"
        dbpedia_output = r"/ontoconnectlm/streamlit/config/classe_enricher/dbpedia_EL_results.xlsx"
        wikidata_output = r"/ontoconnectlm/streamlit/config/classe_enricher/wikidata_EL_results.xlsx"
        col1, col2, col3 = st.columns(3)
        with open(dbpedia_output, 'rb') as dbpedia_output_file:
            dbpedia_output_file_bytes = BytesIO(dbpedia_output_file.read())

        with open(wikidata_output, 'rb') as wikidata_output_file:
            wikidata_output_file_bytes = BytesIO(wikidata_output_file.read())

        col1.download_button(
            label="Download enrich_generated owl file",
            data=_get_file_contents(enrich_onto),
            file_name="enrich_generated.owl",
            on_click="ignore",
            type="primary",
            icon=":material/download:",
        )
        col2.download_button(
            label="Download dbpedia_EL_results file",
            data=dbpedia_output_file_bytes,
            file_name="dbpedia_EL_results.xlsx",
            on_click="ignore",
            type="primary",
            icon=":material/download:",
        )
        col3.download_button(
            label="Download wikidata_EL_results file",
            data=wikidata_output_file_bytes,
            file_name="wikidata_EL_results.xlsx",
            on_click="ignore",
            type="primary",
            icon=":material/download:",
        )

# #################################### Step5: Ontology Evaluator ####################################
elif selected_tab == "Step 5: Ontology Evaluator":
    st.markdown("# Step 5: Ontology Evaluator")
    with st.form("ooe"):
        enrich_onto = r"/ontoconnectlm/streamlit/config/classe_enricher/enrich_generated.owl"

        with open(enrich_onto, "r") as read_file:
            ontology_content = read_file.read()

        evaluator = Onto_Evaluator(
            ontology_content=ontology_content,
            ontology_uri="http://smd#"
        )
        col1, col2 = st.columns(2)

        if st.form_submit_button("Run Eval", icon=":material/play_circle:"):
            st.markdown("### Scaning Ontology Detecting Pitfalls")
            st.dataframe(evaluator.eval_oops())

            st.markdown("### Optional: FAIR quality for open data")
            st.dataframe(evaluator.eval_fair())
