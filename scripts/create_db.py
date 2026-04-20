import psycopg2

DB_CONFIG = {
    'host': 'postgres',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'database': 'receitas'
}

def create_tables():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS receita (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL UNIQUE,
                descricao VARCHAR(200) NOT NULL,
                data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                custo NUMERIC NOT NULL,
                tipo_receita VARCHAR(100) NOT NULL CHECK (tipo_receita IN ('doce', 'salgada'))
            )
        """)

        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'receita_nome_key'
                ) THEN
                    ALTER TABLE receita ADD CONSTRAINT receita_nome_key UNIQUE (nome);
                END IF;
            END $$;
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS usuario (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                login VARCHAR(100) NOT NULL UNIQUE,
                senha VARCHAR(100) NOT NULL,
                situacao VARCHAR(100) NOT NULL
            )
        """)

        cur.execute("""
            INSERT INTO usuario (nome, login, senha, situacao)
            VALUES ('Administrador', 'admin', 'admin123', 'ativo')
            ON CONFLICT (login) DO NOTHING
        """)

        receitas = [
            ('Bolo de Chocolate', 'Bolo fofinho com cobertura de chocolate', 25.50, 'doce'),
            ('Torta de Morango', 'Torta com morangos frescos e creme', 32.00, 'doce'),
            ('Brigadeiro', 'Doce tradicional brasileiro', 15.00, 'doce'),
            ('Pudim', 'Pudim de leite condensado com calda', 18.00, 'doce'),
            ('Mousse de Maracujá', 'Mousse refrescante de maracujá', 12.00, 'doce'),
            ('Pizza Margherita', 'Mussarela, tomate e manjericão', 35.00, 'salgada'),
            ('Lasanha à Bolonhesa', 'Camadas de massa, carne e queijo', 42.00, 'salgada'),
            ('Hambúrguer Artesanal', 'Pão brioche, carne 180g e queijo', 28.00, 'salgada'),
            ('Frango à Parmegiana', 'Filé de frango empanado com queijo', 38.00, 'salgada'),
            ('Coxinha', 'Coxinha de frango com catupiry', 6.00, 'salgada')
        ]

        for receita in receitas:
            cur.execute("""
                INSERT INTO receita (nome, descricao, custo, tipo_receita)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (nome) DO NOTHING
            """, receita)

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    create_tables()