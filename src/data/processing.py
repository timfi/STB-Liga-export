# -*- coding: utf-8 -*-
from .acquisition import *
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

__all__ = [
    'cleanup_team_data',
    'cleanup_ranking_data',
    'cleanup_encounter_data',
]

def cleanup_team_data(team_data):
    '''A method to clean up the given team data.

    <args>
    team_encounter_data - encounter data to clean
    team_ranking_data - ranking data to clean
    '''
    team_encounter_data, team_ranking_data = team_data[0], team_data[1]
    team_encounter_data = team_encounter_data.iloc[:,:9]
    team_encounter_data.columns = ['Liga', 'Begin', 'Heim', 'Gast', 'Mannschaften', 'Punkte', 'TP', 'GP', 'Bemerkung']
    team_ranking_data = team_ranking_data.applymap(lambda x: x.split(':')[-1])
    team_ranking_data.columns = ['Platz', 'Mannschaft', 'Tabellenpunkte', 'Gerätepunkte', 'Wettkämpfe']
    return team_encounter_data, team_ranking_data

def cleanup_ranking_data(ranking_data):
    '''A method to clean up the given ranking data.

    <args>
    ranking_data - data to clean
    '''
    # TODO cleanup_func for ranking data
    return ranking_data

def cleanup_encounter_data(encounter_data):
    '''A method to clean up the given ranking data.

    <args>
    encounter_data - data to clean
    '''
    # Split table
    encounter_lteam_data = encounter_data.iloc[:,:5]
    encounter_rteam_data = encounter_data.iloc[:,6:]
    # reverse rteam table
    encounter_rteam_data = encounter_rteam_data[encounter_rteam_data.columns[::-1]]
    # Relable rTeams columns
    encounter_rteam_data.columns = [0,1,2,3,4]
    return encounter_lteam_data, encounter_rteam_data
