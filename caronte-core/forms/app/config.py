from dotenv import dotenv_values

def load_config(filename = '.env'):
    """
    Import the values contained in the .env file
    """

    config = dotenv_values(filename)

    return config

if __name__ == '__main__':
    config = load_config('.env')