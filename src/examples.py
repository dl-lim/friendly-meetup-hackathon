"""
Example usage and experiments.
"""
from .data_loader import load_sample_data, get_customer_by_id, get_asset_by_id
from .agent import ProactiveAgent


def example_basic_workflow():
    """Basic workflow example."""
    print("=" * 60)
    print("Basic Workflow")
    print("=" * 60)
    
    data = load_sample_data()
    agent = ProactiveAgent()
    cases = agent.process_findings(
        data['risk_findings'],
        data['customers'],
        data['assets']
    )
    
    print(f"\nLoaded {len(data['risk_findings'])} findings")
    print(f"Generated {len(cases)} cases\n")
    
    for case in cases:
        print(f"Case: {case.case_id} | Customer: {case.customer_id}")
        print(f"Message:\n{case.message_draft}\n")
        print("-" * 60)


def example_explore_finding():
    """Explore a specific finding."""
    print("\n" + "=" * 60)
    print("Explore Finding")
    print("=" * 60)
    
    data = load_sample_data()
    kev_finding = next(
        (f for f in data['risk_findings'] if f.get('details', {}).get('is_kev')),
        None
    )
    
    if not kev_finding:
        print("No KEV finding found")
        return
    
    customer = get_customer_by_id(data['customers'], kev_finding['customer_id'])
    asset = get_asset_by_id(data['assets'], kev_finding['asset_id'])
    
    print(f"\nFinding: {kev_finding['finding_id']}")
    print(f"Type: {kev_finding['type']} | Severity: {kev_finding['severity']}")
    print(f"Customer: {customer['company_name']} | Asset: {asset['value']}")
    
    agent = ProactiveAgent()
    should_open = agent.triage_agent.should_open_case(kev_finding, customer, asset)
    print(f"Should open case? {should_open}")


def example_customer_context():
    """How customer context affects severity."""
    print("\n" + "=" * 60)
    print("Customer Context")
    print("=" * 60)
    
    data = load_sample_data()
    agent = ProactiveAgent()
    
    medium_findings = [f for f in data['risk_findings'] if f['severity'] == 'Medium']
    if medium_findings:
        finding = medium_findings[0]
        customer = get_customer_by_id(data['customers'], finding['customer_id'])
        
        print(f"\nFinding: {finding['finding_id']}")
        print(f"Customer: {customer['company_name']} ({customer['risk_profile']})")
        
        effective = agent.triage_agent.assess_effective_severity(
            finding, customer, get_asset_by_id(data['assets'], finding['asset_id'])
        )
        print(f"Base: {finding['severity']} → Effective: {effective}")


if __name__ == "__main__":
    example_basic_workflow()
    example_explore_finding()
    example_customer_context()
