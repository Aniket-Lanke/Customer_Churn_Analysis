import json, webbrowser
from pathlib import Path
BASE = Path(__file__).resolve().parent            # project folder (only read from)
OUT = Path.home() / "churn_project_output"          # results are written here (always writable)
OUT.mkdir(exist_ok=True)
d = json.load(open(OUT / "dashboard_data.json"))
html = r"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Customer churn dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;600;800&display=swap" rel="stylesheet">
<style>
:root{box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px);
--bg:#f4f6f9;--panel:#fff;--ink:#16213a;--mute:#66728a;--line:#dde3ec;--churn:#d62839;--keep:#2a8c82;--bar:#e9edf3}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#10172a;--panel:#18213a;--ink:#eaeefa;--mute:#98a4be;--line:#2a3555;--churn:#ff5c6c;--keep:#4fc4b8;--bar:#25304f}}
:root[data-theme="dark"]{--bg:#10172a;--panel:#18213a;--ink:#eaeefa;--mute:#98a4be;--line:#2a3555;--churn:#ff5c6c;--keep:#4fc4b8;--bar:#25304f}
html{scroll-padding-top:env(safe-area-inset-top,0px)}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:400 15px/1.5 "Public Sans",system-ui,sans-serif}
main{max-width:1080px;margin:0 auto;padding:28px 18px 48px}
h1{font-size:28px;font-weight:800;margin:0 0 4px;letter-spacing:-.02em}h2{font-size:16px;font-weight:600;margin:0 0 4px}
.sub{color:var(--mute);margin:0 0 22px;max-width:62ch}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-bottom:14px}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:14px 16px}
.kpi b{display:block;font-size:30px;font-weight:800;letter-spacing:-.02em}.kpi span{color:var(--mute);font-size:13px}
.kpi.hot b{color:var(--churn)}
.grid{display:grid;grid-template-columns:3fr 2fr;gap:12px}@media(max-width:800px){.grid{grid-template-columns:1fr}}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:16px 18px;margin-bottom:12px}
.note{color:var(--mute);font-size:13px;margin:0 0 12px}
.tabs{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0 14px}
.tabs button{font:inherit;font-size:13px;padding:5px 12px;border:1px solid var(--line);background:none;color:var(--ink);border-radius:20px;cursor:pointer}
.tabs button[aria-pressed=true]{background:var(--ink);color:var(--panel);border-color:var(--ink)}
button:focus-visible{outline:2px solid var(--churn);outline-offset:2px}
.row{display:grid;grid-template-columns:minmax(110px,170px) 1fr 54px;align-items:center;gap:10px;margin:8px 0;font-size:14px}
.track{height:18px;background:var(--bar);border-radius:3px;position:relative;overflow:hidden}
.fill{position:absolute;inset:0 auto 0 0;background:var(--churn);border-radius:3px}
.row small{display:block;color:var(--mute);font-size:12px}.row .v{font-weight:600;text-align:right}
.avg{position:absolute;top:-2px;bottom:-2px;width:2px;background:var(--ink)}
table{width:100%;border-collapse:collapse;font-size:14px}th,td{padding:7px 4px;text-align:right;border-bottom:1px solid var(--line)}th:first-child,td:first-child{text-align:left}th{font-weight:600;color:var(--mute);font-size:13px}
.cm{display:grid;grid-template-columns:auto 1fr 1fr;gap:4px;font-size:13px;margin-top:14px;text-align:center}
.cm div{padding:10px 4px;border-radius:4px}.cm .h{color:var(--mute);padding:4px}
.tn,.tp{background:color-mix(in srgb,var(--keep) 22%,transparent)}.fp,.fn{background:color-mix(in srgb,var(--churn) 20%,transparent)}
.cm b{display:block;font-size:20px}
</style></head><body><main>
<h1>Customer churn dashboard</h1>
<p class="sub">Telecom customer base, __N__ accounts. Churn rate by segment, the revenue that is leaving or about to, and the factors the model leans on.</p>
<section class="kpis">
<div class="kpi"><b>__RATE__%</b><span>Churn rate (__CHURNED__ of __N__ customers)</span></div>
<div class="kpi hot"><b>$__LOST__</b><span>Monthly revenue already lost</span></div>
<div class="kpi hot"><b>$__RISK__</b><span>Monthly revenue at risk (__HR__ active customers scored high risk)</span></div>
<div class="kpi"><b>__AUC__</b><span>Best model ROC-AUC (__BEST__)</span></div>
</section>
<div class="grid"><div>
<section class="panel"><h2>Churn rate by segment</h2>
<p class="note">Black tick marks the overall rate of __RATE__%.</p>
<div class="tabs" id="tabs" role="group" aria-label="Segment"></div><div id="bars"></div></section>
<section class="panel"><h2>Key churn drivers</h2>
<p class="note">Random Forest feature importance, share of total.</p><div id="drivers"></div></section>
</div><div>
<section class="panel"><h2>Model comparison</h2>
<p class="note">20% hold-out set, class weights balanced.</p>
<table id="models"></table>
<div class="cm" id="cm"></div>
<p class="note" style="margin-top:12px">Confusion matrix for <span id="cmname"></span>. Recall matters most here: a missed churner (false negative) costs more than an unneeded retention offer.</p></section>
</div></div>
<script>
const D=__DATA__;
const segs={Contract:D.contract,Tenure:D.tenure,Internet:D.internet,Payment:D.payment,Billing:D.billing};
const $=id=>document.getElementById(id);
function bars(k){const rows=segs[k],max=Math.max(...rows.map(r=>r.rate),D.churn_rate)*1.1;
 $('bars').innerHTML=rows.map(r=>`<div class="row"><div>${r.name}<small>${r.customers.toLocaleString()} customers</small></div>
 <div class="track"><div class="fill" style="width:${r.rate/max*100}%"></div><div class="avg" style="left:${D.churn_rate/max*100}%"></div></div><div class="v">${r.rate}%</div></div>`).join('');
 document.querySelectorAll('#tabs button').forEach(b=>b.setAttribute('aria-pressed',b.textContent===k));}
$('tabs').innerHTML=Object.keys(segs).map(k=>`<button>${k}</button>`).join('');
$('tabs').onclick=e=>{if(e.target.tagName==='BUTTON')bars(e.target.textContent)};bars('Contract');
const dm=Math.max(...D.drivers.map(x=>x.value));
$('drivers').innerHTML=D.drivers.slice(0,8).map(x=>`<div class="row"><div>${x.name.replace(/_/g,' ')}</div><div class="track"><div class="fill" style="width:${x.value/dm*100}%;background:var(--ink)"></div></div><div class="v">${x.value}%</div></div>`).join('');
const m=D.models,f=v=>(v*100).toFixed(1)+'%';
$('models').innerHTML='<tr><th></th>'+Object.keys(m).map(k=>`<th>${k}</th>`).join('')+'</tr>'+
 ['accuracy','precision','recall','f1','roc_auc'].map(q=>`<tr><td>${q.replace('_',' ')}</td>`+Object.keys(m).map(k=>`<td>${q==='roc_auc'?m[k][q].toFixed(3):f(m[k][q])}</td>`).join('')+'</tr>').join('');
const c=m[D.best_model].confusion;$('cmname').textContent=D.best_model;
$('cm').innerHTML=`<div class="h"></div><div class="h">Predicted stay</div><div class="h">Predicted churn</div>
<div class="h">Actual stay</div><div class="tn"><b>${c.tn}</b>true negative</div><div class="fp"><b>${c.fp}</b>false positive</div>
<div class="h">Actual churn</div><div class="fn"><b>${c.fn}</b>false negative</div><div class="tp"><b>${c.tp}</b>true positive</div>`;
</script></main></body></html>"""
rep = {"__DATA__": json.dumps(d), "__N__": f"{d['customers']:,}", "__RATE__": str(d["churn_rate"]),
       "__CHURNED__": f"{d['churned']:,}", "__LOST__": f"{d['monthly_revenue_lost']:,.0f}",
       "__RISK__": f"{d['revenue_at_risk']:,.0f}", "__HR__": f"{d['high_risk_customers']:,}",
       "__AUC__": f"{d['models'][d['best_model']]['roc_auc']:.3f}", "__BEST__": d["best_model"]}
for k, v in rep.items(): html = html.replace(k, v)
open(OUT / "churn_dashboard.html", "w", encoding="utf-8").write(html)
print("Dashboard saved:", OUT / "churn_dashboard.html")
webbrowser.open((OUT / "churn_dashboard.html").as_uri())
