"""
Script to load company knowledge into AutoMem

This populates the global knowledge base with HR policies, company information,
and other documents that should be accessible to all users.

Usage:
    python scripts/load_company_knowledge.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.automem_client import get_default_client


def load_hr_policies():
    """Load HR policies into global knowledge base"""
    automem = get_default_client()
    
    policies = [
        {
            "category": "leave_policy",
            "content": """Leave Policy

Sick Leave:
- 12 days of sick leave per year
- Can be taken without prior approval
- Medical certificate required for absences over 3 consecutive days
- Unused sick leave does not carry forward

Vacation Leave:
- 20 days of paid vacation per year
- Must be approved by manager at least 2 weeks in advance
- Maximum 10 consecutive days without special approval
- Unused vacation can carry forward up to 5 days

Personal Leave:
- 5 days of personal leave per year
- For personal matters, family emergencies
- Requires 1 week advance notice when possible
- Cannot be carried forward""",
            "metadata": {
                "title": "Employee Leave Policy",
                "doc_id": "HR-POL-001",
                "version": "2.1",
                "last_updated": "2024-01-15"
            }
        },
        {
            "category": "work_policy",
            "content": """Remote Work Policy

Eligibility:
- All employees can work remotely up to 3 days per week
- Must maintain core hours: 10 AM - 3 PM in your timezone
- Requires stable internet connection and dedicated workspace

Requirements:
- Attend all scheduled meetings via video
- Respond to messages within 2 hours during work hours
- Available for emergency calls
- Complete security training

Office Days:
- Minimum 2 days per week in office (can be flexible)
- Team meeting days are mandatory in-office
- Prior approval required for fully remote arrangements""",
            "metadata": {
                "title": "Remote Work Policy",
                "doc_id": "HR-POL-002",
                "version": "3.0",
                "last_updated": "2024-02-01"
            }
        },
        {
            "category": "work_policy",
            "content": """Work Hours and Flexibility

Standard Hours:
- 40 hours per week
- Core hours: 10 AM - 3 PM (must be available)
- Flexible start time: 7 AM - 10 AM
- Flexible end time: 3 PM - 7 PM

Overtime:
- Exempt employees: No overtime pay, time-off compensation available
- Non-exempt employees: 1.5x pay for hours over 40/week
- Prior approval required

Breaks:
- 1 hour lunch break (unpaid)
- Two 15-minute breaks (paid)
- Flexible break times""",
            "metadata": {
                "title": "Work Hours Policy",
                "doc_id": "HR-POL-003",
                "version": "1.5",
                "last_updated": "2023-11-20"
            }
        },
        {
            "category": "performance_policy",
            "content": """Performance Review Process

Review Cycle:
- Annual reviews every December
- Mid-year check-ins in June
- Quarterly 1-on-1s with manager

Evaluation Criteria:
- Job performance and goal achievement (40%)
- Team collaboration and communication (30%)
- Innovation and problem-solving (20%)
- Professional development (10%)

Rating Scale:
- Exceeds Expectations (4.5-5.0)
- Meets Expectations (3.5-4.4)
- Needs Improvement (2.5-3.4)
- Unsatisfactory (< 2.5)

Outcomes:
- Salary adjustments based on performance
- Promotion consideration for consistent high performers
- Development plans for improvement areas""",
            "metadata": {
                "title": "Performance Review Policy",
                "doc_id": "HR-POL-004",
                "version": "2.0",
                "last_updated": "2023-12-01"
            }
        },
        {
            "category": "benefits_policy",
            "content": """Employee Benefits

Health Insurance:
- Medical, dental, vision coverage
- Company pays 80% of premiums
- Coverage starts on first day of employment
- Family coverage available

Retirement:
- 401(k) with 5% company match
- Immediate vesting
- Annual financial planning sessions

Professional Development:
- $2,000 annual learning budget per employee
- Conference attendance (2 per year)
- Online course subscriptions
- Mentorship program

Wellness:
- Gym membership reimbursement ($50/month)
- Mental health support (10 free sessions/year)
- Annual health screenings
- Wellness challenges and activities""",
            "metadata": {
                "title": "Employee Benefits Overview",
                "doc_id": "HR-POL-005",
                "version": "4.2",
                "last_updated": "2024-01-01"
            }
        },
        {
            "category": "training_policy",
            "content": """Training and Development Policy

Onboarding:
- 2-week structured onboarding program
- Assigned mentor for first 90 days
- Role-specific training modules
- Monthly new hire check-ins

Continuous Learning:
- Mandatory compliance training annually
- Technical skill development encouraged
- Leadership training for management track
- Cross-functional training opportunities

Certifications:
- Company pays for job-relevant certifications
- Study time allocated during work hours
- Bonus for obtaining critical certifications
- Recertification support

Career Development:
- Individual Development Plans (IDPs)
- Internal job postings
- Rotation programs
- Succession planning""",
            "metadata": {
                "title": "Training and Development Policy",
                "doc_id": "HR-POL-006",
                "version": "1.8",
                "last_updated": "2023-10-15"
            }
        },
        {
            "category": "travel_policy",
            "content": """Business Travel Policy

Approval:
- Manager approval required for all travel
- 2 weeks advance notice preferred
- Budget approval for international travel

Flights:
- Economy class for flights under 6 hours
- Business class for flights over 6 hours
- Book through company travel portal

Accommodation:
- Mid-range hotels (up to $200/night domestic, $250/night international)
- Use preferred hotel chains when available
- Airbnb allowed with approval

Expenses:
- Meals: $75/day domestic, $100/day international
- Ground transportation: Taxis, rideshare, public transit
- Rental cars require special approval
- Submit expenses within 7 days of return

Per Diem:
- Covers meals and incidentals
- No receipts required under per diem
- Additional expenses require receipts""",
            "metadata": {
                "title": "Business Travel Policy",
                "doc_id": "HR-POL-007",
                "version": "2.3",
                "last_updated": "2024-02-10"
            }
        },
        {
            "category": "equipment_policy",
            "content": """Equipment and Technology Policy

Standard Equipment:
- Laptop (Mac or Windows based on role)
- External monitor, keyboard, mouse
- Headset for remote work
- Phone stipend: $50/month

Software:
- All job-required software provided
- License management by IT
- Personal software requires approval

Home Office:
- $500 home office setup stipend
- Ergonomic chair recommended
- Standing desk available on request

Security:
- Encrypted devices mandatory
- VPN required for remote access
- Multi-factor authentication enabled
- Regular security updates

Return Policy:
- All equipment returned upon termination
- Lost/damaged equipment: employee may be charged
- Upgrade cycle: Every 3 years or as needed""",
            "metadata": {
                "title": "Equipment and Technology Policy",
                "doc_id": "HR-POL-008",
                "version": "3.1",
                "last_updated": "2023-12-20"
            }
        },
        {
            "category": "code_of_conduct",
            "content": """Code of Conduct

Professional Behavior:
- Treat everyone with respect and dignity
- No harassment, discrimination, or bullying
- Maintain confidentiality
- Avoid conflicts of interest

Communication:
- Professional and courteous in all interactions
- Constructive feedback encouraged
- Open door policy with management
- Anonymous reporting available

Dress Code:
- Business casual in office
- Client meetings: Business professional
- Remote work: Professional for video calls

Social Media:
- Personal views don't represent company
- No confidential information sharing
- Professional conduct online
- Company social media guidelines apply

Violations:
- Report concerns to HR or manager
- Investigation conducted confidentially
- Appropriate action taken
- Zero tolerance for serious violations""",
            "metadata": {
                "title": "Code of Conduct",
                "doc_id": "HR-POL-009",
                "version": "2.5",
                "last_updated": "2023-09-01"
            }
        },
        {
            "category": "parental_leave",
            "content": """Parental Leave Policy

Eligibility:
- All employees after 90 days of employment
- Applies to birth, adoption, foster care

Leave Duration:
- Primary caregiver: 16 weeks paid leave
- Secondary caregiver: 6 weeks paid leave
- Can be taken within 12 months of child's arrival

Pay:
- 100% salary for first 12 weeks
- 60% salary for remaining weeks
- Benefits continue during leave

Flexible Return:
- Phased return option (part-time for first month)
- Remote work flexibility for first 3 months
- Lactation rooms available in all offices

Additional Benefits:
- $1,000 new parent bonus
- Backup childcare assistance
- Parenting resource program
- Gradual return to work schedule""",
            "metadata": {
                "title": "Parental Leave Policy",
                "doc_id": "HR-POL-010",
                "version": "3.0",
                "last_updated": "2024-01-10"
            }
        }
    ]
    
    print("Loading HR policies into AutoMem...")
    for policy in policies:
        result = automem.store_global_knowledge(
            content=policy["content"],
            category=policy["category"],
            metadata=policy["metadata"]
        )
        if result:
            doc_id = policy["metadata"]["doc_id"]
            print(f"✓ Loaded {doc_id}: {policy['metadata']['title']}")
        else:
            print(f"✗ Failed to load {policy['metadata']['doc_id']}")
    
    print(f"\nSuccessfully loaded {len(policies)} HR policies")


def load_company_info():
    """Load general company information"""
    automem = get_default_client()
    
    company_docs = [
        {
            "category": "company_info",
            "content": """Company Overview

Portonics AI Solutions
Founded: 2019
Headquarters: San Francisco, CA

Mission:
To democratize artificial intelligence and make advanced AI solutions accessible to businesses of all sizes.

Vision:
Become the leading AI solutions provider, known for innovation, reliability, and customer success.

Values:
- Innovation First: Push boundaries and embrace new technologies
- Customer Success: Our success is measured by customer outcomes
- Collaboration: Work together across teams and with clients
- Integrity: Honest, transparent, ethical in all we do
- Continuous Learning: Always growing and improving

Services:
- Custom AI/ML solutions
- AI consulting and strategy
- Model deployment and optimization
- AI training and education

Industries Served:
- Healthcare
- Finance
- Retail
- Manufacturing
- Technology""",
            "metadata": {
                "title": "Company Overview",
                "doc_id": "COM-INFO-001",
                "version": "1.3",
                "last_updated": "2024-01-05"
            }
        },
        {
            "category": "company_info",
            "content": """Office Locations and Contact

Headquarters:
Portonics AI Solutions
123 Market Street, Suite 500
San Francisco, CA 94105
Phone: (415) 555-0100

Regional Offices:

New York Office:
456 Fifth Avenue, Floor 20
New York, NY 10001
Phone: (212) 555-0200

London Office:
789 Tech Square
London EC2A 4BX, UK
Phone: +44 20 1234 5678

Contact Information:
- General Inquiries: info@portonics.ai
- HR: hr@portonics.ai
- IT Support: itsupport@portonics.ai
- Emergency: emergency@portonics.ai

Office Hours:
Monday - Friday: 9 AM - 6 PM (local time)
Weekend: Emergency contacts only""",
            "metadata": {
                "title": "Office Locations and Contact",
                "doc_id": "COM-INFO-002",
                "version": "1.1",
                "last_updated": "2023-11-30"
            }
        },
        {
            "category": "company_info",
            "content": """Teams and Departments

Engineering:
- Backend Development
- Frontend Development
- Machine Learning
- DevOps/Infrastructure
- Quality Assurance

Product:
- Product Management
- Product Design
- User Research

Data:
- Data Science
- Data Engineering
- Analytics

Operations:
- Human Resources
- Finance
- Legal
- IT Support

Sales & Marketing:
- Sales
- Marketing
- Customer Success
- Business Development

Leadership Team:
- CEO: Dr. Sarah Chen
- CTO: Michael Rodriguez
- CPO: Jennifer Park
- CFO: David Thompson
- CHRO: Lisa Anderson""",
            "metadata": {
                "title": "Organizational Structure",
                "doc_id": "COM-INFO-003",
                "version": "2.0",
                "last_updated": "2024-01-20"
            }
        }
    ]
    
    print("\nLoading company information into AutoMem...")
    for doc in company_docs:
        result = automem.store_global_knowledge(
            content=doc["content"],
            category=doc["category"],
            metadata=doc["metadata"]
        )
        if result:
            doc_id = doc["metadata"]["doc_id"]
            print(f"✓ Loaded {doc_id}: {doc['metadata']['title']}")
        else:
            print(f"✗ Failed to load {doc['metadata']['doc_id']}")
    
    print(f"\nSuccessfully loaded {len(company_docs)} company documents")


def main():
    """Main function to load all company knowledge"""
    print("=" * 60)
    print("Loading Company Knowledge into AutoMem")
    print("=" * 60)
    print()
    
    try:
        # Load HR policies
        load_hr_policies()
        
        # Load company info
        load_company_info()
        
        print()
        print("=" * 60)
        print("All company knowledge loaded successfully!")
        print("=" * 60)
        print()
        print("Knowledge can now be retrieved by the knowledge_agent")
        print("when users ask about policies, procedures, or company info.")
        
    except Exception as e:
        print(f"\n✗ Error loading company knowledge: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
