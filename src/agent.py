"""
Agentic AI system for triaging risks and drafting customer notifications.
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class CaseStatus(Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    SENT = "sent"
    RESOLVED = "resolved"


@dataclass
class Case:
    case_id: str
    customer_id: str
    finding_ids: List[str]
    status: CaseStatus
    created_timestamp: str
    message_draft: Optional[str] = None


class RiskTriageAgent:
    """Decides whether a risk finding should result in a case."""
    
    def should_open_case(
        self,
        finding: Dict[str, Any],
        customer: Dict[str, Any],
        asset: Dict[str, Any]
    ) -> bool:
        """Should we notify the customer about this finding?"""
        # TODO: Implement your logic
        severity = finding.get('severity', '').lower()
        confidence = finding.get('confidence', '').lower()
        
        if severity in ['high', 'critical'] and confidence == 'high':
            return True
        
        return False
    
    def assess_effective_severity(
        self,
        finding: Dict[str, Any],
        customer: Dict[str, Any],
        asset: Dict[str, Any]
    ) -> str:
        """Assess severity considering customer context."""
        base_severity = finding.get('severity', 'Medium')
        
        # Example: Upgrade severity for high-value customers
        if customer.get('risk_profile') == 'high-value':
            severity_map = {
                'Low': 'Medium',
                'Medium': 'High',
                'High': 'Critical',
                'Critical': 'Critical'
            }
            return severity_map.get(base_severity, base_severity)
        
        return base_severity


class NotificationDraftingAgent:
    """Drafts customer-friendly notification messages."""
    
    def draft_notification(
        self,
        case: Case,
        finding: Dict[str, Any],
        customer: Dict[str, Any],
        asset: Dict[str, Any]
    ) -> str:
        """Generate a notification message for the customer."""
        # TODO: Implement your drafting logic (template, LLM, or hybrid)
        severity = finding.get('severity', 'Unknown')
        finding_type = finding.get('type', 'risk')
        
        message = f"""
            Dear {customer.get('company_name', 'Customer')},

            We have detected a {severity.lower()} severity {finding_type} on your asset {asset.get('value', 'unknown')}.

            Details:
            {self._format_finding_details(finding)}

            Recommended Actions:
            {self._format_mitigation_steps(finding)}

            If you have questions, please contact our security team.

            Best regards,
            Proactive Security Team
        """.strip()
        
        return message
    
    def _format_finding_details(self, finding: Dict[str, Any]) -> str:
        """Format finding details for the notification."""
        details = finding.get('details', {})
        
        if finding.get('type') == 'cve':
            return f"CVE: {details.get('cve_id', 'Unknown')}\nCVSS Score: {details.get('cvss_score', 'N/A')}\nDescription: {details.get('description', 'No description')}"
        elif finding.get('type') == 'exposed_service':
            return f"Service: {finding.get('subtype', 'Unknown')}\nPort: {details.get('port', 'N/A')}\nDescription: {details.get('description', 'No description')}"
        else:
            return details.get('description', 'No details available')
    
    def _format_mitigation_steps(self, finding: Dict[str, Any]) -> str:
        """Format mitigation steps for the notification."""
        details = finding.get('details', {})
        
        if 'recommendation' in details:
            return f"1. {details['recommendation']}"
        elif 'fixed_version' in details:
            return f"1. Update to version {details['fixed_version']} or later"
        else:
            return "1. Review the finding and take appropriate action based on your security policies"


class ProactiveAgent:
    """Main orchestrating agent."""
    
    def __init__(self):
        self.triage_agent = RiskTriageAgent()
        self.drafting_agent = NotificationDraftingAgent()
    
    def process_findings(
        self,
        findings: List[Dict[str, Any]],
        customers: List[Dict[str, Any]],
        assets: List[Dict[str, Any]]
    ) -> List[Case]:
        """Process risk findings and generate cases."""
        cases = []
        
        customer_map = {c['customer_id']: c for c in customers}
        asset_map = {a['asset_id']: a for a in assets}
        
        for finding in findings:
            customer_id = finding['customer_id']
            asset_id = finding['asset_id']
            
            customer = customer_map.get(customer_id)
            asset = asset_map.get(asset_id)
            
            if not customer or not asset:
                print(f"Warning: Missing customer or asset for finding {finding['finding_id']}")
                continue
            
            if self.triage_agent.should_open_case(finding, customer, asset):
                case_id = f"CASE-{finding['finding_id']}"
                case = Case(
                    case_id=case_id,
                    customer_id=customer_id,
                    finding_ids=[finding['finding_id']],
                    status=CaseStatus.DRAFT,
                    created_timestamp=finding['timestamp']
                )
                
                case.message_draft = self.drafting_agent.draft_notification(
                    case, finding, customer, asset
                )
                
                cases.append(case)
        
        return cases
