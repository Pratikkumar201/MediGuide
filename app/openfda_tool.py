# This tool implements the MCP (Model Context Protocol) pattern from Day 2 of the course

import urllib.request
import urllib.parse
import json
from urllib.error import HTTPError, URLError


def get_drug_info(drug_name: str) -> str:
    """Retrieves warnings, interactions, and dosage information for a drug from OpenFDA.

    Args:
        drug_name: The brand name of the drug.

    Returns:
        A formatted string summary of drug information, or "Drug not found in FDA database."
    """
    # URL encode the brand name
    encoded_name = urllib.parse.quote(drug_name)
    url = f"https://api.fda.gov/drug/label.json?search=openfda.brand_name:{encoded_name}&limit=1"
    
    try:
        req = urllib.request.Request(
            url, 
            headers={"User-Agent": "MediGuide Agent/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, json.JSONDecodeError):
        return "Drug not found in FDA database."

    results = data.get("results")
    if not results or not isinstance(results, list) or len(results) == 0:
        return "Drug not found in FDA database."

    result = results[0]
    
    # Extract warnings (max 2)
    warnings_list = result.get("warnings", [])
    if not isinstance(warnings_list, list):
        warnings_list = [warnings_list]
    warnings = [w[:200] + "..." if len(w) > 200 else w for w in warnings_list[:2]]
    warnings_str = "\n".join(f"- {w}" for w in warnings) if warnings else "None listed"

    # Extract drug interactions (max 2)
    interactions_list = result.get("drug_interactions", [])
    if not isinstance(interactions_list, list):
        interactions_list = [interactions_list]
    interactions = [i[:200] + "..." if len(i) > 200 else i for i in interactions_list[:2]]
    interactions_str = "\n".join(f"- {i}" for i in interactions) if interactions else "None listed"

    # Extract dosage and administration (truncated to 300 chars)
    dosage_list = result.get("dosage_and_administration", [])
    if not isinstance(dosage_list, list):
        dosage_list = [dosage_list]
    dosage_str = dosage_list[0] if dosage_list else "None listed"
    if len(dosage_str) > 300:
        dosage_str = dosage_str[:300] + "..."

    summary = (
        f"Drug Information for {drug_name.capitalize()}:\n"
        f"Warnings:\n{warnings_str}\n"
        f"Drug Interactions:\n{interactions_str}\n"
        f"Dosage & Administration:\n{dosage_str}"
    )
    return summary


def check_drug_interaction(drug1: str, drug2: str) -> str:
    """Checks and returns a combined safety summary for two drugs to highlight interactions.

    Args:
        drug1: The brand name of the first drug.
        drug2: The brand name of the second drug.

    Returns:
        A combined summary of warnings and interaction potentials for both drugs.
    """
    info1 = get_drug_info(drug1)
    info2 = get_drug_info(drug2)
    
    summary = (
        f"--- Interaction Check: {drug1.capitalize()} and {drug2.capitalize()} ---\n\n"
        f"{info1}\n\n"
        f"{info2}\n\n"
        f"Disclaimer: Always consult with a healthcare professional before combining medications."
    )
    return summary
