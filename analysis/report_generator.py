# analysis/report_generator.py
import os, datetime
from typing import Dict, Any
from jinja2 import Template

TEMPLATE = """<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8"><title>qPCR v2.1 Report</title>
<style>body{font-family:sans-serif;margin:40px;line-height:1.6} table{width:100%;border-collapse:collapse;margin:10px 0}
th,td{border:1px solid #ccc;padding:8px;text-align:left} .pass{color:green;font-weight:bold}.fail{color:red}
</style></head><body>
<h1>🧬 qPCR İn Siliko Validasyon & Eğitim Raporu</h1>
<p><strong>Oturum:</strong> {{ id }} | <strong>Tarih:</strong> {{ date }} | <strong>Mod:</strong> v2.1 Digital Twin</p>
<h2>1. Parametreler</h2><table>{% for k,v in params.items() %}<tr><th>{{k}}</th><td>{{v}}</td></tr>{% endfor %}</table>
<h2>2. Performans & ISO 17025 Checklist</h2><table>{% for k,v in metrics.items() %}<tr><th>{{k}}</th><td class="{{ 'pass' if 'PASS' in v else 'fail' }}">{{v}}</td></tr>{% endfor %}</table>
<h2>3. Eğitim Notları</h2><ul>
<li><strong>MIQE Uyumu:</strong> Eğri simetrisi, baseline stabilitesi ve verimlilik otomatik skorlanır.</li>
<li><strong>LoD/LoQ:</strong> Poisson dağılımı ve teknik CV ile kantifikasyon limiti CLSI EP17-A2'ye göre belirlenir.</li>
<li><strong>Multiplex:</strong> LSQ dekonvolüsyon spektral çakışmayı matematiksel olarak ayırır.</li>
</ul>
<div style="margin-top:30px;border-top:1px solid #ccc;padding-top:10px;color:#666;font-size:0.9em">
⚠️ Bu rapor ön-validasyon ve eğitim amaçlıdır. Klinik/regülasyon kararları için ıslak laboratuvar validasyonu zorunludur.
</div></body></html>"""

class ReportGenerator:
    def __init__(self, output_dir: str = "./reports"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_html(self, session_id: str, params: Dict, metrics: Dict) -> str:
        tmpl = Template(TEMPLATE)
        html = tmpl.render(id=session_id, date=datetime.datetime.now().strftime("%Y-%m-%d"), params=params, metrics=metrics)
        path = os.path.join(self.output_dir, f"report_{session_id}.html")
        with open(path, 'w', encoding='utf-8') as f: f.write(html)
        return path

    def generate_pdf(self, html_path: str) -> str:
        pdf_path = html_path.replace('.html', '.pdf')
        try:
            import weasyprint
            weasyprint.HTML(html_path).write_pdf(pdf_path)
            return pdf_path
        except Exception as e:
            print(f"⚠️ WeasyPrint PDF hatası (Windows GTK eksik olabilir). HTML fallback kullanılıyor: {e}")
            return html_path  # Kullanıcı tarayıcıdan PDF'e çevirebilir