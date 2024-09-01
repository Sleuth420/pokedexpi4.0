import sqlite3
import requests
import time
import logging
import config
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Set up logging
logging.basicConfig(filename='pokedex.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s')

# Define a custom retry strategy for requests
retries = Retry(
    total=5,
    status_forcelist=[429, 500, 502, 503, 504],
    backoff_factor=0.3,
    respect_retry_after_header=True,
)
adapter = HTTPAdapter(max_retries=retries)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)


class PokemonDataManager:
    def __init__(self):
        self.create_database_file()
        self.conn = self.create_connection(config.DATABASE_FILE)
        self.create_pokemon_table()

    def create_database_file(self):
        """Creates the database file if it doesn't exist."""
        try:
            os.makedirs(os.path.dirname(config.DATABASE_FILE), exist_ok=True)
            with open(config.DATABASE_FILE, 'a'):
                pass  # Create an empty file if it doesn't exist
            logging.info(f"Database file created: {config.DATABASE_FILE}")
        except OSError as e:
            logging.error(f"Error creating database file: {e}")

    def create_connection(self, db_file):
        """Creates a database connection to the SQLite database."""
        try:
            conn = sqlite3.connect(db_file)
            logging.info(f"Connected to database: {db_file} (SQLite {sqlite3.version})")
            return conn
        except sqlite3.Error as e:
            logging.error(f"Error connecting to database: {e}")
            return None

    def create_pokemon_table(self):
        """Creates the pokemon table in the database if it doesn't exist."""
        sql_create_pokemon_table = """
        CREATE TABLE IF NOT EXISTS pokemon (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            type1 TEXT NOT NULL,
            type2 TEXT,
            hp INTEGER,
            attack INTEGER,
            defense INTEGER,
            sp_atk INTEGER,
            sp_def INTEGER,
            speed INTEGER,
            sprite_front TEXT,
            sprite_back TEXT,
            description TEXT,
            is_favorite INTEGER DEFAULT 0
        );
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql_create_pokemon_table)
            logging.info("Pokemon table created or already exists.")
        except sqlite3.Error as e:
            logging.error(f"Error creating pokemon table: {e}")

    def fetch_pokemon_data(self, pokemon_url):
        """Fetches pokemon data from the PokeAPI, including sprites."""
        try:
            response = http.get(pokemon_url, timeout=10)  # Set a timeout for the request
            response.raise_for_status()

            pokemon_data = response.json()
            species_url = pokemon_data['species']['url']
            species_response = http.get(species_url, timeout=10)  # Set a timeout for the request
            species_response.raise_for_status()
            species_data = species_response.json()

            # Basic Data
            id = pokemon_data['id']
            name = pokemon_data['name']
            type1 = pokemon_data['types'][0]['type']['name']
            type2 = pokemon_data['types'][1]['type']['name'] if len(pokemon_data['types']) > 1 else None
            hp = pokemon_data['stats'][0]['base_stat']
            attack = pokemon_data['stats'][1]['base_stat']
            defense = pokemon_data['stats'][2]['base_stat']
            sp_atk = pokemon_data['stats'][3]['base_stat']
            sp_def = pokemon_data['stats'][4]['base_stat']
            speed = pokemon_data['stats'][5]['base_stat']
            sprite_front = pokemon_data.get('sprites', {}).get('front_default')
            sprite_back = pokemon_data.get('sprites', {}).get('back_default')

            # Description (English only)
            description = None
            for entry in species_data.get('flavor_text_entries', []):
                if entry['language']['name'] == 'en':
                    description = entry['flavor_text']
                    break

            return (
                id,
                name,
                type1,
                type2,
                hp,
                attack,
                defense,
                sp_atk,
                sp_def,
                speed,
                sprite_front,
                sprite_back,
                description
            )

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching Pokémon data from {pokemon_url}: {e}")
            return None

    def insert_pokemon(self, pokemon):
        """Inserts a new pokemon into the pokemon table, including sprites."""
        sql = """ 
        INSERT INTO pokemon(id, name, type1, type2, hp, attack, defense, sp_atk, sp_def, 
                        speed, sprite_front, sprite_back, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) 
        """
        try:
            cur = self.conn.cursor()
            cur.execute(sql, pokemon)
            self.conn.commit()
            logging.info(f"Inserted Pokémon with ID {cur.lastrowid}")
            return cur.lastrowid
        except sqlite3.Error as e:
            logging.error(f"Error inserting Pokémon: {e}")

    def populate_database(self, batch_size=50):
        """Populates the database with pokemon data."""
        cursor = self.conn.cursor()
        offset = 0  # Start from the beginning

        while True:
            url = f'{config.POKEAPI_BASE_URL}pokemon?limit={batch_size}&offset={offset}'
            response = http.get(url, timeout=10)  # Set a timeout for the request

            if response.status_code == 200:
                pokemon_list = response.json()['results']

                # Break the loop if there are no more Pokémon to fetch
                if not pokemon_list:
                    break

                # Fetch individual Pokemon data
                for pokemon in pokemon_list:
                    pokemon_url = pokemon['url']
                    pokemon_id = pokemon_url.split('/')[-2]  # Extract the Pokemon id

                    # Check if Pokemon already exists (using pokemon_url for uniqueness)
                    cursor.execute("SELECT 1 FROM pokemon WHERE id = ?", (pokemon_id,))
                    pokemon_exists = cursor.fetchone() is not None

                    if not pokemon_exists:
                        pokemon_data = self.fetch_pokemon_data(pokemon_url)
                        if pokemon_data:
                            logging.info(f"Fetched Pokémon: {pokemon_data[1]} (ID: {pokemon_data[0]})")
                            self.insert_pokemon(pokemon_data)

                offset += batch_size
                time.sleep(1)  # Introduce a delay between batch requests

            else:
                print(f"Failed to fetch data. Status code: {response.status_code}")
                break  # Stop fetching if there's an error
    def get_all_pokemon(self):
        """Fetches all Pokémon from the database."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM pokemon ORDER BY id")
            return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Error fetching all Pokémon: {e}")
            return []  # Return an empty list in case of error

    def get_pokemon_by_id(self, pokemon_id):
        """Fetches a Pokémon by its ID from the database.
        If not found in the database, fetches from PokeAPI and inserts into the database.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM pokemon WHERE id = ?", (pokemon_id,))
            pokemon = cursor.fetchone()
            if pokemon:
                return pokemon

            # Fetch from PokeAPI if not in database
            pokemon_url = f"{config.POKEAPI_BASE_URL}pokemon/{pokemon_id}"
            pokemon_data = self.fetch_pokemon_data(pokemon_url)
            if pokemon_data:
                self.insert_pokemon(pokemon_data)
                return pokemon_data
            else:
                return None

        except sqlite3.Error as e:
            logging.error(f"Error fetching Pokémon by ID {pokemon_id}: {e}")
            return None

    def update_favorite_status(self, pokemon_id, is_favorite):
        """Updates the favorite status of a Pokémon."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE pokemon SET is_favorite = ? WHERE id = ?", (is_favorite, pokemon_id))
            self.conn.commit()
            logging.info(f"Updated favorite status for Pokémon {pokemon_id} to {is_favorite}")
        except sqlite3.Error as e:
            logging.error(f"Error updating favorite status for Pokémon {pokemon_id}: {e}")

    def close_connection(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            logging.info("Database connection closed.")


if __name__ == '__main__':
    data_manager = PokemonDataManager()
    data_manager.populate_database()
    data_manager.close_connection()