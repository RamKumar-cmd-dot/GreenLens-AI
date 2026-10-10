import React from 'react';
import {describe,it,expect,vi,beforeEach} from 'vitest';
import {render,screen,fireEvent,waitFor,within} from '@testing-library/react';
import App from '../src/App.jsx';
const customer=id=>({customer_id:id,data_timestamp:'2026-01-01',features:{region:'London',age_band:'30-44',monthly_income_gbp:3000,mean_monthly_fuel:150,electricity_kwh_year:4000,homeowner:1,vehicle_type:'petrol',digital_logins_month:18}});
const products=id=>['GP01','GP02','GP03','GP04'].map((pid,i)=>({customer_id:id,product_id:pid,product_name:['EV Finance','Green Home Loan','Solar Finance','Paperless Banking'][i],propensity:id==='C000034'?.25:.75,threshold_screen:{threshold:.24,above_threshold:id==='C000034'?.25>=.24:.75>=.24},status:id==='C000026'&&pid==='GP01'?'EXCLUDED':'POTENTIAL_OPPORTUNITY',reason_codes:['HOME_OWNER'],evidence:{homeowner:1},applicable_exclusions:[],impact:{impact_status:'UNAVAILABLE',reason:'Missing verified inputs',assumptions:[],limitations:[],factors:[]},reliability:{validation_brier:.1,missing_feature_count:0},recommended_action:'Review with relationship team.',data_timestamp:'2026-01-01',model_version:'fixture'}));
beforeEach(()=>{vi.stubGlobal('fetch',vi.fn(async url=>{
 let data;
 if(url.includes('/business/summary')) data={total_customers:2,unique_customers_with_opportunities:2,products:[],data_timestamp:'2026-01-01',model_version:'fixture',high_potential_threshold:.3,caveat:'Conditional only',portfolio_energy_kwh_year:8000,paperless_customers:1,paperless_adoption_rate:.5,mobile_app_active_customers:2,mean_monthly_digital_logins:12};
 else if(url.includes('/business/trends')) data={items:[{month:'2025-01',category:'Fuel',amount_gbp:220}],data_timestamp:'2026-01-01',caveat:'Synthetic history'};
 else if(url.includes('/scenario')) data={customer_id:'C000034',synthetic:true,scenario_changes:{paper_statements_enabled:0},opportunities:products('C000034')};
 else if(url.includes('/business/segments')) data={items:[{region:'London',potential_customers:2}]};
 else if(url.includes('/business/opportunities')) data={total:1,items:[products('C000026')[1]]};
 else if(url.includes('/customers?')) data={total:2,items:[customer('C000034'),customer('C000026')]};
 else if(url.includes('/transactions')) data={total:0,items:[]};
 else if(url.includes('/opportunities')){const id=url.includes('C000026')?'C000026':'C000034';data={opportunities:products(id)};}
 else if(url.includes('/insights')) data={explanations:[],monthly_spending:[{month:'2025-12',category:'Fuel',amount_gbp:150}]};
 else data=customer(url.includes('C000026')?'C000026':'C000034');
 return {ok:true,json:async()=>data};
}));});
describe('Customer dashboard',()=>{
 it('business view supports customer drill-down',async()=>{render(<App/>);fireEvent.click(screen.getByRole('button',{name:/Business intelligence/}));expect(await screen.findByText('Customers analysed')).toBeInTheDocument();fireEvent.click(await screen.findByRole('button',{name:'C000026 ↗'}));await waitFor(()=>expect(within(screen.getByTestId('product-GP01')).getByText('excluded')).toBeInTheDocument());});
 it('loads four cards from API responses',async()=>{render(<App/>);expect(await screen.findByTestId('product-GP01')).toBeInTheDocument();expect(screen.getAllByTestId(/product-GP/)).toHaveLength(4);expect(screen.getByRole('heading',{name:'Transaction history'})).toBeInTheDocument();});
 it('moves excluded products out of offers into a separate explanation section',async()=>{render(<App/>);await screen.findByTestId('product-GP01');fireEvent.change(screen.getByLabelText('Demo customer'),{target:{value:'C000026'}});await screen.findByText('Not recommended or more information needed');fireEvent.click(screen.getByText('Not recommended or more information needed'));const excluded=await screen.findByTestId('product-GP01');expect(within(excluded).getByText('excluded')).toBeInTheDocument();expect(excluded.closest('details')).toBeInTheDocument();});
 it('handles failed requests and retries',async()=>{fetch.mockImplementation(async()=>({ok:false,status:503}));render(<App/>);expect((await screen.findAllByRole('alert')).length).toBeGreaterThan(0);expect(screen.getAllByRole('button',{name:'Retry'}).length).toBeGreaterThan(0);});
 it('expands supporting evidence and next action',async()=>{render(<App/>);const card=await screen.findByTestId('product-GP01');fireEvent.click(within(card).getByRole('button',{name:/Evidence/}));expect(within(card).getByText('Review with relationship team.')).toBeInTheDocument();});
 it('scenario explorer calls the backend with a hypothetical change',async()=>{render(<App/>);fireEvent.click(await screen.findByRole('button',{name:'Simulate switching to paperless'}));await screen.findByText(/Hypothetical changes:/);expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/customers/C002056/scenario'),expect.objectContaining({method:'POST'}));});
});
