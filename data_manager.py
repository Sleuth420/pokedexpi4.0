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
        self.create_berries_table()
        self.create_evolutions_table()

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
    def get_all_pokemon(self, search_term=None, limit=None, offset=0):
        """Fetches all Pokémon from the database, optionally filtered by search_term
        and paginated using limit and offset."""
        try:
            cursor = self.conn.cursor()
            if search_term:
                query = "SELECT * FROM pokemon WHERE name LIKE ? ORDER BY id"
                if limit:
                    query += " LIMIT ? OFFSET ?"
                    params = ('%' + search_term + '%', limit, offset)
                else:
                    params = ('%' + search_term + '%',)
            else:
                query = "SELECT * FROM pokemon ORDER BY id"
                if limit:
                    query += " LIMIT ? OFFSET ?"
                    params = (limit, offset)
                else:
                    params = ()

            cursor.execute(query, params)
            return cursor.fetchall()

        except sqlite3.Error as e:
            logging.error(f"Error fetching all Pokémon: {e}")
        return []

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


    def create_berries_table(self):
        """Creates the berries table in the database if it doesn't exist."""
        sql_create_berries_table = """
                    CREATE TABLE IF NOT EXISTS berries (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        growth_time INTEGER,
                        max_harvest INTEGER,
                        natural_gift_power INTEGER,
                        size INTEGER,
                        smoothness INTEGER,
                        soil_dryness INTEGER,
                        firmness TEXT,
                        flavors TEXT 
                    );
                    """
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql_create_berries_table)
            logging.info("Berries table created or already exists.")
        except sqlite3.Error as e:
            logging.error(f"Error creating berries table: {e}")


    def fetch_berry_data(self, berry_url):
        """Fetches berry data from the PokeAPI."""
        try:
            response = http.get(berry_url)
            response.raise_for_status()

            berry_data = response.json()

            # Extract relevant berry data
            id = berry_data['id']
            name = berry_data['name']
            growth_time = berry_data['growth_time']
            max_harvest = berry_data['max_harvest']
            natural_gift_power = berry_data['natural_gift_power']
            size = berry_data['size']
            smoothness = berry_data['smoothness']
            soil_dryness = berry_data['soil_dryness']
            firmness = berry_data['firmness']['name']
            flavors = ', '.join([f["flavor"]["name"] for f in berry_data['flavors']])

            return (id, name, growth_time, max_harvest, natural_gift_power, size, smoothness,
                    soil_dryness, firmness, flavors)

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching berry data from {berry_url}: {e}")
            return None


    def insert_berry(self, berry):
        """Inserts a new berry into the berries table."""
        sql = """
                    INSERT INTO berries (id, name, growth_time, max_harvest, natural_gift_power, size, 
                                         smoothness, soil_dryness, firmness, flavors)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
        try:
            cur = self.conn.cursor()
            cur.execute(sql, berry)
            self.conn.commit()
            logging.info(f"Inserted Berry with ID {cur.lastrowid}")
            return cur.lastrowid
        except sqlite3.Error as e:
            logging.error(f"Error inserting berry: {e}")


    def populate_berries_table(self, num_berries=None):
        """Populates the database with berry data."""
        if num_berries is None:
            # Fetch the total number of berries from the API
            response = http.get(f"{config.POKEAPI_BASE_URL}berry")
            response.raise_for_status()
            num_berries = response.json()['count']

        for berry_id in range(1, num_berries + 1):
            berry_url = f"{config.POKEAPI_BASE_URL}berry/{berry_id}"
            berry_data = self.fetch_berry_data(berry_url)
            if berry_data:
                self.insert_berry(berry_data)
                logging.info(f"Fetched and inserted berry: {berry_data[1]} (ID: {berry_data[0]})")
            time.sleep(0.2)  # Add a small delay to avoid overwhelming the API


    def create_evolutions_table(self):
        """Creates the evolutions table in the database if it doesn't exist."""
        sql_create_evolutions_table = """
                    CREATE TABLE IF NOT EXISTS evolutions (
                        id INTEGER PRIMARY KEY,
                        pokemon_id INTEGER,
                        evolves_to_id INTEGER,
                        trigger TEXT, 
                        level INTEGER,
                        item TEXT,
                        FOREIGN KEY(pokemon_id) REFERENCES pokemon(id),
                        FOREIGN KEY(evolves_to_id) REFERENCES pokemon(id)
                    );
                    """
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql_create_evolutions_table)
            logging.info("Evolutions table created or already exists.")
        except sqlite3.Error as e:
            logging.error(f"Error creating evolutions table: {e}")


    def fetch_evolution_data(self, pokemon_id):
        """Fetches evolution chain data for a given Pokemon from the PokeAPI."""
        try:
            # Get the Pokemon's species information
            species_url = f"{config.POKEAPI_BASE_URL}pokemon-species/{pokemon_id}/"
            species_response = http.get(species_url)
            species_response.raise_for_status()
            species_data = species_response.json()

            # Get the evolution chain URL
            evolution_chain_url = species_data['evolution_chain']['url']

            # Fetch the evolution chain data
            evolution_chain_response = http.get(evolution_chain_url)
            evolution_chain_response.raise_for_status()
            evolution_chain_data = evolution_chain_response.json()

            # Parse the evolution chain data
            evolutions = []
            self._parse_evolution_chain(evolution_chain_data['chain'], evolutions)

            return evolutions

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching evolution data for Pokemon {pokemon_id}: {e}")
            return []

    def _parse_evolution_chain(self, chain_link, evolutions):
        """Recursively parses an evolution chain link and extracts evolution data."""
        pokemon_id = int(chain_link['species']['url'].split('/')[-2])

        for evolution_detail in chain_link['evolves_to']:
            evolves_to_id = int(evolution_detail['species']['url'].split('/')[-2])
            trigger = evolution_detail['evolution_details'][0]['trigger']['name']
            level = evolution_detail['evolution_details'][0].get('min_level')

            # Check if evolution_details[0] exists before accessing 'item'
            if evolution_detail['evolution_details'][0]:
                item = evolution_detail['evolution_details'][0].get('item', {}).get('name')
            else:
                item = None  # Set item to None if it doesn't exist

            evolutions.append((pokemon_id, evolves_to_id, trigger, level, item))

            self._parse_evolution_chain(evolution_detail, evolutions)


    def insert_evolution(self, evolution):
        """Inserts a new evolution into the evolutions table."""
        sql = """
                    INSERT INTO evolutions (pokemon_id, evolves_to_id, trigger, level, item)
                    VALUES (?, ?, ?, ?, ?)
        """
        try:
            cur = self.conn.cursor()
            cur.execute(sql, evolution)
            self.conn.commit()
            logging.info(f"Inserted Evolution: {evolution[0]} -> {evolution[1]}")
        except sqlite3.Error as e:
            logging.error(f"Error inserting evolution: {e}")

    def populate_evolutions_table(self):
        """Populates the database with evolution data for all Pokemon."""
        all_pokemon = self.get_all_pokemon()
        for pokemon in all_pokemon:
            pokemon_id = pokemon[0]
            evolution_data = self.fetch_evolution_data(pokemon_id)
            for evolution in evolution_data:
                self.insert_evolution(evolution)
            time.sleep(0.2)

    # Add other methods as needed for fetching/filtering berries and evolutions
    def get_all_berries(self, search_term=None):
        """Fetches all berries from the database, optionally filtered by search_term."""
        try:
            cursor = self.conn.cursor()
            if search_term:
                cursor.execute("SELECT * FROM berries WHERE name LIKE ? ORDER BY id", ('%' + search_term + '%',))
            else:
                cursor.execute("SELECT * FROM berries ORDER BY id")
            return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Error fetching all berries: {e}")
            return []

    def get_berry_by_id(self, berry_id):
        """Fetches a berry by its ID from the database."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM berries WHERE id = ?", (berry_id,))
            return cursor.fetchone()
        except sqlite3.Error as e:
            logging.error(f"Error fetching berry by ID {berry_id}: {e}")
            return None

    def get_evolution_chain_for_pokemon(self, pokemon_id):
        """Fetches the evolution chain for a given Pokemon from the database."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                WITH RECURSIVE evolution_chain(pokemon_id, evolves_to_id, trigger, level, item) AS (
                    SELECT pokemon_id, evolves_to_id, trigger, level, item
                    FROM evolutions
                    WHERE pokemon_id = ?
                    UNION ALL
                    SELECT e.pokemon_id, e.evolves_to_id, e.trigger, e.level, e.item
                    FROM evolutions e
                    JOIN evolution_chain ec ON e.pokemon_id = ec.evolves_to_id
                )
                SELECT * FROM evolution_chain;
            """, (pokemon_id,))
            return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Error fetching evolution chain for Pokemon {pokemon_id}: {e}")
            return []


if __name__ == '__main__':
    data_manager = PokemonDataManager()
    data_manager.populate_database()
    data_manager.populate_berries_table()
    data_manager.populate_evolutions_table()
    data_manager.close_connection()
