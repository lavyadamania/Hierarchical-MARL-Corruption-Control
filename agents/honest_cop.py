class HonestCop:
    def __init__(self, agent_id, name, integrity_score):
        self.agent_id = agent_id
        self.name = name
        self.cop_type = 'honest'
        self.rank = 'constable'
        self.personality = 'none' # Honest cops don't have the risk personalities
        self.corruption_score = 0.0 # Meaningless for honest, but keeping schema consistent
        self.integrity_score = integrity_score # 80-100
        
        self.loyalty_score = 100.0
        self.times_caught = 0
        self.total_money_earned = 0.0
        self.reports_filed = 0
        self.bribes_rejected = 0

    def decide_bribe(self, state, current_episode=0):
        """
        Honest Cop Logic: Always choose a Lawful Action based on the situation.
        Never 'Inactive'.
        """
        severity = state.get('severity', 1)
        offer = state.get('offer', 0)
        has_warrant = state.get('has_warrant', False)
        evidence = state.get('evidence_strength', 0.5)
        
        # Rule 1: High Crimes (Murder, Cartel) -> ARREST immediately if possible
        if severity >= 8:
            if has_warrant or evidence > 0.6:
                return 'ARREST'
            return 'REQUEST_WARRANT'
            
        # Rule 2: Middle Crimes with High Bribe -> ARREST for Attempted Bribery or REPORT
        if offer > 50:
            if evidence > 0.5:
                return 'ARREST' # Arrest for bribery
            return 'REPORT_BRIBE'

        # Rule 3: Low Crimes (Traffic) -> TICKET
        if severity <= 3:
            return 'ISSUE_TICKET'
            
        # Rule 4: Standard Procedure
        if evidence > 0.7:
             return 'ARREST'
             
        # Fallback: Investigate to gather evidence (Active policing)
        return 'INVESTIGATE'

    def witness_corruption(self):
        """Logic for witnessing and reporting."""
        # Simple logic: Always reports if they see something
        self.reports_filed += 1
        return True

    def __repr__(self):
        return f"HonestCop(#{self.agent_id}, I:{self.integrity_score}, Reports:{self.reports_filed})"
