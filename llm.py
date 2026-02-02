from langchain.chat_models import init_chat_model

llm = init_chat_model(
    model_provider='openai',
    model="model",
    api_key='None',
    temperature=0,
    top_p=0.2,
)

