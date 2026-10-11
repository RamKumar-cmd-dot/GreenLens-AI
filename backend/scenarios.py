"""Canonical what-if presets. Values describe hypothetical customer attributes only."""

SCENARIO_PRESETS = {
    'EV': {
        'label': 'EV',
        'meaning': 'Simulates an existing EV with no replacement use case; it does not simulate an EV purchase.',
        'overrides': {
            'vehicle_ownership': 1,
            'vehicle_type': 'electric',
            'owns_ev': 1,
            'replacement_intent': 0,
        },
    },
    'GREEN_HOME': {
        'label': 'Green home',
        'meaning': 'Assumes home ownership and an existing gas boiler so the illustrative Green Home scenario can be evaluated; this is not a completed retrofit and a gas boiler is not itself a green improvement.',
        'overrides': {
            'homeowner': 1,
            'heating_technology': 'gas_boiler',
        },
    },
    'SOLAR': {
        'label': 'Solar',
        'meaning': 'Assumes home ownership and a suitable roof; it does not represent installed solar panels. Impact uses the existing supported regional-yield rules.',
        'overrides': {
            'homeowner': 1,
            'roof_suitable': 1,
        },
    },
    'PAPERLESS': {
        'label': 'Paperless',
        'meaning': 'Simulates paperless statements; it does not record a customer preference or change stored customer data.',
        'overrides': {
            'paper_statements_enabled': 0,
        },
    },
}

# Request compatibility for the two original scenario buttons.
LEGACY_OVERRIDES = {
    tuple(sorted(SCENARIO_PRESETS['EV']['overrides'].items())): 'EV',
    tuple(sorted(SCENARIO_PRESETS['PAPERLESS']['overrides'].items())): 'PAPERLESS',
}


def normalize_selection(apply=None, changes=None):
    """Validate chip IDs, de-duplicate in request order, and accept old exact payloads."""
    if apply is not None and changes is not None:
        raise ValueError('Send either apply or legacy changes, not both')
    if changes is not None:
        if not isinstance(changes, dict):
            raise ValueError('changes must be an object')
        if not changes:
            return []
        chip = LEGACY_OVERRIDES.get(tuple(sorted(changes.items())))
        if chip is None:
            raise ValueError('Legacy changes must exactly match the EV or Paperless preset')
        return [chip]
    if apply is None:
        raise ValueError('apply is required')
    if not isinstance(apply, list):
        raise ValueError('apply must be a list')
    invalid = [chip for chip in apply if not isinstance(chip, str) or chip not in SCENARIO_PRESETS]
    if invalid:
        raise ValueError(f'Unknown scenario chip(s): {invalid}')
    return list(dict.fromkeys(apply))
