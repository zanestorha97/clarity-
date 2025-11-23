# PII Sanitizer (Microsoft Presidio + Streamlit)

A tiny web app that uses [Microsoft Presidio](https://github.com/microsoft/presidio)
to detect and anonymize PII in CSV files (e.g. Slack exports) and return a cleaned CSV.

## Features

- Upload CSV
- Choose which columns to scan
- Detects emails, names, locations, etc. (with extra love for `@gmail.com`)
- Download anonymized CSV

## Docker Setup

```bash
docker build -t pii-sanitizer .
docker run -p 8501:8501 pii-sanitizer
```

## Testing

Follow the steps to recreate the image sample.png in img folder
   - Go to browser - http://localhost:8501
   - Upload HRIS csv from data
   - Upload Zip Clarity Slack Export Zip from data
   - Get the combined data csv
   - Press the Anonmyize Slack Data to download anonmyize json file