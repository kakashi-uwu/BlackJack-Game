import sqlite3

class DBh:
    def __init__(self, database):
        '''Connecting to DB and saving connection cursor'''
        self.connection = sqlite3.connect(database)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

    def load_user(self, user_id):
        '''load user if exists'''
        with self.connection:
            return self.cursor.execute('SELECT * FROM `user` WHERE `user_id` = ?', (user_id,)).fetchall()

    def add_user(self, user_id):
        '''register user'''
        with self.connection:
            return self.cursor.execute('INSERT INTO `user` (`user_id`) VALUES (?)', (user_id,))

    def update(self, table, set, where, values):
        '''update data'''
        with self.connection:
            return self.cursor.execute(f'UPDATE {table} SET {set} WHERE {where}', values)

    def close(self):
        '''Close connection with DB'''
        self.connection.close()