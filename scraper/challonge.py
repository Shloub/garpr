import requests
import re
import os
import iso8601
from model import MatchResult
from bs4 import BeautifulSoup
from config import config

BASE_CHALLONGE_API_URL = 'https://api.challonge.com/v1/tournaments'
TOURNAMENT_URL = os.path.join(BASE_CHALLONGE_API_URL, '%s.json')
PARTICIPANTS_URL = os.path.join(BASE_CHALLONGE_API_URL, '%s', 'participants.json')
MATCHES_URL = os.path.join(BASE_CHALLONGE_API_URL, '%s', 'matches.json')

# http://api.challonge.com/v1
class ChallongeScraper(object):
    def __init__(self, tournament_id, config_file_path=config.DEFAULT_CONFIG_PATH):
        self.tournament_id = tournament_id
        self.config = config.Config(config_file_path=config_file_path)
        self.api_key = self.config.get_challonge_api_key()
        self.api_key_dict = {'api_key': self.api_key}

        self.raw_dict = None
        self.get_raw()

    def get_raw(self):
        if self.raw_dict == None:
            self.raw_dict = {}

            url = TOURNAMENT_URL % self.tournament_id
            self.raw_dict['tournament'] = self._check_for_200(requests.get(url, params=self.api_key_dict)).json()

            url = MATCHES_URL % self.tournament_id
            self.raw_dict['matches'] = self._check_for_200(requests.get(url, params=self.api_key_dict)).json()

            url = PARTICIPANTS_URL % self.tournament_id
            self.raw_dict['participants'] = self._check_for_200(requests.get(url, params=self.api_key_dict)).json()

        return self.raw_dict

    def get_name(self):
        return self.get_raw()['tournament']['tournament']['name'].strip()

    def get_date(self):
        return iso8601.parse_date(self.get_raw()['tournament']['tournament']['created_at'])

    def get_matches(self):
        player_map = dict((p['participant']['id'], p['participant']['display-name'].strip())
                          for p in self.get_raw()['participants'])

        matches = []
        for m in self.get_raw()['matches']:
            m = m['match']
            winner_id = m['winner_id']
            loser_id = m['loser_id']
            if winner_id is not None and loser_id is not None:
                winner = player_map[winner_id]
                loser = player_map[loser_id]
                match_result = MatchResult(winner=winner, loser=loser)
                matches.append(match_result)

        return matches

    def get_players(self):
        return [p['participant']['display-name'].strip() \
                for p in self.get_raw()['participants']]

    def _check_for_200(self, response):
        if response.status_code != 200:
            raise Exception('Received status code of %d' % response.status_code)

        return response

