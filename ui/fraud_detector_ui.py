# ui/fraud_detector_ui.py
import streamlit as st
import pandas as pd
import json
import matplotlib.pyplot as plt

class FraudDetectorUI:
    """UI class for invoice fraud detection"""
    
    def __init__(self, invoice_analyzer):
        self.invoice_analyzer = invoice_analyzer
    
    def show(self):
        """Display the fraud detector interface"""
        st.title("🧾 Invoice Fraud Detector")
        
        # Check if there's data from the document processor
        if st.session_state.processed_document and "structured_data" in st.session_state.processed_document:
            st.success("Using data from Document Processor")
            invoice_data = st.session_state.processed_document["structured_data"]
            
            # Display the raw AI response for debugging
            if "ai_extracted_text" in st.session_state.processed_document:
                with st.expander("View Raw AI Response"):
                    st.code(st.session_state.processed_document["ai_extracted_text"])
                    
            # If line_items is empty but we have AI extracted text that has line items, try to use those
            if (not invoice_data.get('line_items') or len(invoice_data.get('line_items', [])) == 0) and "ai_extracted_text" in st.session_state.processed_document:
                ai_text = st.session_state.processed_document["ai_extracted_text"]
                # Look for JSON block
                import re
                json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', ai_text)
                if json_match:
                    try:
                        ai_json = json.loads(json_match.group(1).strip())
                        if 'line_items' in ai_json and len(ai_json['line_items']) > 0:
                            invoice_data['line_items'] = ai_json['line_items']
                            st.info("Imported line items from AI extraction")
                    except:
                        pass
        else:
            st.warning("No data from Document Processor. Upload a JSON directly or return to Document Processor.")
            uploaded_json = st.file_uploader("Upload Invoice JSON", type=["json"])
            
            if uploaded_json:
                try:
                    invoice_data = json.loads(uploaded_json.getvalue().decode())
                except Exception as e:
                    st.error(f"Invalid JSON file: {str(e)}")
                    return
            else:
                st.info("Please upload a JSON file or process a document first.")
                return
        
        # Validate the invoice data
        required_fields = ['invoice_number', 'supplier_name', 'invoice_date', 'tax_id', 'bank_account', 'total_amount']
        missing_fields = []
        
        for field in required_fields:
            if field not in invoice_data or not invoice_data[field]:
                missing_fields.append(field)
        
        if missing_fields:
            st.warning(f"Missing fields in invoice data: {', '.join(missing_fields)}")
        
        if 'line_items' not in invoice_data or not invoice_data['line_items']:
            st.warning("No line items found in the invoice data. Some analysis features will be limited.")
        
        # Display the invoice data
        st.subheader("Invoice Data for Analysis")
        st.json(invoice_data)
        
        # Contract date inputs for validation
        col1, col2 = st.columns(2)
        with col1:
            contract_start = st.date_input("Contract Start Date")
        with col2:
            contract_end = st.date_input("Contract End Date")
        
        if contract_start >= contract_end:
            st.warning("⚠️ Please ensure contract end date is after the start date.")
        
        # Create a placeholder for the analysis results
        analysis_results_placeholder = st.empty()
        
        # Store the analysis result in session state
        if 'analysis_result' not in st.session_state:
            st.session_state.analysis_result = None
        
        # Analyze button
        if st.button("Analyze for Fraud"):
            with st.spinner("Analyzing invoice..."):
                analysis_result = self.invoice_analyzer.analyze_invoice_for_fraud(invoice_data, contract_start, contract_end)
                st.session_state.analysis_result = analysis_result
                
                with analysis_results_placeholder.container():
                    if analysis_result["status"] == "error":
                        st.error(analysis_result["message"])
                    else:
                        st.subheader("Analysis Results")
                        
                        if analysis_result["status"] == "warning":
                            st.warning(analysis_result["message"])
                        else:
                            st.success(analysis_result["message"])
                        
                        invoice = analysis_result["invoice"]
                        
                        if 'anomalous_items' in invoice:
                            st.subheader("Detected Anomalies")
                            
                            # Create visualization
                            try:
                                df_items = pd.DataFrame(invoice['line_items'])
                                fig = self.invoice_analyzer.visualize_anomalies(df_items)
                                st.pyplot(fig)
                            except Exception as e:
                                st.error(f"Error creating visualization: {e}")
                            
                            # List anomalies
                            for idx, item in enumerate(invoice["anomalous_items"]):
                                st.markdown(f"**Item {idx+1}: {item.get('description', 'Unknown item')}**")
                                st.write(f"- Quantity: {item.get('quantity', 'N/A')}")
                                st.write(f"- Unit Price: {item.get('unit_price', 'N/A')}")
                                st.write(f"- Anomaly Score: {item.get('anomaly_score', 'N/A')}")
                                explanation = self.invoice_analyzer.generate_anomaly_explanation(item)
                                st.info(f"📌 Explanation: {explanation}")
                        
                        if 'warnings' in invoice:
                            st.subheader("Warnings")
                            for warning in invoice['warnings']:
                                st.warning(warning)
        
        # Download button - separate from the Analyze button logic
        if st.session_state.analysis_result is not None:
            st.download_button(
                label="📥 Download Analysis Results (JSON)",
                data=json.dumps(st.session_state.analysis_result, indent=2),
                file_name="fraud_analysis.json",
                mime="application/json"
            )