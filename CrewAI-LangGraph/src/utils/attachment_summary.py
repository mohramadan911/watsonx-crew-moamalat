import fitz  # PyMuPDF
import re
# from langchain.chat_models import ChatOpenAI
from langchain_community.chat_models import ChatOpenAI

def summarize_attachments_with_gpt(file_paths):
    summaries = []
    all_links = []
    
    llm = ChatOpenAI(model="gpt-4", temperature=0.3)

    for path in file_paths:
        doc = fitz.open(path)
        text = "\n".join([page.get_text() for page in doc])
        doc.close()
        
        if len(text) > 5000:
            text = text[:5000]  # Trim to reduce tokens

        # Extract links
        links = re.findall(r'(https?://\S+)', text)
        all_links.extend(links)

        prompt = f"""Summarize the following document:\n{text}\n\nOnly include relevant points."""
        summary = llm.predict(prompt)
        summaries.append(f"📄 Summary for {os.path.basename(path)}:\n{summary}")

    # Analyze links
    link_review = []
    for link in all_links:
        reasoning = llm.predict(f"Is this link safe or suspicious? Provide a quick reason.\n\n{link}")
        link_review.append(f"{link} → {reasoning}")

    return "\n".join(summaries), "\n".join(link_review)
