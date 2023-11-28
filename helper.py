import string

def convert_seat_to_index(chosen_seats):
    row_dict = {letter: index for index, letter in enumerate(string.ascii_uppercase)}
    matrix_indices = []
    for seat in chosen_seats:
        row_label, col_label = seat[0], int(seat[1:])  # Extracting row label and column number
        row_index = row_dict[row_label]  # Convert row label to numeric index
        col_index = col_label - 1  # Adjusting column to 0-based index
        matrix_indices.append((row_index, col_index))
    return matrix_indices

def serialize(x):
    if type(x) == list:
        return [i.serialize() for i in x]
    return x.serialize()