from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

def create_presidio_engines():
    """
    Initialize Presidio Analyzer + Anonymizer.
    """

    nlp_configuration = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "en", "model_name": "en_core_web_lg"}],
    }

    provider = NlpEngineProvider(nlp_configuration=nlp_configuration)
    nlp_engine = provider.create_engine()

    analyzer = AnalyzerEngine(
        nlp_engine=nlp_engine,
        supported_languages=["en"],
    )

    anonymizer = AnonymizerEngine()

    gmail_pattern = Pattern(
        name="gmail_pattern",
        regex=r"[A-Za-z0-9._%+-]+@gmail\.com",
        score=0.9,
    )
    gmail_recognizer = PatternRecognizer(
        supported_entity="EMAIL_ADDRESS",
        patterns=[gmail_pattern],
    )
    analyzer.registry.add_recognizer(gmail_recognizer)

    return analyzer, anonymizer


DEFAULT_OPERATORS = {
    # Fallback for anything not explicitly set
    "DEFAULT": OperatorConfig("replace", {"new_value": "<PII>"}),

    "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<EMAIL>"}),
    "PERSON":        OperatorConfig("replace", {"new_value": "<NAME>"}),
    "LOCATION":      OperatorConfig("replace", {"new_value": "<LOCATION>"}),
    "PHONE_NUMBER":  OperatorConfig("replace", {"new_value": "<PHONE>"}),
    "IP_ADDRESS":    OperatorConfig("replace", {"new_value": "<IP>"}),
    "CREDIT_CARD":   OperatorConfig("replace", {"new_value": "<CC>"}),
    "IBAN_CODE":     OperatorConfig("replace", {"new_value": "<IBAN>"}),
    "US_SSN":        OperatorConfig("replace", {"new_value": "<SSN>"}),
}