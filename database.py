import sqlite3

def create_database():
    conn = sqlite3.connect("pesos.db")  # Cria um arquivo de banco de dados SQLite
    cursor = conn.cursor()

    # Criação da tabela
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dados_pesagem (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            peso REAL NOT NULL,
            data_hora DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_weight(weight):
    conn = sqlite3.connect("pesos.db")
    cursor = conn.cursor()

    # Inserir peso no banco de dados
    cursor.execute("INSERT INTO dados_pesagem (peso) VALUES (?)", (weight,))
    conn.commit()
    conn.close()
