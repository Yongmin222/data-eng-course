# rag_env.py — 이번 주 실습 파일이 모두 불러 쓰는 모델 설정 한 곳(7-1 에서 만들고 7-5 까지 그대로 씁니다)
import os
from dotenv import load_dotenv

load_dotenv()   # 같은 폴더의 .env 를 읽습니다(OpenAI 키를 쓰는 사람만 만듭니다)

# OpenAI 키가 있으면 OpenAI, 없으면 로컬 Ollama. 키가 있어도 Ollama 로 하려면 .env 에 LLM_PROVIDER=ollama
PROVIDER = os.getenv("LLM_PROVIDER") or ("openai" if os.getenv("OPENAI_API_KEY") else "ollama")

def get_llm(temperature=0):
    if PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model="gpt-4o-mini", temperature=temperature)
    from langchain_ollama import ChatOllama
    return ChatOllama(model="llama3.2", temperature=temperature)

def get_emb():   # 7-3 부터 씁니다
    if PROVIDER == "openai":
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model="text-embedding-3-small")   # 1536차원
    from langchain_ollama import OllamaEmbeddings
    return OllamaEmbeddings(model="embeddinggemma")            # 768차원

llm = get_llm()

if __name__ == "__main__":
    print("PROVIDER =", PROVIDER)
    print("모델 =", getattr(llm, "model_name", None) or llm.model)
