from router import classify_query
from pandas_agent import users, payments, subscriptions, sessions, ask_dataset

def handle_user_question(message_text: str) -> str:
    dataset_name = classify_query(message_text)

    if dataset_name == "users":
        return ask_dataset(users, message_text)

    if dataset_name == "payments":
        return ask_dataset(payments, message_text)

    if dataset_name == "subscriptions":
        return ask_dataset(subscriptions, message_text)

    if dataset_name == "sessions":
        return ask_dataset(sessions, message_text)

    return "Sorry, I’m not sure which data this relates to."
