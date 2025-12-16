TREATMENT_OPTIONS = {
    "common cold": {
        "accepted": [
            "rest",
            "fluids",
            "hydration",
            "steam inhalation",
            "saline nasal spray",
            "pain reliever",
            "paracetamol",
            "ibuprofen",
            "warm liquids",
        ],
        "rejected": [
            "antibiotics",
            "antifungals",
            "steroids",
            "antiviral medications",
        ]
    },

    "fever": {
        "accepted": [
            "paracetamol",
            "acetaminophen",
            "ibuprofen",
            "rest",
            "fluids",
            "cool compress",
        ],
        "rejected": [
            "antibiotics",
            "antimalarials",
            "antivirals",
        ]
    },

    "dengue": {
        "accepted": [
            "paracetamol",
            "acetaminophen",
            "hydration",
            "oral rehydration salts",
            "rest",
            "monitor platelet count",
        ],
        "rejected": [
            "ibuprofen",
            "aspirin",
            "antibiotics",
            "steroids",
        ]
    },

    "migraine": {
        "accepted": [
            "ibuprofen",
            "naproxen",
            "acetaminophen",
            "rest in a dark room",
            "hydration",
            "cold compress",
        ],
        "rejected": [
            "antibiotics",
            "antacids",
        ]
    },

    "bacterial pneumonia": {
        "accepted": [
            "antibiotics",
            "rest",
            "fluids",
            "fever reducers",
        ],
        "rejected": [
            "antivirals",
            "homeopathy",
            "aspirin for children",
        ]
    },

    "gastric acidity": {
        "accepted": [
            "antacids",
            "proton pump inhibitors",
            "H2 blockers",
            "avoiding spicy foods",
        ],
        "rejected": [
            "antibiotics",
            "pain relievers like ibuprofen",
        ]
    }
}

CONDITION_SYMPTOMS = {
    "common cold": ["runny nose", "sore throat", "mild cough", "congestion", "fatigue", "sneezing"],
    "fever": ["high temperature", "chills", "sweating", "headache", "body aches", "weakness"],
    "dengue": ["high fever", "severe headache", "pain behind eyes", "joint pain", "muscle pain", "rash"],
    "migraine": ["severe headache", "nausea", "sensitivity to light", "sensitivity to sound", "visual disturbances"],
    "bacterial pneumonia": ["cough with phlegm", "fever", "chest pain", "difficulty breathing", "fatigue", "chills"],
    "gastric acidity": ["heartburn", "chest discomfort", "bitter taste", "bloating", "nausea", "burping"]
}