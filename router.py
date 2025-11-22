from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def classify_query(text: str) -> str:
    """
    Classify the question into one of:
    users, payments, subscriptions, sessions, unknown
    """
    prompt = f"""
    Classify this question into one of the following categories:
    - users
    - payments
    - subscriptions
    - sessions
    - unknown

    Question: "{text}"

    Respond with only the category name.
    """

    resp = llm.invoke(prompt)
    return resp.content.strip().lower()