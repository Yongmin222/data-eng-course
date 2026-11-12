# params.py — chunk_size · chunk_overlap 다섯 조합
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

docs = TextLoader("long_notes.txt", encoding="utf-8").load()

for size, overlap in [(100, 0), (100, 20), (300, 30), (500, 50), (1000, 100)]:
    s = RecursiveCharacterTextSplitter(chunk_size=size, chunk_overlap=overlap)
    cs = s.split_documents(docs)
    lengths = [len(c.page_content) for c in cs]
    print(f"size={size:5} overlap={overlap:4} → 조각 {len(cs):3}개, "
          f"평균 {sum(lengths)//max(len(lengths),1):5}자, 최대 {max(lengths):5}자")
