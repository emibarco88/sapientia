"use client";
import {useEffect,useState} from "react";
import {useParams} from "next/navigation";
const API=process.env.NEXT_PUBLIC_API_URL||"http://127.0.0.1:8000";
export default function Page(){
 const params=useParams<{domain:string}>(); const domain=String(params?.domain||"FINANCE").toUpperCase();
 const [items,setItems]=useState<any[]>([]); const [comparison,setComparison]=useState<any>(null); const [msg,setMsg]=useState("");
 useEffect(()=>{const t=localStorage.getItem("sapientia_token");fetch(`${API}/intelligence/assessments/domain/${domain}/timeline?project_id=1`,{headers:t?{Authorization:`Bearer ${t}`}:{}})
 .then(r=>r.ok?r.json():Promise.reject(r.statusText)).then(d=>setItems(d.timeline||[])).catch(e=>setMsg(String(e)))},[domain]);
 async function compare(){if(items.length<2)return;const t=localStorage.getItem("sapientia_token");
 const u=`${API}/intelligence/assessments/compare?previous_assessment_id=${items[1].assessment_id}&current_assessment_id=${items[0].assessment_id}&project_id=1`;
 const r=await fetch(u,{headers:t?{Authorization:`Bearer ${t}`}:{}});setComparison(await r.json());}
 return <main style={{padding:32,maxWidth:1200,margin:"0 auto"}}><a href={`/workspace/${domain}/intelligence`}>← Intelligence</a>
 <h1>{domain} Assessment History</h1><p>Track how Sapientia's enterprise intelligence changes over time.</p>
 {msg&&<p>{msg}</p>}<button disabled={items.length<2} onClick={compare}>Compare latest two versions</button>
 <div style={{display:"grid",gap:12,marginTop:24}}>{items.map(x=><section key={x.assessment_id} style={{border:"1px solid #ccc",borderRadius:12,padding:16}}>
 <b>Version {x.assessment_version}</b> · {x.assessment_status}<div>{x.assessment_title}</div>
 <small>{x.object_count} objects · {x.finding_count} findings · {x.risk_count} risks · {x.opportunity_count} opportunities</small>
 {x.assessment_comparison_id&&<div>+{x.new_object_count||0} new · {x.changed_object_count||0} changed · {x.resolved_object_count||0} resolved</div>}
 </section>)}</div>
 {comparison&&<section style={{border:"1px solid #ccc",borderRadius:12,padding:18,marginTop:24}}>
 <h2>Version {comparison.previous_version} → {comparison.current_version}</h2>
 <p>{comparison.new_object_count} new · {comparison.changed_object_count} changed · {comparison.resolved_object_count} resolved · {comparison.unchanged_object_count} unchanged</p>
 {(comparison.changes||[]).filter((x:any)=>x.change_type!=="UNCHANGED").map((x:any)=><div key={x.intelligence_object_change_id} style={{padding:"10px 0",borderTop:"1px solid #ddd"}}>
 <b>{x.change_type}: {x.title||x.object_key}</b><div>{x.change_summary}</div></div>)}
 </section>}</main>}
