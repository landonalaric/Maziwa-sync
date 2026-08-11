import json
import os
import joblib

from dotenv import load_dotenv
from groq import Groq


class CattleAIService:

    def __init__(self):

        # Load environment variables
        load_dotenv()

        # Get current service directory
        base_dir = os.path.dirname(os.path.abspath(__file__))

        # -----------------------------
        # Load ML model
        # -----------------------------

        model_path = os.path.join(
            base_dir,
            "cattle_disease_model.pkl"
        )

        features_path = os.path.join(
            base_dir,
            "model_features.pkl"
        )

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model file not found: {model_path}"
            )

        if not os.path.exists(features_path):
            raise FileNotFoundError(
                f"Model features file not found: {features_path}"
            )

        self.model = joblib.load(model_path)

        self.model_features = joblib.load(features_path)

        # -----------------------------
        # Valid symptoms
        # -----------------------------

        self.valid_symptoms = [
            feature
            for feature in self.model_features
            if feature not in ["Age", "Temperature"]
            and not feature.startswith("Animal")
        ]

        # -----------------------------
        # Groq
        # -----------------------------

        api_key = os.environ.get("GROQ_API_KEY")

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is not configured on the server"
            )

        self.groq_client = Groq(
            api_key=api_key
        )

    # ----------------------------------
    # Extract symptoms
    # ----------------------------------

    def extract_symptoms_with_groq(self, farmer_text):

        system_prompt = f"""
You are a veterinary assistant.

Analyse the farmer's description and extract symptoms
that match exactly the following list:

{self.valid_symptoms}

Return ONLY valid symptoms.

Respond as JSON:

{{
    "symptoms": ["symptom_name"]
}}
"""

        try:

            completion = self.groq_client.chat.completions.create(

                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": f'Farmer text: "{farmer_text}"'
                    }
                ],

                model="llama-3.1-8b-instant",

                temperature=0,

                response_format={
                    "type": "json_object"
                }
            )

            response_text = (
                completion
                .choices[0]
                .message
                .content
                .strip()
            )

            result_json = json.loads(response_text)

            return result_json.get("symptoms", [])

        except Exception as e:

            print(f"Groq Extraction Error: {e}")

            return []

    # ----------------------------------
    # Treatment recommendation
    # ----------------------------------

    def get_treatment_recommendation(
        self,
        disease,
        animal_type
    ):

        system_prompt = """
You are an expert livestock veterinarian.

Provide clear, concise and professional treatment
recommendations under 120 words.

Use short bullet points.

Always include a veterinary disclaimer.
"""

        try:

            completion = self.groq_client.chat.completions.create(

                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Treatment recommendation for a "
                            f"{animal_type} with {disease}"
                        )
                    }
                ],

                model="llama-3.1-8b-instant",

                temperature=0.3
            )

            return (
                completion
                .choices[0]
                .message
                .content
                .strip()
            )

        except Exception as e:

            print(f"Groq Treatment Error: {e}")

            return "Treatment recommendation temporarily unavailable."

    # ----------------------------------
    # Prediction
    # ----------------------------------

    def predict(
        self,
        animal_type,
        age,
        temp,
        description
    ):

        # Extract symptoms
        extracted_symptoms = (
            self.extract_symptoms_with_groq(
                description
            )
        )

        # Create empty feature dictionary
        input_data = {
            feature: 0
            for feature in self.model_features
        }

        # Numeric values
        input_data["Age"] = float(age)
        input_data["Temperature"] = float(temp)

        # Animal
        animal_key = (
            f"Animal_{str(animal_type).strip().lower()}"
        )

        if animal_key in input_data:
            input_data[animal_key] = 1

        # Symptoms
        for symptom in extracted_symptoms:

            if symptom in input_data:
                input_data[symptom] = 1

        # Maintain exact training feature order
        final_input_vector = [
            input_data[feature]
            for feature in self.model_features
        ]

        print("MODEL INPUT:")
        print(final_input_vector)

        # Prediction
        prediction = self.model.predict(
            [final_input_vector]
        )

        predicted_disease = prediction[0]

        # Treatment
        treatment_plan = (
            self.get_treatment_recommendation(
                predicted_disease,
                animal_type
            )
        )

        return {
            "status": "success",
            "extracted_symptoms_by_ai": extracted_symptoms,
            "predicted_disease": predicted_disease,
            "treatment_recommendation": treatment_plan
        }