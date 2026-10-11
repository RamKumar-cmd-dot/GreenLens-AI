import React from 'react';
import {beforeEach,describe,expect,it,vi} from 'vitest';
import {fireEvent,render,screen,waitFor,within} from '@testing-library/react';
import App from '../src/App.jsx';

let memory;
const customer={customer_id:'C002056',data_timestamp:'2026-01-01',features:{region:'London',age_band:'30-44',monthly_income_gbp:3000,mean_monthly_fuel:150,electricity_kwh_year:4000,homeowner:1,vehicle_type:'petrol',digital_logins_month:18}};
const products=()=>['GP01','GP02','GP03','GP04'].map((product_id,index)=>{
 const action=memory[product_id];
 const state={explore:['EXPLORED',105],interested:['INTERESTED',120],dismiss:['DEPRIORITIZED',40],remind_later:['SNOOZED',10],not_interested:['SUPPRESSED',0],clear:['STANDARD',100]}[action]||['STANDARD',100];
 return {customer_id:customer.customer_id,product_id,product_name:['EV Finance','Green Home Loan','Solar Finance','Paperless Banking'][index],propensity:.76,threshold_screen:{threshold:.24,above_threshold:true},confidence:null,confidence_level:'medium',confidence_method:'validation-informed reliability assessment v1',status:'POTENTIAL_OPPORTUNITY',reason_codes:[],evidence:{},applicable_exclusions:[],impact:{impact_status:'UNAVAILABLE',reason:'No estimate',assumptions:[],limitations:[],factors:[]},reliability:{scope:'synthetic_validation_only',reason_codes:[],limitations:[]},recommended_action:'Explore with your relationship team.',data_timestamp:'2026-01-01',model_version:'test',presentation_status:state[0],presentation_priority:state[1],presentation_note:action==='not_interested'?'Suppressed by your preference.':action==='dismiss'?'Shown lower because you dismissed it.':action==='remind_later'?'Reminder set for later.':null,customer_memory:action?{action,reason:null,created_at:'2026-01-01T00:00:00Z',snooze_until:action==='remind_later'?'2099-01-01T09:00:00Z':null}:{}};
});

beforeEach(()=>{
 memory={};
 vi.stubGlobal('fetch',vi.fn(async(url,options={})=>{
  if(url.includes('/feedback')){
   if(options.method==='POST'){
    const body=JSON.parse(options.body);memory[body.product_id]=body.action;
    return {ok:true,json:async()=>({message:'Preference recorded.',recommendation:products().find(row=>row.product_id===body.product_id)})};
   }
   return {ok:true,json:async()=>({customer_id:customer.customer_id,total:0,offset:0,limit:50,items:[]})};
  }
  if(url.includes('/customers?'))return {ok:true,json:async()=>({total:1,items:[customer]})};
  if(url.includes('/transactions'))return {ok:true,json:async()=>({total:0,items:[]})};
  if(url.includes('/opportunities'))return {ok:true,json:async()=>({customer_id:customer.customer_id,opportunities:products()})};
  if(url.includes('/insights'))return {ok:true,json:async()=>({explanations:[],monthly_spending:[]})};
  return {ok:true,json:async()=>customer};
 }));
});

describe('Customer memory controls',()=>{
 it('deprioritizes a dismissed opportunity without changing propensity or screening',async()=>{
  render(<App/>);let card=await screen.findByTestId('product-GP01');
  expect(within(card).getByText('76')).toBeInTheDocument();
  fireEvent.click(within(card).getByRole('button',{name:'Dismiss EV Finance'}));
  card=await screen.findByText('deprioritized').then(node=>node.closest('[data-testid="product-GP01"]'));
  expect(within(card).getByText('76')).toBeInTheDocument();
  expect(within(card).getByText('potential opportunity')).toBeInTheDocument();
  expect(within(card).getByText(/shown lower because you dismissed/i)).toBeInTheDocument();
 });

 it('suppresses not-interested recommendations into a reversible section',async()=>{
  render(<App/>);const card=await screen.findByTestId('product-GP01');
  fireEvent.click(within(card).getByRole('button',{name:'Mark not interested in EV Finance'}));
  fireEvent.click(await screen.findByText('Paused by your feedback'));
  const suppressed=await screen.findByTestId('product-GP01');
  expect(within(suppressed).getByText('suppressed')).toBeInTheDocument();
  fireEvent.click(within(suppressed).getByRole('button',{name:'Undo EV Finance feedback'}));
  await waitFor(()=>expect(screen.queryByText('Paused by your feedback')).not.toBeInTheDocument());
  expect(await screen.findByTestId('product-GP01')).toBeInTheDocument();
 });

 it('records explore, interested and snooze preferences via the feedback endpoint',async()=>{
  render(<App/>);let card=await screen.findByTestId('product-GP01');
  fireEvent.click(within(card).getByRole('button',{name:'Explore EV Finance'}));
  expect(await screen.findByText('explored')).toBeInTheDocument();
  card=screen.getByTestId('product-GP01');
  fireEvent.click(within(card).getByRole('button',{name:'Mark interested in EV Finance'}));
  expect(await screen.findByText('interested')).toBeInTheDocument();
  card=screen.getByTestId('product-GP01');
  fireEvent.click(within(card).getByRole('button',{name:'Remind me later for EV Finance'}));
  expect(await screen.findByText('snoozed')).toBeInTheDocument();
  const calls=fetch.mock.calls.filter(([url,options])=>url.includes('/feedback')&&options?.method==='POST');
  expect(calls.map(([,options])=>JSON.parse(options.body).action)).toEqual(['explore','interested','remind_later']);
  expect(JSON.parse(calls[2][1].body).snooze_until).toMatch(/Z$/);
 });
});
