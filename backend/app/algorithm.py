import heapq

def simplify_debts(expenses, members):
    # Sabka net balance 0 set karo
    balances = {member.id: 0.0 for member in members}

    # Calculate karo kisne kitna diya aur kiske upar udhari hai
    for exp in expenses:
        balances[exp.paid_by_id] += exp.amount
        for split in exp.splits:
            balances[split.user_id] -= split.amount_owed

    debtors = []   # Jinko paise dene hain (-)
    creditors = [] # Jinko paise lene hain (+)

    for u_id, bal in balances.items():
        if bal < -0.01:
            heapq.heappush(debtors, (bal, u_id))
        elif bal > 0.01:
            heapq.heappush(creditors, (-bal, u_id))

    transactions = []

    # Owdhari khatam karne ka loop
    while debtors and creditors:
        deb_bal, deb_id = heapq.heappop(debtors)
        cred_bal, cred_id = heapq.heappop(creditors)
        cred_bal = -cred_bal

        settle_amt = min(-deb_bal, cred_bal)
        settle_amt = round(settle_amt, 2)

        if settle_amt > 0:
            transactions.append({
                "from_user_id": deb_id,
                "to_user_id": cred_id,
                "amount": settle_amt
            })

        new_deb_bal = deb_bal + settle_amt
        new_cred_bal = cred_bal - settle_amt

        if new_deb_bal < -0.01:
            heapq.heappush(debtors, (new_deb_bal, deb_id))
        if new_cred_bal > 0.01:
            heapq.heappush(creditors, (-new_cred_bal, cred_id))

    return transactions