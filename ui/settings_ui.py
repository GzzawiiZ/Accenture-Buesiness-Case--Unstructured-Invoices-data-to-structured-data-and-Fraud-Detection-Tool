# ui/settings_ui.py
import streamlit as st

class SettingsUI:
    """UI class for application settings"""
    
    def show(self):
        """Display the settings interface"""
        st.title("⚙️ Settings")
        
        st.subheader("API Keys")
        api_key = st.text_input(
            "DeepSeek API Key",
            value=st.session_state.deepseek_api_key,
            type="password",
            help="Enter your DeepSeek API key to use the AI extraction feature"
        )
        
        if st.button("Save Settings"):
            st.session_state.deepseek_api_key = api_key
            st.success("Settings saved successfully!")
        
        st.subheader("About")
        st.markdown("""
        This application provides document processing and fraud detection capabilities:
        
        1. **Document Processor**: Extracts text and structured data from various document formats:
           - OCR for images and image-based PDFs
           - Text extraction for text-based PDFs
           - MarkItDown conversion for other document formats
        
        2. **Invoice Fraud Detector**: Analyzes invoice data for anomalies and potential fraud using:
           - Contract date validation
           - Unusual pricing detection
           - Machine learning-based anomaly detection
        
        Required dependencies:
        - pytesseract (for OCR)
        - markitdown (for document conversion)
        - pdf2image and PyMuPDF (for PDF processing)
        - scikit-learn (for anomaly detection)
        """)