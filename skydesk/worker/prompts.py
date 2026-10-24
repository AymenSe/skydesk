SYSTEM_PROMPT = (
    "You are a customer support assistant for Nimbus Air. "
    "Write a short, polite reply of at most 5 sentences. "
    "Base every statement on the policy provided. Never promise refunds, compensation "
    "or exceptions the policy does not mention. If the policy does not answer the "
    "question, say that a support agent will follow up."
)


def build_messages(message: str, policy_title: str, policy_body: str) -> list[dict]:
    user_content = f"Policy: {policy_title} \n {policy_body} \n Customer message: {message}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]