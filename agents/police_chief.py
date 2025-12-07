import random

class PoliceChief:
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.name = "Chief_Justice"
        self.cop_type = 'chief'
        self.rank = 'chief'
        
        # New Stats for Corruption
        self.corruption_score = 50.0 # Starts mid-way
        self.total_money_earned = 0.0
        
        self.investigations_ordered = 0
        self.officers_fired = 0

    def monitor_subordinates(self, db_cops):
        """
        db_cops: List of dictionaries or objects containing cop stats from DB.
        Returns list of orders (dictionaries).
        """
        orders = []
        for cop in db_cops:
            if cop['rank'] == 'constable':
                suspicion_score = (cop['corruption_score'] * 0.6) + \
                                  (cop['times_bribed'] * 5) + \
                                  (cop['times_caught'] * 10)
                
                # If suspicious
                if suspicion_score > 70.0:
                    # CORRUPT DECISION: Blackmail or Investigate?
                    # If Chief is corrupt (Score > 40) AND Target has money
                    # We don't have target money in this simplified list pass, assume lucrative if High Corruption
                    
                    # Logic: If Chief is corrupt, he prefers money over justice
                    if self.corruption_score > 40 and random.random() < (self.corruption_score / 150.0):
                        # Dynamic Blackmail Calculation
                        # 'Tax' the officer based on their earnings
                        target_wealth = cop.get('total_money_earned', 0)
                        
                        if target_wealth > 2000:
                            # 30% Wealth Tax + Service Fee
                            blackmail_amount = int((target_wealth * 0.3) + (suspicion_score * 50))
                            
                            orders.append({
                                'type': 'BLACKMAIL',
                                'target_cop_id': cop['cop_id'],
                                'details': f"Extortion: {blackmail_amount} (30% of {target_wealth})",
                                'amount': blackmail_amount
                            })
                        else:
                             # Too poor to blackmail, just investigate/punish normally
                             orders.append({
                                'type': 'INVESTIGATE',
                                'target_cop_id': cop['cop_id'],
                                'details': f"Poor & Suspicious (Wealth: {target_wealth})"
                            })
                    else:
                        # Legitimate Duty
                        orders.append({
                            'type': 'INVESTIGATE',
                            'target_cop_id': cop['cop_id'],
                            'details': f"High suspicion score: {suspicion_score:.1f}"
                        })
                        self.investigations_ordered += 1
        return orders

    def decide_punishment(self, investigation_result, target_cop_data):
        """
        Decides punishment based on investigation outcome.
        investigation_result: 'STRONG', 'MODERATE', 'WEAK'
        target_cop_data: dict with 'times_caught', 'corruption_score'
        """
        if investigation_result == 'WEAK':
            return 'INSUFFICIENT_EVIDENCE'
            
        times_caught = target_cop_data['times_caught']
        corruption = target_cop_data['corruption_score']
        
        # Logic from spec
        if times_caught >= 3 or corruption > 85:
            self.officers_fired += 1
            return 'FIRE'
        elif times_caught >= 2 or corruption > 70:
            return 'SUSPEND'
        else:
            return 'WARNING'

    def __repr__(self):
        return f"PoliceChief(#{self.agent_id}, Investigations:{self.investigations_ordered}, Fired:{self.officers_fired})"
