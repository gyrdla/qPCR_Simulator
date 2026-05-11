# ncbi/fetcher.py
import time
from typing import Optional, Dict
from Bio import Entrez, SeqIO
from io import StringIO

Entrez.email = "your_email@domain.com"  # ← NCBI politikası gereği zorunlu
Entrez.api_key = None

def fetch_sequence(accession: str, db: str = "nucleotide", rettype: str = "fasta") -> Optional[str]:
    try:
        with Entrez.efetch(db=db, id=accession, rettype=rettype, retmode="text") as handle:
            data = handle.read()
            if not data or "<!DOCTYPE" in data or "Error" in data:
                return None
            return data
    except Exception as e:
        print(f"[NCBI Fetch] Hata: {e}")
        return None

def parse_fasta(fasta_str: str) -> Dict[str, str]:
    if not fasta_str or not fasta_str.strip().startswith('>'):
        raise ValueError("Geçersiz veya boş FASTA verisi.")
    handle = StringIO(fasta_str)
    try:
        record = SeqIO.read(handle, "fasta")
        return {
            "id": record.id,
            "description": record.description,
            "sequence": str(record.seq).upper()
        }
    except Exception as e:
        raise ValueError(f"FASTA parse hatası: {e}")

def search_gene(query: str, db: str = "gene", max_results: int = 5) -> list:
    try:
        with Entrez.esearch(db=db, term=query, retmax=max_results) as handle:
            result = Entrez.read(handle)
        return result.get("IdList", [])
    except Exception as e:
        print(f"[NCBI Search] Hata: {e}")
        return []