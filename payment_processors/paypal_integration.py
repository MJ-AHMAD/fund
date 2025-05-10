import os
import json
import logging
import paypalrestsdk
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/paypal_integration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("paypal_integration")

class PayPalIntegration:
    def __init__(self, api_key_path: str = "config/api_keys.json", config_path: str = "config/config.json"):
        self.api_key_path = api_key_path
        self.config_path = config_path
        self.api_keys = self._load_api_keys()
        self.config = self._load_config()
        
        # Initialize PayPal
        paypalrestsdk.configure({
            "mode": os.getenv("PAYPAL_MODE", "sandbox"),  # sandbox or live
            "client_id": self.api_keys.get("paypal_client_id", ""),
            "client_secret": self.api_keys.get("paypal_secret", "")
        })
        
    def _load_api_keys(self) -> Dict[str, str]:
        """Load the API keys for PayPal"""
        try:
            with open(self.api_key_path, 'r') as f:
                api_keys = json.load(f)
                return {
                    "paypal_client_id": api_keys.get("paypal_client_id", ""),
                    "paypal_secret": api_keys.get("paypal_secret", "")
                }
        except Exception as e:
            logger.error(f"Failed to load API keys: {e}")
            return {
                "paypal_client_id": os.getenv("PAYPAL_CLIENT_ID", ""),
                "paypal_secret": os.getenv("PAYPAL_SECRET", "")
            }
    
    def _load_config(self) -> Dict[str, Any]:
        """Load the configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                return config.get("payment_processors", {}).get("paypal", {})
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def create_payment(self, project_id: str, amount: float, currency: str = "USD", 
                     description: str = "") -> Optional[str]:
        """Create a PayPal payment for a project"""
        try:
            # Create a payment
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "redirect_urls": {
                    "return_url": self.config.get("success_url", ""),
                    "cancel_url": self.config.get("cancel_url", "")
                },
                "transactions": [{
                    "amount": {
                        "total": str(amount),
                        "currency": currency
                    },
                    "description": description or f"Funding for {project_id}"
                }]
            })
            
            # Create the payment
            if payment.create():
                logger.info(f"Created payment for {project_id}: {payment.id}")
                
                # Get the approval URL
                for link in payment.links:
                    if link.rel == "approval_url":
                        return link.href
                
                return None
            else:
                logger.error(f"Failed to create payment: {payment.error}")
                return None
            
        except Exception as e:
            logger.error(f"Failed to create payment: {e}")
            return None
    
    def execute_payment(self, payment_id: str, payer_id: str) -> bool:
        """Execute a PayPal payment"""
        try:
            # Get the payment
            payment = paypalrestsdk.Payment.find(payment_id)
            
            # Execute the payment
            if payment.execute({"payer_id": payer_id}):
                logger.info(f"Payment executed: {payment.id}")
                return True
            else:
                logger.error(f"Failed to execute payment: {payment.error}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to execute payment: {e}")
            return False
    
    def handle_webhook(self, payload: Dict[str, Any]) -> bool:
        """Handle a webhook event from PayPal"""
        try:
            # Get the event type
            event_type = payload.get("event_type", "")
            
            # Handle the event
            if event_type == "PAYMENT.SALE.COMPLETED":
                resource = payload.get("resource", {})
                payment_id = resource.get("parent_payment", "")
                
                logger.info(f"Payment completed: {payment_id}")
                
                # Process the payment (e.g., update your database)
                # This is where you would update your funding records
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to handle webhook: {e}")
            return False

# Example usage
if __name__ == "__main__":
    # Create a PayPal integration
    paypal_integration = PayPalIntegration()
    
    # Create a payment
    payment_url = paypal_integration.create_payment(
        project_id="project_1",
        amount=100.0,
        currency="USD",
        description="Funding for Open Source Project 1"
    )
    
    print(f"Payment URL: {payment_url}")