# Invoice Processing and Fraud Detection Tool

This app extracts structured data from invoices (PDFs, images, etc.) and checks for signs of fraud. It uses OCR, PDF tools, and machine learning to handle documents and flag anomalies. There's also a web UI built with Streamlit.

## Features

### Document Processing

* OCR for images and image-based PDFs via [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
* Text extraction from native PDFs using [PyMuPDF](https://pymupdf.readthedocs.io/en/latest/) and [pdf2image](https://github.com/Belval/pdf2image)
* Converts other formats using [`markitdown`](https://github.com/microsoft/markitdown) (optional)
* Extracts structured invoice data using AI (via [OpenAI API](https://platform.openai.com/) or [DeepSeek](https://deepseek.com))

### Fraud Detection

* Validates contract dates
* Analyzes line items using ML
* Detects outliers and anomalies using [scikit-learn](https://scikit-learn.org/stable/)
* Displays flagged issues with [matplotlib](https://matplotlib.org/)

## Interesting Techniques

* **Layered Document Parsing**: Uses conditional logic to route between OCR and PDF parsing based on MIME type and file content.
* **Outlier Detection**: Applies Isolation Forests from `scikit-learn` to catch pricing anomalies and suspicious patterns in invoice line items.
* **Interactive Visualization**: Renders real-time charts in [Streamlit](https://docs.streamlit.io/) to help users inspect flagged entries.
* **Modular Pipeline Design**: Document processors and fraud checkers are loosely coupled Python modules — easy to extend and test.

## Notable Libraries and Tools

* [Tesseract](https://github.com/tesseract-ocr/tesseract) for image OCR
* [Poppler](https://poppler.freedesktop.org/) via `pdf2image` for PDF rendering
* [PyMuPDF](https://pymupdf.readthedocs.io/en/latest/) for native PDF text extraction
* [Streamlit](https://streamlit.io/) for the UI
* [DeepSeek](https://deepseek.com) and [OpenAI](https://platform.openai.com) APIs for AI-enhanced field detection
* [scikit-learn](https://scikit-learn.org/stable/) for anomaly detection
* [`markitdown`](https://github.com/Red9/markitdown) for flexible document conversion

## Project Structure

```
invoice_processing_app/
├── app.py
├── requirements.txt
├── processors/
│   ├── __init__.py
│   ├── document_processor.py
│   └── invoice_analyzer.py
├── ui/
│   ├── __init__.py
│   ├── document_ui.py
│   ├── fraud_detector_ui.py
│   └── settings_ui.py
├── assets/
│   └── logo.png
├── data/
│   └── samples/
└── tests/
    └── test_processor.py
```

* `processors/`: Core logic for handling document input and fraud analysis.
* `ui/`: Streamlit component logic, separated into modules.
* `assets/`: Static files such as logos or icons.
* `data/samples/`: Sample documents for testing or demonstration.
* `tests/`: Basic unit tests for core modules.

## How to Run

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/invoice-processing-app.git
   cd invoice-processing-app
   ```

2. Create a virtual environment:

   * On Windows:

     ```bash
     python -m venv ub
     ub\Scripts\activate.bat
     ```
   * On macOS/Linux:

     ```bash
     python3 -m venv ub
     source ub/bin/activate
     ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   pip install 'markitdown[all]'
   ```

4. Install system tools:

   * Tesseract OCR:

     * Windows: Download from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) and add to PATH
     * macOS: `brew install tesseract`
     * Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
   * Poppler:

     * Windows: Download from [poppler-windows](http://blog.alivate.com.au/poppler-windows/) and add to PATH
     * macOS: `brew install poppler`
     * Ubuntu/Debian: `sudo apt-get install poppler-utils`

5. Start the app:

   ```bash
   streamlit run app.py
   ```

   This will open the UI at `http://localhost:8501`.

## License

This project is licensed under the [MIT License](./LICENSE).

## Acknowledgements

* [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for OCR.
* [Streamlit](https://streamlit.io/) for the frontend.
* [DeepSeek](https://deepseek.com) for AI-powered invoice field detection.
* [Markitdown](https://github.com/microsoft/markitdown) for converting any type of files into text data.

