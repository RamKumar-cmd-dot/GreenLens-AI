"""Annual operational scenarios, with source-backed factors and explicit assumptions."""
import json
import math
from ml.common import DATA
from backend.schemas import Impact

FACTOR_PATH = DATA/'reference/emission_factors_2025.json'
DEFAULT_FACTORS = json.loads(FACTOR_PATH.read_text())['factors'] if FACTOR_PATH.exists() else {}

def number(f, key):
    value = f.get(key)
    if value is None or isinstance(value, bool): return None
    try: value = float(value)
    except (TypeError, ValueError): return None
    return value if math.isfinite(value) and value >= 0 else None

def estimate(pid, f, factors=None):
    factors = DEFAULT_FACTORS if factors is None else factors
    used = []
    def factor(key):
        record = factors.get(key)
        unit = 'kgCO2e/litre' if key.endswith('litre') else 'kgCO2e/kWh'
        if not record or record.get('unit') != unit or not record.get('source_url') or not record.get('year'): raise ValueError('Required documented emissions factor unavailable')
        value = number(record, 'value')
        if value is None: raise ValueError('Invalid emissions factor')
        used.append(record)
        return value
    def unavailable(reason): return Impact(impact_status='UNAVAILABLE',reason=reason)
    limitations = ['Illustrative scenario, not a prediction of adoption or a guarantee.', 'Synthetic annual activity estimates; verify customer inputs.', 'Operational boundary excludes manufacturing, upstream fuel, grid losses and rebound effects.']
    try:
        if pid == 'GP01':
            mileage = number(f,'annual_mileage_estimate')
            if mileage is None or f.get('vehicle_type') not in ['petrol','diesel']: return unavailable('A combustion vehicle and valid annual mileage are required; EV-to-EV replacement is not modelled.')
            fuel = f['vehicle_type']
            efficiency = number(f,'fuel_litres_per_100km') if 'fuel_litres_per_100km' in f else 7.0 if fuel=='petrol' else 6.0
            ev = number(f,'ev_kwh_per_km') if 'ev_kwh_per_km' in f else .18
            if efficiency is None or efficiency == 0 or ev is None: return unavailable('Invalid vehicle efficiency input')
            km = mileage * 1.609344
            baseline = km * efficiency / 100 * factor(fuel+'_litre')
            scenario = km * ev * factor('electricity_kwh')
            assumptions = [f'Annual distance = {mileage:g} miles × 1.609344 km/mile.', f'Illustrative combustion efficiency = {efficiency:g} litres/100 km; EV grid demand = {ev:g} kWh/km including assumed charging losses.', 'Same annual distance; 2025 UK operational factors held constant. Efficiency defaults are scenario choices, not measured vehicle specifications.']
        elif pid == 'GP02':
            gas = number(f,'gas_kwh_year')
            if f.get('homeowner')!=1 or f.get('heating_technology')!='gas_boiler' or gas is None: return unavailable('Owner with gas-boiler heating and annual gas kWh required for this scenario.')
            baseline = gas * factor('gas_kwh'); scenario = baseline * .9
            assumptions = ['Illustrative heating-controls/efficiency package reduces total annual gas demand by 10%; scenario assumption, not an engineering forecast.', 'Gas kWh assumed gross calorific value. No change to electricity use. An assessment must establish achievable reduction.']
        elif pid == 'GP03':
            keys = ['solar_capacity_kwp','solar_yield_kwh_per_kwp_year','solar_self_consumption_ratio','electricity_kwh_year']
            values = [number(f,k) for k in keys]
            if f.get('homeowner')!=1 or f.get('roof_suitable')!=1 or any(v is None for v in values) or not f.get('solar_yield_source') or not f.get('solar_location'):
                return unavailable('Requires verified capacity, location-specific annual yield and source, roof suitability, self-consumption ratio and annual demand. Region alone is insufficient.')
            capacity,yield_,ratio,demand = values
            if ratio>1: return unavailable('Solar self-consumption ratio must be between zero and one')
            generation = capacity*yield_; displaced = min(demand,generation*ratio); ef=factor('electricity_kwh')
            return Impact(impact_status='ESTIMATED',baseline_kgco2e=demand*ef,scenario_kgco2e=(demand-displaced)*ef,avoided_kgco2e=displaced*ef,generation_kwh=generation,factors=used,assumptions=[f'Generation = {capacity:g} kWp × {yield_:g} kWh/kWp/year; yield source: {f["solar_yield_source"]}; location: {f["solar_location"]}.',f'Self-consumption ratio {ratio:g}; displaced demand capped at annual consumption. Exports receive no credit.'],limitations=limitations)
        elif pid == 'GP04':
            if f.get('paper_statements_enabled') not in [0,1]: return unavailable('Paper statement preference is missing')
            pages = 48.0 if f['paper_statements_enabled']==1 else 0.0
            return Impact(impact_status='ESTIMATED',avoided_pages=pages,assumptions=['One monthly statement of four printed pages: 12 × 4 pages/year; illustrative frequency and length, not observed counts.'],limitations=['No carbon result: a verified statement lifecycle factor is unavailable. Digital-delivery impacts are not quantified.','Avoided pages assume an actual switch and no subsequent printing.'])
        else: return unavailable('Unsupported product')
        return Impact(impact_status='ESTIMATED',baseline_kgco2e=baseline,scenario_kgco2e=scenario,avoided_kgco2e=baseline-scenario,assumptions=assumptions,factors=used,limitations=limitations+['Negative avoided emissions are retained and mean the scenario increases emissions.'])
    except ValueError as exc:
        return unavailable(str(exc))
