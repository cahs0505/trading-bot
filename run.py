from MainBot import MainBot
from Strategy.SpreadStrategy import SpreadStrategy
import time

def main():

    app = MainBot ()
    app.add_strategy(SpreadStrategy())
    app.start()


if __name__ == "__main__":
    main()