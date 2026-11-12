# rag_source.py — 답 아래에 근거 문서를 붙입니다
from kb_corpus import records
from hybrid import hybrid_ids
from rag import chain

by_id = {str(r.id): r.payload for r in records}

def ask_with_source(question):
    docs = [by_id[i] for i in hybrid_ids(question)]
    context = "\n---\n".join(d["text"] for d in docs)
    answer = chain.invoke({"context": context, "question": question})
    srcs = sorted({d.get("source", "?") for d in docs})
    return answer + "\n\n[근거] " + ", ".join(srcs)

print(ask_with_source("ERR-4021 이 뜨면 무엇부터 확인해?"))
