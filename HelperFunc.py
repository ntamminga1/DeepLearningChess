################################# IMPORT LIBRARIES ##########################################
import requests
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import time
from tqdm import tqdm
import pickle
import chess
import chess.pgn
import pandas as pd
import re

############################### ENGINE QUERY FUNCTIONS ######################################
base_url = 'http://www.chessdb.cn/cdb.php'

def process_fen(fen):
    params = {
        'action': 'queryall',
        'board': fen,
        'showall': 1
    }
    # Send the GET request
    done = False
    tries = 0
    while not done and tries < 5:
        tries += 1
        done = True
        response = requests.get(base_url, params=params)

        moves_data = response.text.strip().split('|')
        engine_moves = []
        max_score = -np.inf
        for move_data in moves_data:
            #Convert the query into the relevant data
            
            details = move_data.split(',')

            #With the threading, sometimes the full query isnt load properly
            #if it isn't loaded fully, redo the request
            if len(details) > 2:
                move, score = details[:2]
                move = move.split(':')
                score = score.split(':')
                if len(move)>1 and len(score)>1:
                    move = move[1]
                    score = score[1]
                else:
                    done = False
            else:
                done = False


            #Keep all moves with the top score
            if done and (score.isnumeric() or (score.startswith('-') and score[1:].isnumeric())) and int(score) >= max_score:
                max_score = int(score)
                engine_moves.append(move)
            else:
                break
    if not done:
        print(tries)
        return []
    else:
        return engine_moves
    
def process_multiple_fens(fens, max_workers=20):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(tqdm(executor.map(process_fen, fens), total=len(fens)))
    return results

############################### BUILD BITBOARDS ###############################################
letter_2_number = {'a':0,'b':1,'c':2,'d':3,'e':4,'f':5,'g':6,'h':7}
number_2_letter = {0:'a',1:'b',2:'c',3:'d',4:'e',5:'f',6:'g',7:'h'}

def board_2_bit(board):
    pieces = ['p','r','n','b','q','k']
    layers = []
    for piece in pieces:
        layers.append(create_layer(board, piece))
    bitboard = np.stack(layers)
    return bitboard

def create_layer(board, type):
    s = str(board)
    s = re.sub(f'[^{type}{type.upper()} \n]', '.', s)
    s = re.sub(f'{type}', '-1', s)
    s = re.sub(f'{type.upper()}', '1', s)
    s = re.sub(f'\.', '0', s)

    board_mat = []
    for row in s.split('\n'):
        row = row.split(' ')
        row = [int(x) for x in row]
        board_mat.append(row)

    return np.array(board_mat)

def move_2_bit(move, board, val):
    uci_move = chess.Move.from_uci(move)
    board.push(uci_move)
    move = str(board.pop())

    from_layer = np.zeros((8,8))
    from_row = 8 - int(move[1])
    from_column = letter_2_number[move[0]]
    from_layer[from_row, from_column] = val

    to_layer = np.zeros((8,8))
    to_row = 8 - int(move[3])
    to_column = letter_2_number[move[2]]
    to_layer[to_row, to_column] = val

    return np.stack([from_layer, to_layer])

def fen_to_bitboard(fen, move):
    board = chess.Board(fen)
    fen_bit = board_2_bit(board)
    split_fen = fen.split()
    if split_fen[1] == 'w':
        val = 1
    if split_fen[1] == 'b':
        val = -1
    h_move = move_2_bit(move, board, val)
    bitboard = np.append(fen_bit, h_move, axis=0)
    bitboard = np.ndarray.flatten(bitboard)
    bitboard = np.append(bitboard, val)
    bitboard = np.append(bitboard, 1*('K' in split_fen[2]))
    bitboard = np.append(bitboard, 1*('Q' in split_fen[2]))
    bitboard = np.append(bitboard, -1*('k' in split_fen[2]))
    bitboard = np.append(bitboard, -1*('q' in split_fen[2]))
    
    return bitboard