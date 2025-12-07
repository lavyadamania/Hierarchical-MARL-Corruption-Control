import random
from config import (
    WITNESS_RISK_FACTOR, IA_RISK_MULTIPLIER, LOCATION_RISK_WEIGHT,
    CRIME_TYPES, SEVERITY_RISK_MULTIPLIER, VIOLENCE_SCALAR,
    ALERT_RISK_ADDITION
)

class GameWorld:
    def __init__(self):
        self.crime_names = list(CRIME_TYPES.keys())

    def generate_scenario(self):
        """
        Generates a detailed bribe scenario.
        Includes Asset Value, Criminal Wealth, and Context-Aware Bribes.
        """
        # Pick a crime
        crime_name = random.choice(self.crime_names)
        severity, base_val_min, base_val_max = CRIME_TYPES[crime_name]
        
        # 1. Asset/Context Value (What is at stake?)
        # For Theft: Value of item. For Murder: Value of getting away (Life).
        # We assume base_val in definition is now the "Stakes Value" not offer.
        # Actually, let's derive distinct Asset Value.
        
        asset_value = random.randint(base_val_min * 10, base_val_max * 10) 
        # Example: Traffic (Base 500) -> Asset (Car/License) ~ 5000 to 20000
        
        # 2. Criminal Profile
        criminal_wealth = random.choice(['poor', 'middle', 'rich'])
        wealth_factor = {'poor': 0.5, 'middle': 1.0, 'rich': 3.0}[criminal_wealth]
        
        # 3. Repeat Offender?
        criminal_history = random.choice(['first_timer', 'repeat_offender'])
        history_multiplier = 1.5 if criminal_history == 'repeat_offender' else 1.0
        
        # 4. Calculate Bribe Offer
        # Bribe is typically 10-30% of the trouble's cost/asset value
        bribe_percentage = random.uniform(0.1, 0.3)
        
        raw_offer = asset_value * bribe_percentage * wealth_factor * history_multiplier
        final_offer = int(raw_offer)
        
        return {
            'crime_type': crime_name,
            'severity': severity,
            'offer': final_offer,
            'asset_value': asset_value,
            'criminal_wealth': criminal_wealth,
            'witnesses': random.randint(0, 4),
            'ia_nearby': random.choice([True, False]),
            'location_risk': random.random()
        }

    def resolve_outcome(self, decision, state):
        """
        Determines the outcome of a cop's decision.
        """
        if decision == 'REJECT':
            # Violence Check: Rejection can lead to death
            # Severity 1 (Traffic) -> 3% chance
            # Severity 10 (Murder) -> 30% chance
            violence_prob = state['severity'] * VIOLENCE_SCALAR
            
            # Risk Multiplier for 'Rich/Desperate' criminals? 
            # Implied in severity usually, but let's keep it simple based on severity.
            
            if random.random() < violence_prob:
                return 'killed'
            return 'rejected'

        # Calculate detection probability
        # Base Risk + Severity Risk
        # High severity crimes attract more attention (Chief, Media, Public)
        
        severity_risk = state['severity'] * SEVERITY_RISK_MULTIPLIER
        
        # Global Alert Risk (Heat)
        # If alert_level is 1.0, we add full ALERT_RISK_ADDITION
        heat_risk = state.get('alert_level', 0.0) * ALERT_RISK_ADDITION

        detection_probability = (state['witnesses'] * WITNESS_RISK_FACTOR) + \
                                (IA_RISK_MULTIPLIER if state['ia_nearby'] else 0.0) + \
                                (state['location_risk'] * LOCATION_RISK_WEIGHT) + \
                                severity_risk + \
                                heat_risk
        
        # Cap prob at 1.0 (Certainty of getting caught for very high risk)
        detection_probability = min(1.0, detection_probability)
        
        if random.random() < detection_probability:
            return 'caught'
        else:
            return 'success'
