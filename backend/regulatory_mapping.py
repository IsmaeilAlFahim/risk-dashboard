import csv
import os

def load_regulatory_mapping(csv_path):
    """
    Loads a CSV file containing fine information for each violation type.
    Expects columns like:
      Code,Category,Violation Type,First Offense,Second Offense,Third Offense,Additional Action
    Returns a dict keyed by Violation Type, for example:
      {
        "Failure to report contagious diseases among workers": {
          "category": "Personal Hygiene & Health Violations",
          "offenses": ["500", "1000", "2000"],
          "additional_action": ""
        },
        "Selling or providing unfit or spoiled food": {
          "category": "Unsafe Food Violations",
          "offenses": ["Confiscation", "Confiscation", "Confiscation"],
          "additional_action": ""
        },
        ...
      }
    """
    mapping = {}

    # Preserve your existing file existence check and warning
    if not os.path.exists(csv_path):
        print(f"[WARNING] CSV file not found at: {csv_path}")
        return mapping

    # Preserve your full DictReader logic
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # We assume these columns exist:
            #   "Category", "Violation Type", "First Offense", "Second Offense", "Third Offense", "Additional Action"
            v_type = row["Violation Type"].strip()
            category = row["Category"].strip()
            # Store each offense exactly as a string
            first_offense  = row["First Offense"].strip()
            second_offense = row["Second Offense"].strip()
            third_offense  = row["Third Offense"].strip()
            additional_action = row["Additional Action"].strip() if "Additional Action" in row else ""

            mapping[v_type] = {
                "category": category,
                "offenses": [first_offense, second_offense, third_offense],
                "additional_action": additional_action
            }

    return mapping

# Adjust the CSV path if needed
csv_file_path = os.path.join(os.path.dirname(__file__), "Violations_Dataset.csv")

# This global variable can be imported elsewhere:
REGULATORY_MAPPING = load_regulatory_mapping(csv_file_path)
