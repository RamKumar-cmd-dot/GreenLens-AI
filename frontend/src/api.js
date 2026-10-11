export async function api(path, signal){
  const response=await fetch(`${import.meta.env.VITE_API_BASE || '/api'}${path}`,{signal});
  if(!response.ok) throw new Error(response.status===503?'The data or models are unavailable. Check the backend startup log.':`Request failed (${response.status}). Please retry.`);
  return response.json();
}
export async function classify(transaction){
 const response=await fetch(`${import.meta.env.VITE_API_BASE || '/api'}/transactions/classify`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({merchant_name:transaction.merchant_name,merchant_description:transaction.merchant_description})});
 if(!response.ok)throw new Error(`Classification unavailable (${response.status}).`);
 return response.json();
}
export async function runScenario(customerId,selection,{signal}={}){
 const payload=Array.isArray(selection)?{apply:selection}:{changes:selection};
 const response=await fetch(`${import.meta.env.VITE_API_BASE || '/api'}/customers/${encodeURIComponent(customerId)}/scenario`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),signal});
 if(!response.ok)throw new Error(response.status===422?'Scenario inputs are invalid.':`Scenario unavailable (${response.status}).`);
 return response.json();
}
export async function saveFeedback(customerId,feedback){
 const response=await fetch(`${import.meta.env.VITE_API_BASE || '/api'}/customers/${encodeURIComponent(customerId)}/feedback`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(feedback)});
 if(!response.ok){let detail='Feedback could not be saved.';try{const body=await response.json();detail=body.detail||detail;}catch{}throw new Error(typeof detail==='string'?detail:`Feedback request failed (${response.status}).`);}
 return response.json();
}
