"""Create browser evidence views from raw logs and result files; no invented output."""
from pathlib import Path
import csv, html, json
root = Path(__file__).resolve().parent
results=root/'results'
style='''body{margin:0;background:#edf2f7;color:#172033;font:16px Arial,sans-serif}main{max-width:1100px;margin:28px auto;padding:30px;background:white;border-radius:16px}h1{font-size:30px;margin:10px 0}h2{font-size:21px}.tag{color:#007c71;font-weight:bold;letter-spacing:2px;font-size:12px}p{line-height:1.5;color:#475569}pre{background:#101b2d;color:#dbf6e9;padding:24px;border-radius:10px;font:13px/1.6 monospace;white-space:pre-wrap;overflow-wrap:anywhere}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:10px;text-align:left;border-bottom:1px solid #ddd}th{background:#f1f5f9}.cards{display:flex;gap:18px}.card{flex:1;background:#f1f5f9;padding:20px;border-radius:10px}.number{font-size:32px;font-weight:bold;color:#007c71}img{width:100%}footer{margin-top:20px;font-size:12px;color:#64748b}'''
meta=json.loads((results/'metadata.json').read_text())
def page(name,title,body):
    (root/(name+'.html')).write_text('<!doctype html><html><head><meta charset="utf-8"><title>'+title+'</title><style>'+style+'</style></head><body><main><div class="tag">SECURITY-AWARE EDGE–CLOUD SCHEDULER</div><h1>'+title+'</h1>'+body+'<footer>Execution evidence · Python simulation; no real cloud deployment.</footer></main></body></html>')
for name,title in [('tests','Automated test results'),('execution','Full experiment execution')]:
    page(name,title,'<p>Browser view of captured process output. The unedited raw log is included as '+name+'.txt.</p><pre>'+html.escape((root/(name+'.txt')).read_text())+'</pre>')
rows=list(csv.DictReader((results/'runs.csv').open()))
audit=list(csv.DictReader((results/'audit.csv').open()))
violations=[r for r in audit if r['sensitive']=='True' and r['destination']=='cloud']
sensitive=[r for r in audit if r['sensitive']=='True']
summary={'scheduler_runs':len(rows),'task_assignments':len(audit),'sensitive_assignments':len(sensitive),'sensitive_to_cloud':len(violations)}
(root/'audit_verification.json').write_text(json.dumps(summary,indent=2))
cards='<div class="cards">'+''.join('<div class="card"><div class="number">'+str(v)+'</div>'+k.replace('_',' ')+'</div>' for k,v in summary.items())+'</div>'
sample=[r for r in audit if r['scheduler']=='pso' and r['task_count']=='20' and r['sensitive_fraction']=='0.3' and r['seed']=='0' and r['sensitive']=='True']
headers=['task_id','sensitive','destination','completion_s','policy_violation']
table='<table><tr>'+''.join('<th>'+h+'</th>' for h in headers)+'</tr>'+''.join('<tr>'+''.join('<td>'+html.escape(r[h])+'</td>' for h in headers)+'</tr>' for r in sample)+'</table>'
page('security','Sensitive-data placement audit',cards+'<h2>Sample: PSO · 20 tasks · 30% sensitive · seed 0</h2>'+table+'<p>Independent CSV check: count every sensitive task placed on cloud. The full audit.csv contains all assignments. This proves compliance with the simulation policy, not security of a deployed system.</p>')
page('comparison','Scheduler comparison','<p>Actual experiment output. Task completion times are simulated; error bars show variation across 10 seeds.</p><img src="results/comparison.svg" alt="Scheduler performance chart">')
page('sensitivity','Effect of sensitive-data restrictions','<p>Actual experiment output for 20 tasks. Higher sensitivity restricts more placements to local nodes.</p><img src="results/sensitivity.svg" alt="Sensitivity chart">')
