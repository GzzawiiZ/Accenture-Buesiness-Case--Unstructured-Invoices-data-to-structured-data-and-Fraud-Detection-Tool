# ui/document_ui.py
import streamlit as st
import json
import base64

class DocumentProcessorUI:
    """UI class for document processing"""
    
    def __init__(self, document_processor):
        self.document_processor = document_processor
    
    def show(self):
        """Display the document processor interface"""
        st.title("📄 Document Processor")
        
        st.write("This tool processes documents to extract text and structure data. Upload any document (image, PDF, or other file types) to begin.")
        
        upload_col, info_col = st.columns([2, 1])
        
        with upload_col:
            uploaded_file = st.file_uploader("Upload a document", 
                                            type=["pdf", "ppt", "pptx", "doc", "docx", "xls", "xlsx", 
                                                "jpg", "jpeg", "png", "gif", "bmp", "txt", "html", "htm", 
                                                "json", "xml", "epub", "md"])
        
        with info_col:
            st.info("""
            Processing methods:
            - Images: OCR technology
            - PDFs: Text extraction or OCR
            - Other files: MarkItDown conversion
            """)
            
            try:
                from markitdown import MarkItDown
                markitdown_available = True
            except ImportError:
                markitdown_available = False
                
            if not markitdown_available:
                st.warning("⚠️ MarkItDown library not installed.")
                
            if not st.session_state.get('deepseek_api_key'):
                st.warning("⚠️ DeepSeek API key not set.")
        
        if uploaded_file:
            with st.spinner("Processing your document..."):
                result = self.document_processor.process_document(uploaded_file)
                st.session_state.processed_document = result
                
                if result["status"] == "error":
                    st.error(f"Error: {result['message']}")
                else:
                    # Display the processing method
                    st.success(f"Document processed using {result['method'].replace('_', ' ').title()}")
                    
                    # Display tabs for different views
                    tab1, tab2, tab3 = st.tabs(["Extracted Text", "Structured Data", "Download Options"])
                    
                    with tab1:
                        if "raw_text" in result:
                            st.subheader("Raw Extracted Text")
                            st.text_area("Text Content", result["raw_text"], height=300)
                        
                        if "formatted_text" in result and result["method"] == "markitdown":
                            st.subheader("Formatted Markdown")
                            st.markdown(result["formatted_text"])
                    
                    with tab2:
                        if "structured_data" in result:
                            st.subheader("Structured Data")
                            st.json(result["structured_data"])
                        
                        if "ai_extracted_text" in result:
                            st.subheader("AI Extracted Information")
                            st.text_area("AI Analysis", result["ai_extracted_text"], height=200)
                    
                    with tab3:
                        st.subheader("Download Options")
                        
                        if "raw_text" in result:
                            st.markdown(self.document_processor.create_download_link(result["raw_text"], "extracted_text.txt"), unsafe_allow_html=True)
                        
                        if "formatted_text" in result and result["method"] == "markitdown":
                            st.markdown(self.document_processor.create_download_link(result["formatted_text"], "converted_content.md"), unsafe_allow_html=True)
                        
                        if "structured_data" in result:
                            st.download_button(
                                label="Download Structured Data (JSON)",
                                data=json.dumps(result["structured_data"], indent=2),
                                file_name="extracted_data.json",
                                mime="application/json"
                            )
                        
                        if "ai_extracted_text" in result:
                            st.markdown(self.document_processor.create_download_link(result["ai_extracted_text"], "ai_analysis.txt"), unsafe_allow_html=True)
                    
                    # Add button to proceed to fraud detection
                    if "structured_data" in result and result["structured_data"]:
                        if st.button("Proceed to Fraud Detection"):
                            st.session_state.processed_document = result
                            st.experimental_set_query_params(page="fraud_detector")  # Hint to switch to fraud detector
                            st.rerun()  # Rerun the app to update the UI
        else:
            st.info("Please upload a document to begin.")