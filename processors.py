import pandas as pd
from typing import List
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine


def anonymize_text(
    text: str,
    analyzer: AnalyzerEngine,
    anonymizer: AnonymizerEngine,
    operators: dict,
    language: str = "en",
) -> str:
    if not isinstance(text, str) or text.strip() == "":
        return text

    results = analyzer.analyze(
        text=text,
        entities=list(operators.keys()),
        language=language,
    )

    if not results:
        return text

    anonymized_result = anonymizer.anonymize(
        text=text,
        analyzer_results=results,
        operators=operators,
    )

    return anonymized_result.text


def anonymize_dataframe(
    df: pd.DataFrame,
    analyzer: AnalyzerEngine,
    anonymizer: AnonymizerEngine,
    operators: dict,
    columns: List[str],
) -> pd.DataFrame:
    df = df.copy()

    for col in columns:
        if col not in df.columns:
            continue

        # Only anonymize likely-text columns
        if df[col].dtype == "object":
            df[col] = df[col].astype(str).apply(
                lambda x: anonymize_text(
                    x,
                    analyzer=analyzer,
                    anonymizer=anonymizer,
                    operators=operators,
                )
            )
        else:
            # If you want to be extra paranoid, cast and run anyway.
            pass

    return df
