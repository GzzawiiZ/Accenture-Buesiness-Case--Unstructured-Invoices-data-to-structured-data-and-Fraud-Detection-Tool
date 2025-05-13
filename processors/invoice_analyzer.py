# processors/invoice_analyzer.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from sklearn.ensemble import IsolationForest

class InvoiceAnalyzer:
    """Class for analyzing invoices and detecting fraud"""
    
    def analyze_invoice_for_fraud(self, invoice, contract_start=None, contract_end=None):
        """Analyze an invoice for potential fraud or anomalies"""
        issues = []
        
        if not invoice:
            return {"status": "error", "message": "Invalid invoice data"}
        
        required_fields = ['invoice_number', 'supplier_name', 'invoice_date', 'tax_id', 'bank_account', 'total_amount']
        missing_fields = [field for field in required_fields if field not in invoice]
        
        if missing_fields:
            return {
                "status": "warning", 
                "message": f"Missing required fields: {', '.join(missing_fields)}",
                "invoice": invoice
            }
        
        # Date validation
        if contract_start and contract_end and 'invoice_date' in invoice:
            try:
                invoice_date_obj = datetime.strptime(invoice['invoice_date'], "%m/%d/%Y")
                if not (contract_start <= invoice_date_obj.date() <= contract_end):
                    issues.append("Invoice date is outside the contract period.")
            except:
                issues.append("Unable to parse invoice date format.")
        
        # Line item analysis
        if 'line_items' in invoice and invoice['line_items']:
            for item in invoice['line_items']:
                if 'unit_price' in item and item['unit_price'] and item['unit_price'] > 100:
                    issues.append(f"High unit price detected: {item['unit_price']} for {item['description']}")
            
            # Anomaly detection with machine learning
            df_items = pd.DataFrame(invoice['line_items'])
            if 'unit_price' in df_items.columns and 'quantity' in df_items.columns:
                model = IsolationForest(contamination=0.25, random_state=42)
                df_numeric = df_items[['unit_price', 'quantity']].dropna()
                if not df_numeric.empty:
                    model.fit(df_numeric)
                    df_items['anomaly_score'] = model.decision_function(df_numeric)
                    df_items['is_anomaly'] = model.predict(df_numeric)
                    anomalies = df_items[df_items['is_anomaly'] == -1]
                    if not anomalies.empty:
                        invoice['anomalous_items'] = anomalies.to_dict(orient='records')
                        issues.append("Potential fraud/anomalies detected via machine learning model.")
        
        if issues:
            invoice['warnings'] = issues
            return {
                "status": "warning",
                "message": "Analysis completed with warnings",
                "invoice": invoice
            }
        
        return {
            "status": "success",
            "message": "No issues detected",
            "invoice": invoice
        }
    
    def generate_anomaly_explanation(self, item):
        """Generate an explanation for an anomalous item"""
        if item['unit_price'] > 100:
            return "This item has a high unit price which may be unusual for this type of product."
        elif item['quantity'] > 10:
            return "High quantity detected, might be bulk order or mis-entry."
        else:
            return "Anomaly detection based on unit price and quantity patterns."
    
    def visualize_anomalies(self, df_items):
        """Create a visualization of anomalies"""
        fig, ax = plt.subplots()
        ax.scatter(df_items['unit_price'], df_items['quantity'], 
                c=df_items.get('is_anomaly', ['blue'] * len(df_items)), 
                cmap='coolwarm', s=100)
        ax.set_xlabel("Unit Price")
        ax.set_ylabel("Quantity")
        ax.set_title("Anomaly Detection on Line Items")
        return fig