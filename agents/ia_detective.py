import random
from config import EVIDENCE_THRESHOLD

class IADetective:
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.name = "Det_Holmes"
        self.cop_type = 'detective'
        self.rank = 'detective'
        self.investigation_skill = 0.9 # High skill
        
        # Corruption Stats
        self.corruption_score = 40.0
        self.total_money_earned = 0.0
        
        self.cases_solved = 0
        self.cases_failed = 0

    def conduct_investigation(self, target_cop_data):
        """
        Returns: (Outcome_String, Bribe_Amount)
        Outcome in ['STRONG', 'MODERATE', 'WEAK', 'COVERUP']
        """
        # Probability to find existing evidence
        evidence_found_prob = self.investigation_skill * 0.8
        
        if random.random() < evidence_found_prob:
            # Evidence found, calculate strength
            evidence_score = (target_cop_data['corruption_score'] * 0.6) + \
                             (target_cop_data['times_caught'] * 15)
            
            # DECISION: Report or Coverup?
            # If IA Corrupt (>30) and Case is juicy (Strong/Moderate)
            if self.corruption_score > 30 and evidence_score > 30:
                if random.random() < (self.corruption_score / 120.0):
                    # Take Hush Money!
                    bribe = 5000 if evidence_score > 60 else 2000
                    self.total_money_earned += bribe
                    self.corruption_score += 2 # Gets more corrupt
                    return 'COVERUP', bribe

            if evidence_score > EVIDENCE_THRESHOLD: # 60
                self.cases_solved += 1
                return 'STRONG', 0
            elif evidence_score > 30:
                self.cases_solved += 1
                return 'MODERATE', 0
            else:
                self.cases_failed += 1
                return 'WEAK', 0
        else:
            self.cases_failed += 1
            return 'WEAK', 0

    def __repr__(self):
        return f"IADetective(#{self.agent_id}, Solved:{self.cases_solved}, Failed:{self.cases_failed})"
