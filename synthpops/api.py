"""
This module provides the layer for communicating with the agent-based model Covasim.
"""

import sciris as sc
import synthpops as sp

# Put this here so it's accessible as sp.api.choices
popsize_choices = [5000,
                    6000,
                   10000,
                   20000,
                   50000,
                   100000,
                   120000,
                ]


def make_population(n=None, max_contacts=None, as_objdict=False, generate=None, with_industry_code=False, with_facilities=False, use_two_group_reduction=True, average_LTCF_degree=20):
    '''
    Make a full population network including both people (ages, sexes) and contacts using Seattle, Washington cached data.

    Args:
        n (int)                        : The number of people to create.
        max_contacts (dict)            : A dictionary for maximum number of contacts per layer: keys must be "S" (school) and/or "W" (work).
        as_objdict (bool)              : If True, change popdict type to ``sc.objdict``.
        generate (bool)                : If True, first look for cached population files and if those are not available, generate new population
        with_industry_code (bool)      : If True, assign industry codes for workplaces, currently only possible for cached files of populations in the US
        with_facilities (bool)         : If True, create long term care facilities
        use_two_group_reduction (bool) : If True, create long term care facilities with reduced contacts across both groups
        average_LTCF_degree (int)      : default average degree in long term care facilities

    Returns:
        network (dict): A dictionary of the full population with ages and connections.

    '''

    default_n = 10000
    default_max_contacts = {'S': 20, 'W': 20}  # this can be anything but should be based on relevant average number of contacts for the population under study

    if n is None: n = default_n
    n = int(n)
    if n not in popsize_choices:
        if generate is False:
            choicestr = ', '.join([str(choice) for choice in popsize_choices])
            errormsg = f'If generate=False, number of people must be one of {choicestr}, not {n}'
            raise ValueError(errormsg)
        else:
            generate = True # If not found, generate

    max_contacts = sc.mergedicts(default_max_contacts, max_contacts)

    country_location = 'usa'
    state_location = 'Washington'
    location = 'seattle_metro'
    sheet_name = 'United States of America'

    options_args = {'use_microstructure': True, 'use_industry_code': with_industry_code, 'use_long_term_care_facilities': with_facilities, 'use_two_group_reduction': use_two_group_reduction, 'average_LTCF_degree': average_LTCF_degree}
    network_distr_args = {'Npop': int(n)}

    # Heavy lift 1: make the contacts and their connections
    try:
        # try to read in from file
        population = sp.make_contacts(location=location, state_location=state_location, country_location=country_location, options_args=options_args, network_distr_args=network_distr_args)
    except:
        # make a new network on the fly
        if generate:
            if with_facilities:
                population = sp.generate_microstructure_with_facilities(sp.datadir, location=location, state_location=state_location, country_location=country_location, gen_pop_size=n, return_popdict=True, use_two_group_reduction=use_two_group_reduction, average_LTCF_degree=average_LTCF_degree)
            else:
                population = sp.generate_synthetic_population(n, sp.datadir, location=location, state_location=state_location, country_location=country_location, sheet_name=sheet_name, plot=False, return_popdict=True)
    else:
        if with_facilities and with_industry_code:
            errormsg = f'Requesting both long term care facilities and industries by code is not supported yet.'
            raise ValueError(errormsg)
        # raise NotImplementedError("Population not available")

    # Semi-heavy-lift 2: trim them to the desired numbers
    population = sp.trim_contacts(population, trimmed_size_dic=max_contacts, use_clusters=False)

    # Change types
    if as_objdict:
        population = sc.objdict(population)
    for key,person in population.items():
        if as_objdict:
            population[key] = sc.objdict(population[key])
            population[key]['contacts'] = sc.objdict(population[key]['contacts'])
        for layerkey in population[key]['contacts'].keys():
            population[key]['contacts'][layerkey] = list(population[key]['contacts'][layerkey])
    return population
