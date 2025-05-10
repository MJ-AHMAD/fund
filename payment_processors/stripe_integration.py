import os
import stripe
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/stripe_integration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("stripe_integration")

class StripeIntegration:
    def __init__(self, api_key_path: str = "config/api_keys.json", config_path: str = "config/config.json"):
        self.api_key_path = api_key_path
        self.config_path = config_path
        self.api_key = self._load_api_key()
        self.config = self._load_config()
        
        # Initialize Stripe
        stripe.api_key = self.api_key
        
    def _load_api_key(self) -> str:
        """Load the API key for Stripe"""
        try:
            with open(self.api_key_path, 'r') as f:
                api_keys = json.load(f)
                return api_keys.get("stripe", "")
        except Exception as e:
            logger.error(f"Failed to load API key: {e}")
            return os.getenv("STRIPE_SECRET_KEY", "")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load the configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                return config.get("payment_processors", {}).get("stripe", {})
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def create_payment_link(self, project_id: str, amount: float, currency: str = "usd", 
                          description: str = "") -> Optional[str]:
        """Create a payment link for a project"""
        try:
            # Create a product for the project
            product = stripe.Product.create(
                name=f"Funding for {project_id}",
                description=description or f"Funding contribution for {project_id}"
            )
            
            # Create a price for the product
            price = stripe.Price.create(
                product=product.id,
                unit_amount=int(amount * 100),  # Convert to cents
                currency=currency.lower()
            )
            
            # Create a payment link
            payment_link = stripe.PaymentLink.create(
                line_items=[{"price": price.id, "quantity": 1}],
                after_completion={"type": "redirect", "redirect": {"url": self.config.get("success_url", "")}}
            )
            
            logger.info(f"Created payment link for {project_id}: {payment_link.url}")
            return payment_link.url
            
        except Exception as e:
            logger.error(f"Failed to create payment link: {e}")
            return None
    
    def create_checkout_session(self, project_id: str, amount: float, currency: str = "usd", 
                              description: str = "") -> Optional[str]:
        """Create a checkout session for a project"""
        try:
            # Create a checkout session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": currency.lower(),
                        "product_data": {
                            "name": f"Funding for {project_id}",
                            "description": description or f"Funding contribution for {project_id}"
                        },
                        "unit_amount": int(amount * 100)  # Convert to cents
                    },
                    "quantity": 1
                }],
                mode="payment",
                success_url=self.config.get("success_url", ""),
                cancel_url=self.config.get("cancel_url", "")
            )
            
            logger.info(f"Created checkout session for {project_id}: {checkout_session.id}")
            return checkout_session.url
            
        except Exception as e:
            logger.error(f"Failed to create checkout session: {e}")
            return None
    
    def handle_webhook(self, payload: Dict[str, Any], signature: str) -> bool:
        """Handle a webhook event from Stripe"""
        try:
            # Verify the webhook signature
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                os.getenv("STRIPE_WEBHOOK_SECRET", "")
            )
            
            # Handle the event
            if event.type == "checkout.session.completed":
                session = event.data.object
                logger.info(f"Payment succeeded: {session.id}")
                
                # Process the payment (e.g., update your database)
                # This is where you would update your funding records
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to handle webhook: {e}")
            return False

# Example usage
if __name__ == "__main__":
    # Create a Stripe integration
    stripe_integration = StripeIntegration()
    
    # Create a payment link
    payment_link = stripe_integration.create_payment_link(
        project_id="project_1",
        amount=100.0,
        currency="usd",
        description="Funding for Open Source Project 1"
    )
    
    print(f"Payment link: {payment_link}")