# This file contains the function to turn an FEN into an opening, along with it's helper functions

# Import necessary libraries
import chess
import chess.pgn
import pandas as pd
from bs4 import BeautifulSoup
import requests
import re

# Splits the total games into number of white wins, black wins, and draws
def find_totals(string):
  white_start = string.find('white', 0, -1)+7
  white_end = string.find(',', white_start, -1)
  draw_start = string.find('draw', white_start, -1)+7
  draw_end = string.find(',', draw_start, -1)
  black_start = string.find('black', draw_start, -1)+7
  black_end = string.find(',', black_start, -1)
  return int(string[white_start:white_end]), int(string[draw_start:draw_end]), int(string[black_start:black_end])

# Pulls the opening name and ECO code
def find_name_eco(string):
  if string.find('null') != -1:
    return 'null', 'null'
  i = string.find('eco')+6
  j = string.find('"', i)
  k = string.find('name')+7
  l = string.find('"', k)
  return string[i:j], string[k:l]

# Pulls the moves from the most common moves string
def find_common_move(string):
  i = string.find('uci')+6
  j = string.find('"', i)
  k = string.find('san')+6
  l = string.find('"', k)
  return [string[i:j], string[k:l]]

def fen_to_opening(fen):
  # Read Opening from Lichess Database
  base_url = 'https://explorer.lichess.ovh/lichess?variant=standard&speeds=classical&fen='
  # Other game style stats on the openings can be found with different base_url links
  # The styling for these URLs can be found here: https://lichess.org/api#tag/Opening-Explorer/operation/openingExplorerLichess
  url = base_url + fen
  page = requests.get(url)
  soup = BeautifulSoup(page.content, "html.parser")
  string = soup.string

  # Split soup into useful strings
  totals, rest = string.split('moves')
  moves, rest = rest.split('recentGames')
  openeco = rest.split('opening')[1]
  
  # Read relevant data from strings
  white, draw, black = find_totals(totals)
  eco, name = find_name_eco(openeco)
  try:
    common1 = find_common_move(moves.split('{')[1])
  except IndexError:
    common1 = 'None'
  try:
    common2 = find_common_move(moves.split('{')[2])
  except IndexError:
    common2 = 'None'
  try:
    common3 = find_common_move(moves.split('{')[3])
  except IndexError:
    common3 = 'None'

  # Returns either true or false depending on whether this is classified as an opening
  # Also returns all the data gathered from our scraping
  if name=='null':
    return False, [name, eco, white, draw, black, common1, common2, common3]
  else:
    return True, [name, eco, white, draw, black, common1, common2, common3]