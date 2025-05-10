from flask import Flask, request, jsonify, redirect, render_template_string
import os
import json
import uuid
from datetime import datetime
import logging
from dotenv import load_dotenv
from payment_processors.stripe_integration import StripeIntegration
from payment_processors.paypal_integration import PayPalIntegration

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/api_service.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("api_service")

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your_secure_secret_key_here")

# Initialize payment processors
stripe_integration = StripeIntegration()
paypal_integration = PayPalIntegration()

# Load configuration
def load_config():
    try:
        with open("config/config.json", 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}

config = load_config()

# Load projects
def load_projects():
    return config.get("projects", {})

projects = load_projects()

# Simple in-memory database for funding records
funding_records = []

@app.route('/')
def home():
    """Home page"""
    # Simple HTML template for the home page
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Open Source Project Funding</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                max-width: 800px;
                margin: 0 auto;
            }
            h1 {
                color: #333;
            }
            .project {
                border: 1px solid #ddd;
                padding: 15px;
                margin-bottom: 20px;
                border-radius: 5px;
            }
            .project h2 {
                margin-top: 0;
            }
            .btn {
                display: inline-block;
                background: #4CAF50;
                color: white;
                padding: 10px 15px;
                text-decoration: none;
                border-radius: 5px;
                margin-right: 10px;
            }
            .btn:hover {
                background: #45a049;
            }
        </style>
    </head>
    <body>
        <h1>Open Source Project Funding</h1>
        <p>Support these important open source projects that will make a difference in students' lives.</p>
        
        {% for project_id, project in projects.items() %}
        <div class="project">
            <h2>{{ project.name }}</h2>
            <p>{{ project.description }}</p>
            <p><strong>Funding Goal:</strong> {{ project.currency }} {{ project.funding_goal }}</p>
            <a href="/fund/{{ project_id }}" class="btn">Fund This Project</a>
        </div>
        {% endfor %}
    </body>
    </html>
    """
    return render_template_string(html, projects=projects)

@app.route('/fund/<project_id>')
def fund_project(project_id):
    """Fund a project page"""
    if project_id not in projects:
        return jsonify({"error": "Project not found"}), 404
    
    project = projects[project_id]
    
    # Simple HTML template for the funding page
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Fund {{ project.name }}</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                max-width: 800px;
                margin: 0 auto;
            }
            h1 {
                color: #333;
            }
            .form-group {
                margin-bottom: 15px;
            }
            label {
                display: block;
                margin-bottom: 5px;
            }
            input, select {
                width: 100%;
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            .btn {
                display: inline-block;
                background: #4CAF50;
                color: white;
                padding: 10px 15px;
                text-decoration: none;
                border-radius: 5px;
                border: none;
                cursor: pointer;
                font-size: 16px;
            }
            .btn:hover {
                background: #45a049;
            }
            .payment-options {
                display: flex;
                gap: 10px;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <h1>Fund {{ project.name }}</h1>
        <p>{{ project.description }}</p>
        <p><strong>Funding Goal:</strong> {{ project.currency }} {{ project.funding_goal }}</p>
        
        <form id="fundingForm">
            <div class="form-group">
                <label for="amount">Amount ({{ project.currency }}):</label>
                <input type="number" id="amount" name="amount" min="1" step="1" required>
            </div>
            
            <div class="form-group">
                <label for="name">Your Name:</label>
                <input type="text" id="name" name="name" required>
            </div>
            
            <div class="form-group">
                <label for="email">Your Email:</label>
                <input type="email" id="email" name="email" required>
            </div>
            
            <div class="form-group">
                <label for="message">Message (Optional):</label>
                <input type="text" id="message" name="message">
            </div>
            
            <div class="payment-options">
                <button type="button" class="btn" onclick="payWithStripe()">Pay with Stripe</button>
                <button type="button" class="btn" onclick="payWithPayPal()">Pay with PayPal</button>
            </div>
        </form>
        
        <script>
            function payWithStripe() {
                const amount = document.getElementById('amount').value;
                const name = document.getElementById('name').value;
                const email = document.getElementById('email').value;
                const message = document.getElementById('message').value;
                
                if (!amount || !name || !email) {
                    alert('Please fill in all required fields');
                    return;
                }
                
                window.location.href = `/api/v1/fund/stripe/{{ project_id }}?amount=${amount}&name=${encodeURIComponent(name)}&email=${encodeURIComponent(email)}&message=${encodeURIComponent(message)}`;
            }
            
            function payWithPayPal() {
                const amount = document.getElementById('amount').value;
                const name = document.getElementById('name').value;
                const email = document.getElementById('email').value;
                const message = document.getElementById('message').value;
                
                if (!amount || !name || !email) {
                    alert('Please fill in all required fields');
                    return;
                }
                
                window.location.href = `/api/v1/fund/paypal/{{ project_id }}?amount=${amount}&name=${encodeURIComponent(name)}&email=${encodeURIComponent(email)}&message=${encodeURIComponent(message)}`;
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html, project=project)

@app.route('/api/v1/fund/stripe/<project_id>')
def fund_with_stripe(project_id):
    """Fund a project with Stripe"""
    if project_id not in projects:
        return jsonify({"error": "Project not found"}), 404
    
    project = projects[project_id]
    
    # Get query parameters
    amount = float(request.args.get('amount', 0))
    name = request.args.get('name', '')
    email = request.args.get('email', '')
    message = request.args.get('message', '')
    
    if amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400
    
    # Create a checkout session
    checkout_url = stripe_integration.create_checkout_session(
        project_id=project_id,
        amount=amount,
        currency=project["currency"].lower(),
        description=f"Funding for {project['name']}"
    )
    
    if not checkout_url:
        return jsonify({"error": "Failed to create checkout session"}), 500
    
    # Store the funding record
    funding_record = {
        "id": str(uuid.uuid4()),
        "project_id": project_id,
        "amount": amount,
        "currency": project["currency"],
        "name": name,
        "email": email,
        "message": message,
        "payment_method": "stripe",
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    
    funding_records.append(funding_record)
    
    # Redirect to the checkout URL
    return redirect(checkout_url)

@app.route('/api/v1/fund/paypal/<project_id>')
def fund_with_paypal(project_id):
    """Fund a project with PayPal"""
    if project_id not in projects:
        return jsonify({"error": "Project not found"}), 404
    
    project = projects[project_id]
    
    # Get query parameters
    amount = float(request.args.get('amount', 0))
    name = request.args.get('name', '')
    email = request.args.get('email', '')
    message = request.args.get('message', '')
    
    if amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400
    
    # Create a PayPal payment
    payment_url = paypal_integration.create_payment(
        project_id=project_id,
        amount=amount,
        currency=project["currency"],
        description=f"Funding for {project['name']}"
    )
    
    if not payment_url:
        return jsonify({"error": "Failed to create payment"}), 500
    
    # Store the funding record
    funding_record = {
        "id": str(uuid.uuid4()),
        "project_id": project_id,
        "amount": amount,
        "currency": project["currency"],
        "name": name,
        "email": email,
        "message": message,
        "payment_method": "paypal",
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    
    funding_records.append(funding_record)
    
    # Redirect to the payment URL
    return redirect(payment_url)

@app.route('/webhooks/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    payload = request.data
    signature = request.headers.get('Stripe-Signature', '')
    
    success = stripe_integration.handle_webhook(payload, signature)
    
    if success:
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"status": "error"}), 400

@app.route('/webhooks/paypal', methods=['POST'])
def paypal_webhook():
    """Handle PayPal webhook events"""
    payload = request.json
    
    success = paypal_integration.handle_webhook(payload)
    
    if success:
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"status": "error"}), 400

@app.route('/success')
def success():
    """Success page after payment"""
    # Simple HTML template for the success page
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Payment Successful</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                max-width: 800px;
                margin: 0 auto;
                text-align: center;
            }
            h1 {
                color: #4CAF50;
            }
            .btn {
                display: inline-block;
                background: #4CAF50;
                color: white;
                padding: 10px 15px;
                text-decoration: none;
                border-radius: 5px;
                margin-top: 20px;
            }
            .btn:hover {
                background: #45a049;
            }
        </style>
    </head>
    <body>
        <h1>Thank You for Your Support!</h1>
        <p>Your payment was successful. Your contribution will help make these open source projects a reality.</p>
        <a href="/" class="btn">Return to Home</a>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/cancel')
def cancel():
    """Cancel page after payment cancellation"""
    # Simple HTML template for the cancel page
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Payment Cancelled</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                max-width: 800px;
                margin: 0 auto;
                text-align: center;
            }
            h1 {
                color: #f44336;
            }
            .btn {
                display: inline-block;
                background: #4CAF50;
                color: white;
                padding: 10px 15px;
                text-decoration: none;
                border-radius: 5px;
                margin-top: 20px;
            }
            .btn:hover {
                background: #45a049;
            }
        </style>
    </head>
    <body>
        <h1>Payment Cancelled</h1>
        <p>Your payment was cancelled. If you change your mind, you can still support the projects.</p>
        <a href="/" class="btn">Return to Home</a>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/api/v1/projects', methods=['GET'])
def get_projects():
    """Get all projects"""
    return jsonify(projects)

@app.route('/api/v1/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """Get a project by ID"""
    if project_id not in projects:
        return jsonify({"error": "Project not found"}), 404
    
    return jsonify(projects[project_id])

@app.route('/api/v1/funding-records', methods=['GET'])
def get_funding_records():
    """Get all funding records"""
    return jsonify(funding_records)

@app.route('/dashboard')
def dashboard():
    """Dashboard page"""
    # Calculate total funding for each project
    project_funding = {}
    for project_id in projects:
        project_funding[project_id] = {
            "total": 0,
            "currency": projects[project_id]["currency"],
            "records": []
        }
    
    for record in funding_records:
        if record["status"] == "completed" and record["project_id"] in project_funding:
            project_funding[record["project_id"]]["total"] += record["amount"]
            project_funding[record["project_id"]]["records"].append(record)
    
    # Simple HTML template for the dashboard
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Funding Dashboard</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                max-width: 1000px;
                margin: 0 auto;
            }
            h1, h2 {
                color: #333;
            }
            .project {
                border: 1px solid #ddd;
                padding: 15px;
                margin-bottom: 20px;
                border-radius: 5px;
            }
            .project h2 {
                margin-top: 0;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }
            th, td {
                padding: 8px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #f2f2f2;
            }
        </style>
    </head>
    <body>
        <h1>Funding Dashboard</h1>
        
        {% for project_id, project in projects.items() %}
        <div class="project">
            <h2>{{ project.name }}</h2>
            <p>{{ project.description }}</p>
            <p><strong>Funding Goal:</strong> {{ project.currency }} {{ project.funding_goal }}</p>
            <p><strong>Total Funding:</strong> {{ project.currency }} {{ project_funding[project_id].total }}</p>
            <p><strong>Progress:</strong> {{ (project_funding[project_id].total / project.funding_goal * 100) | round(2) }}%</p>
            
            <h3>Funding Records</h3>
            {% if project_funding[project_id].records %}
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Name</th>
                        <th>Amount</th>
                        <th>Payment Method</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for record in project_funding[project_id].records %}
                    <tr>
                        <td>{{ record.created_at }}</td>
                        <td>{{ record.name }}</td>
                        <td>{{ record.currency }} {{ record.amount }}</td>
                        <td>{{ record.payment_method }}</td>
                        <td>{{ record.status }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <p>No funding records yet.</p>
            {% endif %}
        </div>
        {% endfor %}
    </body>
    </html>
    """
    return render_template_string(html, projects=projects, project_funding=project_funding)

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=True)