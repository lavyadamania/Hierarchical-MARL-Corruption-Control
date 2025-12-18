
import random

def generate_narrative(agent_name, state, action, outcome):
    """
    Generates a dynamic 2-line story based on the event.
    """
    crime = state['crime_type'].replace('_', ' ')
    
    # Context String
    context = ""
    if state['gang_affiliated']: context = "Gang Member"
    elif state['severity'] > 8: context = "Psychopath Killer"
    elif state['severity'] < 3: context = "Regular Civilian"
    else: context = "Criminal"

    intro = f"{agent_name} encountered a {context} ({crime})."
    
    # Middle & Ending
    if action == 'ARREST':
        if outcome == 'arrest_success':
            return f"👮 {intro} He slapped the cuffs on immediately! Law & Order served.", "✅ Suspect Jailed."
        else:
            return f"👮 {intro} He tried to arrest him, but the evidence was weak.", "❌ Lawyer got him released."

    if action == 'INVESTIGATE':
        return f"🔍 {intro} He decided to dig deeper and gather clues.", "✅ Case file updated."

    if action == 'DE_ESCALATE':
        if outcome == 'de_escalate_success':
            return f"🗣️ {intro} Officer calmed the situation down with words.", "✅ Peace restored."
        return f"🗣️ {intro} Negotiation failed! Suspect pulled a gun.", "💀 SHOTS FIRED."

    if action == 'ISSUE_TICKET':
        if outcome == 'ticket_success':
            return f"📝 {intro} He wrote a swift challan for ₹{state['offer']//10}.", "✅ Quota +1."
        return f"📝 {intro} Tried to ticket a MURDERER?!", "❌ This requires a real arrest, idiot."

    if action == 'REPORT_BRIBE':
        if outcome == 'report_success':
            return f"🛡️ {intro} Suspect offered ₹{state['offer']}. Officer recorded it and booked him for bribery.", "🌟 Integrity +++."
        return f"🛡️ {intro} He tried to report the Gang Boss...", "💀 Gang assassins silenced him."

    if action == 'WHISTLEBLOW':
        if outcome == 'whistleblow_success':
            return f"📢 {intro} Officer leaked department corruption to the Media!", "🌟 BREAKING NEWS: Hero Cop Exposes Truth!"
        return f"📢 {intro} He tried to expose the Chief...", "💀 Found dead in a ditch."

    if action == 'ACCEPT_BRIBE':
        if outcome == 'success':
            return f"🤝 {intro} Suspect offered ₹{state['offer']}. Officer looked left, looked right... took it.", "🤑 Wallet +₹{state['offer']}."
        return f"🤝 {intro} He took the cash, but IA was watching through binoculars!", "🚨 BUSTED! Suspended."

    if action == 'EXTORT':
        if outcome == 'extortion_success':
            return f"🔫 {intro} Officer demanded: 'Give me ₹5000 or die'.", "🤑 Innocent victim paid up out of fear."
        return f"🔫 {intro} Tried to extort a civilian...", "🚨 Recorded on viral video! IA notified."

    if action == 'PLANT_EVIDENCE':
        if outcome == 'frame_success':
            return f"😈 {intro} He slipped a packet of drugs into the suspect's pocket.", "✅ 'Found' evidence. Arrest made."
        return f"😈 {intro} Trying to plant evidence...", "🚨 Witnesses saw it! Caught red-handed."

    if action == 'TIP_OFF':
        if outcome == 'tip_off_success':
            return f"📱 {intro} Called the Gang Boss: 'Raid incoming, clear out'.", "🤑 Received 'Consulting Fee'."
        return f"📱 {intro} Tipped off the gang...", "🚨 Phone was tapped by IA!"

    if action == 'DESTROY_EVIDENCE':
        if outcome == 'destroy_success':
            return f"🗑️ {intro} Officer 'accidentally' deleted the CCTV footage.", "🤑 Case dismissed. Bribe received."
        return f"🗑️ {intro} Smashing the hard drive...", "🚨 IA walked in the room."

    if action == 'STEAL_SEIZED':
        if outcome == 'steal_success':
            return f"💰 {intro} Found ₹{state['seized_value']} in cash. Stuffed it in his socks.", "🤑 'Evidence Lost in Transit'."
        return f"💰 {intro} Stealing from the evidence locker...", "🚨 Security camera caught him."

    return f"ℹ️ {intro} Officer analyzed the situation but chose inaction.", "❌ No Significant Event."
