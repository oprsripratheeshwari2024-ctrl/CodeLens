const sv=x=>`<div class=row><b class=e>${x.sev}</b> Line ${x.line}: ${esc(x.msg)}<br><small>${esc(x.why||"")}</small></div>`,ln=x=>`<div class=row>Line ${x.line}: ${esc(x.msg)}</div>`;
Object.assign(P,{
Errors:()=>R?list(R.errors,x=>`<div class=row><b class="${x.sev=="error"?"e":"w"}">Line ${x.line}</b> ${esc(x.msg)}<br><small>💡 ${esc(x.why||"")}</small></div>`)+(R.heuristic?"<p><i>Non-Python analysis is heuristic.</i></p>":""):N,
Security:()=>R?list(R.security,sv):N,
Complexity:()=>R?`<div class=big>${R.score}/100</div><p>Quality score</p><p>Cyclomatic complexity: <b>${R.complexity.cc}</b> (${R.complexity.level})<br>Max nesting: <b>${R.complexity.nesting}</b><br>Estimated time: <b>${R.complexity.bigo}</b></p><h2>Per function (Python)</h2>${list(R.funcs,f=>`<div class=row>${esc(f.name)} (line ${f.line}): complexity <b>${f.cc}</b>, ${f.lines} lines</div>`)}`:N,
Smells:()=>R?`<h2>Code smells</h2>${list(R.smells,ln)}<h2>Dead code / unused imports</h2>${list(R.dead,ln)}<h2>Performance tips</h2>${list(R.perf,ln)}`:N,
Pseudocode:()=>R?`<pre>${esc(R.pseudo)}</pre>`:N,
Concepts:()=>R?(R.concepts.map(c=>`<span class=row style="margin:4px;padding:6px 12px;border:1px solid var(--gold);border-radius:20px;display:inline-block">${c}</span>`).join("")||"None"):N,
Quiz:()=>R?R.quiz.map((q,i)=>`<div class=row><b>${i+1}. ${esc(q.q)}</b><br>${q.opts.map((o,j)=>`<button onclick="this.style.background='${j==q.ans?"#2f7d4f":"#b3261e"}';this.style.color='#fff'">${esc(o)}</button> `).join("")}</div>`).join(""):N,
"AI Tools":()=>'<select id=at><option value=ask>Ask about code<option value=docstring>Docstrings/comments<option value=tests>Unit tests<option value=readme>README</select> <input id=aq placeholder="Your question (for Ask)" style="width:45%"> <button class=pri onclick=aitool()>Run</button><pre id=o></pre>',
Dashboard:()=>{setTimeout(dash);return '<canvas id=c1 height=80></canvas><canvas id=c2 height=80></canvas><canvas id=c3 height=80></canvas>'},
History:()=>{setTimeout(hist);return '<input id=q placeholder="Search history" oninput=hist()> <label><input type=checkbox id=fv onchange=hist()> ★ saved only</label> <button onclick=cmp()>Compare 2 selected</button><div id=cmpo></div><div id=h></div>'}});
async function aitool(){try{const j=await api("ai",{...body(),to:$("#at").value,b:$("#aq").value});$("#o").textContent=j.code||j.note}catch(e){$("#o").textContent=e.message}}
async function dash(){if(!window.Chart)return $("#view").insertAdjacentHTML("beforeend","<p>Charts need internet (Chart.js CDN).</p>");const s=await api("stats",null,"GET"),mk=(id,t,l,d)=>new Chart($(id),{type:t,data:{labels:l,datasets:[{label:t=="line"?"Score trend":id=="#c2"?"Analyses per language":"Common error types",data:d,backgroundColor:"#b8892b",borderColor:"#b8892b"}]}});
mk("#c1","line",s.trend.map((_,i)=>i+1),s.trend);mk("#c2","bar",Object.keys(s.langs),Object.values(s.langs));mk("#c3","bar",Object.keys(s.errors),Object.values(s.errors))}
hist=async function(){const h=await api("history?q="+encodeURIComponent($("#q")?.value||"")+($("#fv")?.checked?"&fav=1":""),null,"GET");$("#h").innerHTML=list(h,x=>`<div class=row><input type=checkbox class=ck value=${x.id}> <a href=# onclick="favt(${x.id});return false">${x.fav?"★":"☆"}</a> <b>${x.lang}</b> · score ${x.score} · ${x.ts} <a href=# onclick="$('#code').value=${esc(JSON.stringify(x.code)).replace(/"/g,"&quot;")};return false">load</a></div>`)};
async function favt(i){await api("fav/"+i,{});hist()}
async function cmp(){const c=[...document.querySelectorAll(".ck:checked")].map(x=>x.value);if(c.length!=2)return $("#cmpo").textContent="Select exactly 2 entries";const j=await api(`compare?a=${c[0]}&b=${c[1]}`,null,"GET");$("#cmpo").innerHTML=`<p>Score A: <b>${j.a}</b> → B: <b>${j.b}</b> (${j.b-j.a>=0?"+":""}${j.b-j.a})</p><pre>${j.diff.map(l=>`<div class="${l[0]=="+"?"add":l[0]=="-"?"del":""}">${esc(l)}</div>`).join("")}</pre>`}
const dl=(n,t)=>{const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([t]));a.download=n;a.click()};
$("#xm").onclick=()=>R&&dl("codelens-report.md",`# CodeLens Report\nScore: ${R.score}/100 | Complexity: ${R.complexity.cc} (${R.complexity.bigo})\n\n## Errors\n`+R.errors.map(e=>`- Line ${e.line}: ${e.msg}`).join("\n")+"\n\n## Security\n"+R.security.map(e=>`- Line ${e.line}: ${e.msg} (${e.sev})`).join("\n")+"\n\n## Pseudocode\n\n"+R.pseudo);
$("#xj").onclick=()=>R&&dl("codelens-report.json",JSON.stringify(R,null,2));
const ta=$("#code"),gut=$("#gut");ta.onscroll=()=>gut.scrollTop=ta.scrollTop;
setInterval(()=>{const bad=R?R.errors.map(e=>e.line):[];gut.innerHTML=ta.value.split("\n").map((_,i)=>`<div class="${bad.includes(i+1)?"bad":""}">${i+1}</div>`).join("")},500);
addEventListener("keydown",e=>{if(e.ctrlKey&&e.key=="Enter")$("#run").click()});
if(T)draw();
