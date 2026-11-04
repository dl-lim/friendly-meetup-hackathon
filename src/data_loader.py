"""
Load and parse sample data.
"""
import json
from pathlib import Path
from typing import Dict, List, Any


def load_sample_data(data_path: str = None) -> Dict[str, Any]:
    """Load sample dataset from JSON."""
    if data_path is None:
        repo_root = Path(__file__).parent.parent
        data_path = repo_root / "data" / "sample_data.json"
    
    with open(data_path, 'r') as f:
        return json.load(f)


def get_customer_by_id(customers: List[Dict], customer_id: str) -> Dict:
    """Get customer by ID."""
    for customer in customers:
        if customer['customer_id'] == customer_id:
            return customer
    raise ValueError(f"Customer {customer_id} not found")


def get_asset_by_id(assets: List[Dict], asset_id: str) -> Dict:
    """Get asset by ID."""
    for asset in assets:
        if asset['asset_id'] == asset_id:
            return asset
    raise ValueError(f"Asset {asset_id} not found")


def get_findings_for_customer(findings: List[Dict], customer_id: str) -> List[Dict]:
    """Get all findings for a customer."""
    return [f for f in findings if f['customer_id'] == customer_id]


def get_findings_for_asset(findings: List[Dict], asset_id: str) -> List[Dict]:
    """Get all findings for an asset."""
    return [f for f in findings if f['asset_id'] == asset_id]


if __name__ == "__main__":
    data = load_sample_data()
    print(f"Customers: {len(data['customers'])}")
    print(f"Assets: {len(data['assets'])}")
    print(f"Findings: {len(data['risk_findings'])}")
