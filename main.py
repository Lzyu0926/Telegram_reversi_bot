from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CommandHandler, CallbackQueryHandler
import random

black = '⚫️'
white = '⚪️'

async def computer_move(board):
    valid_moves = get_valid_moves(board,white)
    if valid_moves:
        # Randomly choose a valid move
        row, col = random.choice(valid_moves)
        board[(row, col)] = white
        return row, col
    return None, None

def enc(board):
    # board is a dictionary mapping (row, col) to grid
    # grid = [[board.get((row, col), '') for col in range(8)] for row in range(8)]
    number = 0
    base = 3
    for row in range(8):
        for col in range(8):
            number *= base
            # if grid[row][col] == black:
            if board.get((row, col)) == black:
                number += 2
            # elif grid[row][col] == white:
            elif board.get((row, col)) == white:
                number += 1
    return str(number)


def dec(number):
    board = {}
    base = 3
    for row in [7, 6, 5, 4, 3, 2, 1, 0]:
        for col in [7, 6, 5, 4, 3, 2, 1, 0]:
            if number % 3 == 2:
                board[(row, col)] = black
            elif number % 3 == 1:
                board[(row, col)] = white
            number //= base
    return board


def board_markup(board):
    # board will be encoded and embedded to callback_data
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(board.get((row, col), ' '), callback_data=f'{row}{col}{enc(board)}') for col in range(8)]
        for row in range(8)])

def get_valid_moves(board,color):
    valid_moves = []
    for row in range(8):
        for col in range(8):
            if (row, col) not in board:
                if is_valid_move(board, row, col,color):
                    valid_moves.append((row, col))
    return valid_moves

def is_valid_move(board, row, col,color):
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            if is_valid_direction(board, row, col, dr, dc,color):
                return True
    return False

def is_valid_direction(board, row, col, dr, dc, color):
    r, c = row + dr, col + dc
    if not is_valid_position(r, c):
        return False
    if (r, c) not in board or board[(r, c)] == color:
        return False
    while is_valid_position(r, c):
        if (r, c) not in board:
            return False
        if board[(r, c)] == color:
            return True
        r += dr
        c += dc
    return False

def is_valid_position(row, col):
    return 0 <= row < 8 and 0 <= col < 8

#---- reversi basic ----
def flip_pieces(board, row, col):
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]
    for dr, dc in directions:
        flip_line(board, row, col, dr, dc)

def flip_line(board, row, col, dr, dc):
    r, c = row + dr, col + dc
    if not is_valid_position(r, c):
        return
    if (r, c) not in board or board[(r, c)] == black:
        return
    line = []
    while is_valid_position(r, c):
        if (r, c) not in board:
            return
        if board[(r, c)] == black:
            for flip_row, flip_col in line:
                board[(flip_row, flip_col)] = black
            return
        line.append((r, c))
        r += dr
        c += dc


def flip_pieces_comp(board, row, col):
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]
    for dr, dc in directions:
        flip_line_comp(board, row, col, dr, dc)

def flip_line_comp(board, row, col, dr, dc):
    r, c = row + dr, col + dc
    if not is_valid_position(r, c):
        return
    if (r, c) not in board or board[(r, c)] == white:
        return
    line = []
    while is_valid_position(r, c):
        if (r, c) not in board:
            return
        if board[(r, c)] == white:
            for flip_row, flip_col in line:
                board[(flip_row, flip_col)] = white
            return
        line.append((r, c))
        r += dr
        c += dc

def count_pieces(board):
    black_count = 0
    white_count = 0
    for piece in board.values():
        if piece == black:
            black_count += 1
        elif piece == white:
            white_count += 1
    return black_count, white_count

# Define a few command handlers. These usually take the two arguments update and
# context.
async def func(update, context):
    data = update.callback_query.data
    # user clicked the button on row int(data[0]) and col int(data[1])
    row = int(data[0])
    col = int(data[1])
    
    board = dec(int(data[2:]))
    if (row, col) not in get_valid_moves(board,black):
        await context.bot.answer_callback_query(update.callback_query.id, 'This position is not clickable.')
        return
    
    await context.bot.answer_callback_query(update.callback_query.id, f'you make a move at row {row} col {col}')
    
    board[(row, col)] = black
    
    # flip
    flip_pieces(board, row, col)
    
    await context.bot.edit_message_text('Current board',
                                        reply_markup=board_markup(board),
                                        chat_id=update.callback_query.message.chat_id,
                                        message_id=update.callback_query.message.message_id)
    # Check if the game is over
    if len(get_valid_moves(board,black)) == 0:
        black_count, white_count = count_pieces(board)
        if black_count > white_count:
            await context.bot.send_message(update.callback_query.message.chat_id, 'Game over, you win')
        elif black_count == white_count:
            await context.bot.send_message(update.callback_query.message.chat_id, 'Game over, tie')
        else:
            await context.bot.send_message(update.callback_query.message.chat_id, 'Game over, you lose')
        return
    
    # Computer's turn
    computer_row, computer_col = await computer_move(board)
    
    if computer_row is not None and computer_col is not None:
        await context.bot.answer_callback_query(update.callback_query.id, f'computer makes a move at row {computer_row} col {computer_col}')
        # Apply flip rule
        
        flip_pieces_comp(board, computer_row, computer_col)
        
        await context.bot.edit_message_text('Current board',
                                            reply_markup=board_markup(board),
                                            chat_id=update.callback_query.message.chat_id,
                                            message_id=update.callback_query.message.message_id)
    
        # Check if the game is over after computer's move
        if len(get_valid_moves(board,white)) == 0:
            black_count, white_count = count_pieces(board)
            if black_count > white_count:
                await context.bot.send_message(update.callback_query.message.chat_id, 'Game over, you win')
            elif black_count == white_count:
                await context.bot.send_message(update.callback_query.message.chat_id, 'Game over, tie')
            else:
                await context.bot.send_message(update.callback_query.message.chat_id, 'Game over, you lose')
            return
            

async def start(update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Start the game. /game_start\nGet the basic. /help')

async def game_start(update, context):
    board = {(3,3): '⚫️', (3,4): '⚪️', (4,3): '⚪️', (4,4): '⚫️'}
    # reply_markup = board_markup(board)
    await update.message.reply_text('Current board', reply_markup=board_markup(board))
async def help(update, context):
    text = "There are sixty-four identical game pieces called disks, which are light on one side and dark on the other. Players take turns placing disks on the board with their assigned color facing up.\n\nDuring a play, any disks of the opponent's color that are in a straight line and bounded by the disk just placed and another disk of the current player's color are turned over to the current player's color. The objective of the game is to have the majority of disks turned to display one's color when the last playable empty square is filled."
    await update.message.reply_text(text)

def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    # put your token in this place
    application = Application.builder().token("TOKEN").build() 

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("game_start", game_start))
    application.add_handler(CommandHandler("help", help))

    application.add_handler(CallbackQueryHandler(func))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
