async function fetchJSON(url){
  const res=await fetch(url,{credentials:'same-origin'});
  if(!res.ok) throw new Error('HTTP '+res.status);
  return res.json();
}
function pick(o,...names){
  for(const n of names){
    if(o[n]!=null) return o[n];
  }
  return null;
}
const palette=['#FF6384','#36A2EB','#FFCE56','#4BC0C0','#9966FF'];
document.addEventListener('DOMContentLoaded',()=>{
  loadApplicationStatus();
  loadDeferredOffers();
  loadAgentPerformance();
  loadStudentClassification();
});
async function loadApplicationStatus(){
  try{
    const rows=await fetchJSON('/api/application-status');
    const labels=rows.map(r=>pick(r,'status','Status'));
    const data=rows.map(r=>Number(pick(r,'total','Total'))||0);
    new Chart(document.getElementById('applicationStatusChart'),{
      type:'bar',
      data:{labels,datasets:[{label:'Applications',backgroundColor:palette.slice(0,labels.length),data}]},
      options:{responsive:true}
    });
  }catch(e){console.error('application status',e);}
}
async function loadDeferredOffers(){
  try{
    const rows=await fetchJSON('/api/deferred-offers');
    const labels=rows.map(r=>pick(r,'term','Term'));
    const defers=rows.map(r=>Number(pick(r,'deferred_count','Deferred Count','Deferred_Count'))||0);
    const totals=rows.map(r=>Number(pick(r,'total_offers','Total Offers','Total_Offers'))||0);
    new Chart(document.getElementById('deferredOffersChart'),{
      type:'bar',
      data:{
        labels,
        datasets:[
          {label:'Deferred',backgroundColor:palette[0],data:defers},
          {label:'Total offers',backgroundColor:palette[1],data:totals}
        ]
      },
      options:{responsive:true}
    });
  }catch(e){console.error('deferred offers',e);}
}
async function loadAgentPerformance(){
  try{
    const rows=await fetchJSON('/api/agent-performance');
    const labels=rows.map(r=>pick(r,'agent','Agent'));
    const apps=rows.map(r=>Number(pick(r,'applications','Applications'))||0);
    const offers=rows.map(r=>Number(pick(r,'offers','Offers'))||0);
    const enrolled=rows.map(r=>Number(pick(r,'enrolled','Enrolled'))||0);
    new Chart(document.getElementById('agentPerformanceChart'),{
      type:'bar',
      data:{
        labels,
        datasets:[
          {label:'Applications',backgroundColor:palette[0],data:apps},
          {label:'Offers',backgroundColor:palette[1],data:offers},
          {label:'Enrolled',backgroundColor:palette[2],data:enrolled}
        ]
      },
      options:{responsive:true,plugins:{legend:{position:'top'}}}
    });
  }catch(e){console.error('agent performance',e);}
}
async function loadStudentClassification(){
  try{
    const rows=await fetchJSON('/api/student-classification');
    const labels=rows.map(r=>pick(r,'classification','Classification'));
    const data=rows.map(r=>Number(pick(r,'total','Total'))||0);
    new Chart(document.getElementById('studentClassificationChart'),{
      type:'doughnut',
      data:{
        labels,
        datasets:[{
          backgroundColor:palette.slice(0,labels.length),
          borderColor:'#F4F1DE',
          borderWidth:2,
          hoverOffset:8,
          data
        }]
      },
      options:{responsive:true}
    });
  }catch(e){console.error('student classification',e);}
}
