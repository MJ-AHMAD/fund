#!/usr/bin/env python3

import os
import json
import uuid
from datetime import datetime

def add_initial_funds():
    """Add initial funds to the system"""
    try:
        # Load the funding records
        funding_records_path = "data/funding_records.json"
        
        if os.path.exists(funding_records_path):
            with open(funding_records_path, 'r') as f:
                funding_records = json.load(f)
        else:
            funding_records = []
        
        # Add initial funds for each project
        projects = {
            "project_1": {
                "name": "Open Source Project 1",
                "amount": 500,
                "currency": "USD"
            },
            "project_2": {
                "name": "Open Source Project 2",
                "amount": 300,
                "currency": "USD"
            },
            "project_3": {
                "name": "Open Source Project 3",
                "amount": 200,
                "currency": "USD"
            }
        }
        
        for project_id, project in projects.items():
            # Create a funding record
            funding_record = {
                "id": str(uuid.uuid4()),
                "project_id": project_id,
                "amount": project["amount"],
                "currency": project["currency"],
                "name": "Initial Funding",
                "email": "initial@example.com",
                "message": "Initial funding to bootstrap the project",
                "payment_method": "manual",
                "status": "completed",
                "created_at": datetime.now().isoformat()
            }
            
            funding_records.append(funding_record)
            
            print(f"Added {project['currency']} {project['amount']} to {project['name']}")
        
        # Save the funding records
        os.makedirs(os.path.dirname(funding_records_path), exist_ok=True)
        with open(funding_records_path, 'w') as f:
            json.dump(funding_records, f, indent=2)
        
        print(f"Initial funds added successfully")
        return True
        
    except Exception as e:
        print(f"Failed to add initial funds: {e}")
        return False

if __name__ == "__main__":
    add_initial_funds()