import re


def split_text(text: str, max_length: int = 250):
    """
    Divide o texto em chunks pequenos, preservando sentenças e pausas.
    """
    text = re.sub(r'[ \t]+', ' ', text).strip()
    
    # Divide em sentenças usando pontuação
    sentences = re.split(r'(?<=[.!?;:])\s+', text)
    
    chunks = []
    current = ""
    
    for s in sentences:
        if len(current) + len(s) + 1 <= max_length:
            current += (" " if current else "") + s
        else:
            chunks.append(current)
            current = s
    if current:
        chunks.append(current)
    
    return chunks
