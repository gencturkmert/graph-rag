from llama import *

llm, tokenizer = get_llama_model()
if llm and tokenizer:
    print("Llama succesfully loaded")
else:
    print("error")