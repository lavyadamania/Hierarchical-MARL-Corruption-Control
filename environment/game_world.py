import random
import config # CHANGED

class SimulationEnvironment:
    def __init__(self):
        self.crime_names = list(config.CRIME_TYPES.keys())

    def generate_scenario(self):
        """
        Generates a rich 10-dim RPG scenario.
        """
        crime_name = random.choice(self.crime_names)
        severity, base_val_min, base_val_max = config.CRIME_TYPES[crime_name]
        
        # 1. Asset Value
        asset_value = random.randint(base_val_min * 10, base_val_max * 10) 
        
        # 2. Criminal Profile & Weath
        criminal_class = random.choice(['poor', 'middle', 'rich'])
        # Wealth on 0-1000 scale
        if criminal_class == 'poor': suspect_wealth_value = random.randint(10, 100)
        elif criminal_class == 'middle': suspect_wealth_value = random.randint(100, 500)
        else: suspect_wealth_value = random.randint(500, 1000)
        
        # 3. Bribe Offer Logic (User Requested)
        if severity <= 3:
            raw_offer = 0.10 * asset_value
        elif severity <= 7:
            raw_offer = max(0.30 * asset_value, 0.30 * suspect_wealth_value)
        else:
            raw_offer = 0.50 * suspect_wealth_value

        final_offer = int(raw_offer)
        
        # 4. RPG Features
        return {
            'crime_type': crime_name,
            'severity': severity,
            'offer': final_offer,
            'witnesses': random.randint(0, 4),
            'ia_nearby': random.choice([True, False]),
            'alert_level': 0.0, 
            'evidence_strength': random.uniform(0.1, 1.0),
            'has_warrant': random.choice([True, False]) if severity > 5 else False,
            'gang_affiliated': random.choice([True, False]),
            'seized_value': random.randint(100, 1000) if random.random() < 0.3 else 0,
            'suspect_aggression': random.uniform(0.1, 1.0) if severity > 6 else 0.1,
            'location_risk': random.random()
        }

    def resolve_outcome(self, decision, state):
        """
        RPG Logic for 15 Actions.
        Returns: String Outcome
        """
        risk = 0.0
        
        # --- HONEST ACTIONS ---
        if decision == 'ARREST':
            # Needs Evidence OR Warrant
            if state['has_warrant'] or state['evidence_strength'] > 0.6:
                return 'arrest_success'
            return 'arrest_failed' if random.random() < 0.5 else 'arrest_success'
            
        if decision == 'INVESTIGATE':
            return 'investigate_success' 
            
        if decision == 'DE_ESCALATE':
            if state['suspect_aggression'] > 0.8:
                return 'severe_injury' if random.random() < 0.2 else 'de_escalate_failed'
            return 'de_escalate_success'
            
        if decision == 'ISSUE_TICKET':
            if state['severity'] > 3: return 'ticket_invalid' 
            return 'ticket_success'
            
        if decision == 'REPORT_BRIBE':
            if state['gang_affiliated'] and random.random() < 0.3:
                return 'severe_injury' 
            return 'report_success'

        if decision == 'REQUEST_WARRANT':
            return 'warrant_success'
            
        if decision == 'WHISTLEBLOW':
            return 'severe_injury' if random.random() < 0.6 else 'whistleblow_success'

        # --- CORRUPT ACTIONS ---
        if decision == 'ACCEPT_BRIBE':
            risk = (state['witnesses'] * config.WITNESS_RISK_FACTOR) + (0.5 if state['ia_nearby'] else 0)
            return 'caught' if random.random() < risk else 'success'
            
        if decision == 'EXTORT':
            risk = 0.3 + (0.5 if state['ia_nearby'] else 0)
            return 'caught' if random.random() < risk else 'extortion_success'
            
        if decision == 'PLANT_EVIDENCE': # Frame
            if state['witnesses'] > 0 or state['ia_nearby']:
                return 'caught' 
            return 'frame_success'
            
        if decision == 'TIP_OFF':
            if not state['gang_affiliated']: return 'tip_off_useless'
            return 'caught' if state['ia_nearby'] else 'tip_off_success'
            
        if decision == 'DESTROY_EVIDENCE':
            if state['ia_nearby']: return 'caught'
            return 'destroy_success'
            
        if decision == 'INTIMIDATE_WITNESS':
            if state['witnesses'] == 0: return 'intimidate_useless'
            return 'caught' if state['ia_nearby'] else 'intimidate_success'
            
        if decision == 'STEAL_SEIZED':
            if state['seized_value'] == 0: return 'steal_useless'
            risk = 0.1 if not state['ia_nearby'] else 0.9
            return 'caught' if random.random() < risk else 'steal_success'
            
        if decision == 'EXCESSIVE_FORCE':
            return 'caught' if (state['witnesses'] > 0 or state['ia_nearby']) else 'brutality_success'

        if decision == 'ISOLATE_SUSPECT':
            if state['witnesses'] == 0:
                return 'isolate_useless' 
            
            # Application of the Maneuver
            state['witnesses'] = 0 # The "Gully" Effect
            state['suspect_aggression'] = min(1.0, state['suspect_aggression'] + 0.3) 
            return 'isolate_success'        


        # Default / Fallback
        return 'investigate_success'
