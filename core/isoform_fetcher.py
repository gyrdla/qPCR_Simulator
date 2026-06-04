# core/isoform_fetcher.py
import urllib.request, json, re, os, time
from typing import Dict, Optional

class IsoformFetcher:
    def __init__(self, cache_dir: str = "./data/ncbi_cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def fetch_transcripts(self, accession: str) -> Dict[str, str]:
        """NCBI E-Utilities ile gen/transkript sekanslarını çeker. Önbellek destekli."""
        acc = accession.strip()
        cache_path = os.path.join(self.cache_dir, f"{acc.replace('.','_')}_isoforms.json")
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        try:
            # 1. NCBI ESummary ile RefSeq transkript listesi
            url_sum = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=nuccore&id={acc}&retmode=json"
            with urllib.request.urlopen(url_sum, timeout=10) as resp:
                summary = json.loads(resp.read().decode())
            if "result" not in summary:
                raise ValueError("Geçersiz Accession veya NCBI yanıtı alınamadı.")
            
            # 2. EFetch ile FASTA çekimi (Sadece NM_ ve NR_ reftranskriptleri)
            url_fetch = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id={acc}&rettype=fasta&retmode=text"
            with urllib.request.urlopen(url_fetch, timeout=15) as resp:
                fasta_text = resp.read().decode('utf-8')

            transcripts = self._parse_fasta_to_dict(fasta_text)
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(transcripts, f, indent=2)
            return transcripts
        except Exception as e:
            raise ConnectionError(f"NCBI API hatası: {str(e)}")

    def _parse_fasta_to_dict(self, text: str) -> Dict[str, str]:
        """FASTA metnini {id: seq} sözlüğüne çevirir."""
        trans = {}
        current_id, current_seq = "", []
        for line in text.splitlines():
            line = line.strip()
            if line.startswith('>'):
                if current_id:
                    trans[current_id] = "".join(current_seq).upper()
                m = re.match(r">(\S+)", line)
                current_id = m.group(1) if m else line
                current_seq = []
            else:
                current_seq.append(line)
        if current_id:
            trans[current_id] = "".join(current_seq).upper()
        return trans