import React from 'react';
import {beforeEach,describe,expect,it,vi} from 'vitest';
import {fireEvent,render,screen,waitFor} from '@testing-library/react';
import App from '../src/App.jsx';

const profile=id=>({customer_id:id,data_timestamp:'2026-01-01',features:{region:'London',age_band:'30-44',monthly_income_gbp:3000,mean_monthly_fuel:150,electricity_kwh_year:4000,homeowner:1,vehicle_type:'petrol',digital_logins_month:18}});
const result=(id,apply=[])=>({customer_id:id,synthetic:true,applied_chips:apply,scenario_changes:{},changed_attributes:{},original_attributes:{},chip_notes:[],disclaimers:['Synthetic hypothetical scenario.'],comparisons:['GP01','GP02','GP03','GP04'].map(product_id=>({product_id,product_name:'Product '+product_id,baseline:{propensity:.4,status:'POTENTIAL_OPPORTUNITY',confidence_level:'medium',reason_codes:[],evidence:{},impact:{impact_status:'UNAVAILABLE',reason:'No supported impact'}},scenario:{propensity:.45,status:'POTENTIAL_OPPORTUNITY',confidence_level:'medium',reason_codes:[],evidence:{},impact:{impact_status:'UNAVAILABLE',reason:'No supported impact'}}})),opportunities:[]});
const ok=data=>({ok:true,json:async()=>data});

beforeEach(()=>{
 vi.stubGlobal('fetch',vi.fn(async(url,options={})=>{
  if(url.includes('/scenario'))return ok(result('C002056',JSON.parse(options.body||'{}').apply||[]));
  if(url.includes('/customers?'))return ok({total:2,items:[profile('C002056'),profile('C000018')]});
  if(url.includes('/opportunities'))return ok({customer_id:'C002056',opportunities:[]});
  if(url.includes('/insights'))return ok({explanations:[],monthly_spending:[]});
  if(url.includes('/transactions'))return ok({total:0,items:[]});
  return ok(profile(url.includes('C000018')?'C000018':'C002056'));
 }));
});

describe('combinable scenario explorer',()=>{
 it('combines chips, reports aria-pressed, and clears back to baseline',async()=>{
  render(<App/>);
  const ev=await screen.findByRole('button',{name:'EV'});const solar=screen.getByRole('button',{name:'Solar'});
  await screen.findByText(/Baseline profile/);
  fireEvent.click(ev);fireEvent.click(solar);
  expect(ev).toHaveAttribute('aria-pressed','true');expect(solar).toHaveAttribute('aria-pressed','true');
  await screen.findByText(/Applied: EV · SOLAR/);
  let calls=fetch.mock.calls.filter(([url])=>url.includes('/scenario'));
  expect(JSON.parse(calls.at(-1)[1].body)).toEqual({apply:['EV','SOLAR']});
  fireEvent.click(screen.getByRole('button',{name:'Clear all'}));
  await screen.findByText(/Baseline profile/);
  expect(ev).toHaveAttribute('aria-pressed','false');expect(solar).toHaveAttribute('aria-pressed','false');
  calls=fetch.mock.calls.filter(([url])=>url.includes('/scenario'));
  expect(JSON.parse(calls.at(-1)[1].body)).toEqual({apply:[]});
 });

 it('resets chip selection when the customer changes',async()=>{
  render(<App/>);const ev=await screen.findByRole('button',{name:'EV'});fireEvent.click(ev);await screen.findByText(/Applied: EV/);
  fireEvent.change(screen.getByLabelText('Demo customer'),{target:{value:'C000018'}});
  await waitFor(()=>expect(screen.getByRole('button',{name:'EV'})).toHaveAttribute('aria-pressed','false'));
  expect(await screen.findByText(/Baseline profile/)).toBeInTheDocument();
 });

 it('ignores an older scenario response that arrives after the latest selection',async()=>{
  let resolveOld;
  fetch.mockImplementation(async(url,options={})=>{
   if(url.includes('/scenario')){
    const apply=JSON.parse(options.body||'{}').apply||[];
    if(apply.length===1&&apply[0]==='EV')return new Promise(resolve=>{resolveOld=()=>resolve(ok(result('C002056',['EV'])));});
    return ok(result('C002056',apply));
   }
   if(url.includes('/customers?'))return ok({total:1,items:[profile('C002056')]});
   if(url.includes('/opportunities'))return ok({opportunities:[]});
   if(url.includes('/insights'))return ok({explanations:[],monthly_spending:[]});
   if(url.includes('/transactions'))return ok({total:0,items:[]});
   return ok(profile('C002056'));
  });
  render(<App/>);await screen.findByText(/Baseline profile/);
  fireEvent.click(await screen.findByRole('button',{name:'EV'}));
  fireEvent.click(screen.getByRole('button',{name:'Solar'}));
  await screen.findByText(/Applied: EV · SOLAR/);
  resolveOld();
  await waitFor(()=>expect(screen.getByText(/Applied: EV · SOLAR/)).toBeInTheDocument());
  expect(screen.queryByText(/^Applied: EV\./)).not.toBeInTheDocument();
 });
});
