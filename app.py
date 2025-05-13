# app.py
import streamlit as st
from processors.document_processor import DocumentProcessor
from processors.invoice_analyzer import InvoiceAnalyzer
from ui.document_ui import DocumentProcessorUI
from ui.fraud_detector_ui import FraudDetectorUI
from ui.settings_ui import SettingsUI
import uuid
import json

class InvoiceProcessingApp:
    def __init__(self):
        self._initialize_session_state()
        self.document_processor = DocumentProcessor()
        self.invoice_analyzer = InvoiceAnalyzer()
        
        # UI Components
        self.document_ui = DocumentProcessorUI(self.document_processor)
        self.fraud_detector_ui = FraudDetectorUI(self.invoice_analyzer)
        self.settings_ui = SettingsUI()
    
    def _initialize_session_state(self):
        """Initialize Streamlit session state variables"""
        if 'deepseek_api_key' not in st.session_state:
            st.session_state.deepseek_api_key = ""
        if 'processed_document' not in st.session_state:
            st.session_state.processed_document = None
        if 'analysis_result' not in st.session_state:
            st.session_state.analysis_result = None
    
    def run(self):
        """Main application entry point"""
        st.set_page_config(page_title="Document Processing Tool", layout="wide")
        
        # Sidebar navigation
        st.sidebar.title("Navigation")
        app_mode = st.sidebar.radio("Choose Application", 
                                    ["Document Processor", 
                                     "Invoice Fraud Detector",
                                     "Settings"])
        
        # Display the selected UI component
        if app_mode == "Document Processor":
            self.document_ui.show()
        elif app_mode == "Invoice Fraud Detector":
            self.fraud_detector_ui.show()
        elif app_mode == "Settings":
            self.settings_ui.show()

if __name__ == "__main__":
    app = InvoiceProcessingApp()
    app.run()