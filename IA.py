'''
Created on 12 de ago de 2016

@author: fvj

PIECE AND COLOR BITMASK = 0bCPPP
where:
C - color
P - piece code

CASTLING RIGHTS BITMASK = 0bqkQK
where:
q - CASTLE_QUEENSIDE_BLACK
k - CASTLE_KINGSIDE_BLACK
Q - CASTLE_QUEENSIDE_WHITE
K - CASTLE_KINGSIDE_WHITE

This program uses "Little-Endian Rank-File Mapping":
bit_boards = 0b(h8)(g8)...(b1)(a1)
board = [ a1, b1, ..., g8, h8 ]

move = [ leaving_position, arriving_position ]

'''
from chess import *
from copy import deepcopy
from random import choice
from time import sleep, time

def material_balance(board):
    return material_sum(board, WHITE) - material_sum(board, BLACK)

def mobility_balance(game):
    return count_legal_moves(game, WHITE) - count_legal_moves(game, BLACK)

def positional_balance(game):
    return positional_bonus(game, WHITE) - positional_bonus(game, BLACK)


def positional_bonus(game, color):
    bonus = 0

    if color == WHITE:
        board = game.board
    elif color == BLACK:
        board = flip_board_v(game.board)

    for index in range(64):
        piece = board[index]

        if piece != EMPTY and piece & COLOR_MASK == color:
            piece_type = piece & PIECE_MASK

            if piece_type == PAWN:
                bonus += PAWN_BONUS[index]
            elif piece_type == KNIGHT:
                bonus += KNIGHT_BONUS[index]
            elif piece_type == BISHOP:
                bonus += BISHOP_BONUS[index]

            elif piece_type == ROOK:
                position = 0b1 << index

                if is_open_file(position, board):
                    bonus += ROOK_OPEN_FILE_BONUS
                elif is_semi_open_file(position, board):
                    bonus += ROOK_SEMI_OPEN_FILE_BONUS

                if position & RANK_7:
                    bonus += ROOK_ON_SEVENTH_BONUS

            elif piece_type == KING:
                if is_endgame(board):
                    bonus += KING_ENDGAME_BONUS[index]
                else:
                    bonus += KING_BONUS[index]

    return bonus


def evaluate_game(game):
    if game_ended(game):
        return evaluate_end_node(game)
    else:
        return material_balance(game.board) + positional_balance(game)# + 10*mobility_balance(game)

def evaluate_end_node(game):
    if is_checkmate(game, game.to_move):
        return win_score(game.to_move)
    elif is_stalemate(game) or \
         has_insufficient_material(game) or \
         is_under_75_move_rule(game):
        return 0


def win_score(color):
    if color == WHITE:
        return -10*PIECE_VALUES[KING]
    if color == BLACK:
        return 10*PIECE_VALUES[KING]


def evaluated_move(game, color):
    best_score = win_score(color)
    best_moves = []
    
    for move in legal_moves(game, color):
        evaluation = evaluate_game(make_move(game, move))
        
        if is_checkmate(make_move(game, move), opposing_color(game.to_move)):
            return [move, evaluation]
        
        if (color == WHITE and evaluation > best_score) or \
           (color == BLACK and evaluation < best_score):
            best_score = evaluation
            best_moves = [move]
        elif evaluation == best_score:
            best_moves.append(move)
                
    return [choice(best_moves), best_score]


def random_move(game, color):
    return choice(legal_moves(game, color))


def minimax(game, color, depth=1):
    if game_ended(game):
        return [None, evaluate_game(game)]
    
    [simple_move, simple_evaluation] = evaluated_move(game, color)
    
    if depth == 1 or \
       simple_evaluation == win_score(opposing_color(color)):
        return [simple_move, simple_evaluation]
    
    best_score = win_score(color)
    best_moves = []
    
    for move in legal_moves(game, color):
        his_game = make_move(game, move)
        
        if is_checkmate(his_game, his_game.to_move):
            return [move, win_score(his_game.to_move)]
            
        [_, evaluation] = minimax(his_game, opposing_color(color), depth-1)
        
        if evaluation == win_score(opposing_color(color)):
            return [move, evaluation]
        
        if (color == WHITE and evaluation > best_score) or \
           (color == BLACK and evaluation < best_score):
            best_score = evaluation
            best_moves = [move]
        elif evaluation == best_score:
            best_moves.append(move)
        
    return [choice(best_moves), best_score]

def alpha_beta(game, color, depth, alpha=-float('inf'), beta=float('inf')):
    if game_ended(game):
        return [None, evaluate_game(game)]
    
    [simple_move, simple_evaluation] = evaluated_move(game, color)
    
    if depth == 1 or \
       simple_evaluation == win_score(opposing_color(color)):
        return [simple_move, simple_evaluation]

    best_moves = []
        
    if color == WHITE:
        for move in legal_moves(game, color):
            if verbose:
                print('\t'*depth + str(depth) + '. evaluating ' + PIECE_CODES[get_piece(game.board, move[0])] + move2str(move))
                
            new_game = make_move(game, move)
            [_, score] = alpha_beta(new_game, opposing_color(color), depth-1, alpha, beta)
            
            if verbose:
                print('\t'*depth + str(depth) + '. ' + str(score) + ' [{},{}]'.format(alpha, beta))
            
            if score == win_score(opposing_color(color)):
                return [move, score]
            
            if score == alpha:
                best_moves.append(move)
            if score > alpha: # white maximizes her score
                alpha = score
                best_moves = [move]
                if alpha > beta: # alpha-beta cutoff
                    if verbose:
                        print('\t'*depth + 'cutoff')
                    break
        if best_moves:
            return [choice(best_moves), alpha]
        else:
            return [None, alpha]
    
    if color == BLACK:
        for move in legal_moves(game, color):
            if verbose:
                print('\t'*depth + str(depth) + '. evaluating ' + PIECE_CODES[get_piece(game.board, move[0])] + move2str(move))
                
            new_game = make_move(game, move)
            [_, score] = alpha_beta(new_game, opposing_color(color), depth-1, alpha, beta)
            
            if verbose:
                print('\t'*depth + str(depth) + '. ' + str(score) + ' [{},{}]'.format(alpha, beta))
            
            if score == win_score(opposing_color(color)):
                return [move, score]
            
            if score == beta:
                best_moves.append(move)
            if score < beta: # black minimizes his score
                beta = score
                best_moves = [move]
                if alpha > beta: # alpha-beta cutoff
                    if verbose:
                        print('\t'*depth + 'cutoff')
                    break
        if best_moves:
            return [choice(best_moves), beta]
        else:
            return [None, beta]


def get_AI_move(game, depth=2, use_book = False):
    if verbose:
        print('Searching best move for white...' if game.to_move == WHITE else 'Searching best move for black...')
    start_time = time()

    if (use_book):
        if find_in_book(game):
            move = get_book_move(game)
    else:
#       move = minimax(game, game.to_move, depth)[0]
        move = alpha_beta(game, game.to_move, depth)[0]

    end_time = time()
    if verbose:
        print('Found move ' + PIECE_CODES[get_piece(game.board, move[0])] + ' from ' + str(bb2str(move[0])) + ' to ' + str(bb2str(move[1])) + ' in {:.3f} seconds'.format(end_time-start_time) + ' ({},{})'.format(evaluate_game(game), evaluate_game(make_move(game, move))))
    return move

def watch_AI_game(game=Game(), sleep_seconds=0):
    print('Watching AI-vs-AI game!')
    while True:
        print_board(game.board)
        if game_ended(game):
            break
                
        game = make_move(game, get_AI_move(game))
        sleep(sleep_seconds)
    print_outcome(game)


def find_in_book(game):
    if game.position_history[0] != INITIAL_FEN:
        return False
    
    openings = []
    book_file = open("book.txt")
    for line in book_file:
        if line.startswith(game.get_move_list()) and line.rstrip() > game.get_move_list():
            openings.append(line.rstrip())
    book_file.close()
    return openings

def get_book_move(game):
    openings = find_in_book(game)
    chosen_opening = choice(openings)
    next_moves = chosen_opening.replace(game.get_move_list(), '').lstrip()
    move_str = next_moves.split(' ')[0]
    move = [str2bb(move_str[:2]), str2bb(move_str[-2:])]
    return move