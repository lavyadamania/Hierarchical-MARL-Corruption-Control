class HonestCop:
    def __init__(self, agent_id, name, integrity_score):
        self.agent_id = agent_id
        self.name = name
        self.cop_type = 'honest'
        self.rank = 'constable'
        self.personality = 'none' # Honest cops don't have the risk personalities
        self.corruption_score = 0.0 # Meaningless for honest, but keeping schema consistent
        self.integrity_score = integrity_score # 80-100
        
        self.reports_filed = 0
        self.bribes_rejected = 0

    def decide_bribe(self, state):
        """Always rejects bribes."""
        self.bribes_rejected += 1
        return 'REJECT'

    def witness_corruption(self):
        """Logic for witnessing and reporting."""
        # Simple logic: Always reports if they see something
        self.reports_filed += 1
        return True

    def __repr__(self):
        return f"HonestCop(#{self.agent_id}, I:{self.integrity_score}, Reports:{self.reports_filed})"
