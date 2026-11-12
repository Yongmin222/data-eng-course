# rag.py — 찾은 조각만 근거로 답하게 합니다
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from hybrid import hybrid_search
from rag_env import llm

prompt = ChatPromptTemplate.from_messages([
    ("system",
     "아래 컨텍스트만 근거로 한국어로 짧게 답해줘. 컨텍스트에 없는 내용이면 모른다고 답해줘.\n\n[컨텍스트]\n{context}"),
    ("human", "{question}"),
])
chain = prompt | llm | StrOutputParser()

def ask(question):
    context = "\n---\n".join(hybrid_search(question))
    return chain.invoke({"context": context, "question": question})

if __name__ == "__main__":
    print(ask("작업 순서를 관리하는 도구가 뭐야?"))
    print("---")
    print(ask("김치찌개 끓이는 법 알려줘"))   # 지식베이스 밖 질문
