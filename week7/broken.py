# broken.py — 마침표로 끝나지 않는 조각 = 문장 중간에서 잘린 조각
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

docs = TextLoader("long_notes.txt", encoding="utf-8").load()

def broken_endings(chunks):
    bad = [c for c in chunks if not c.page_content.rstrip().endswith(".")]
    return len(bad), bad[:2]

for size, overlap in [(100, 0), (100, 20), (300, 30), (500, 50)]:
    s = RecursiveCharacterTextSplitter(chunk_size=size, chunk_overlap=overlap)
    cs = s.split_documents(docs)
    n, samples = broken_endings(cs)
    print(f"size={size} overlap={overlap} → 문장 중간에서 끝난 조각 {n}/{len(cs)}개")
    for sm in samples:
        print("   ...", sm.page_content[-30:])
