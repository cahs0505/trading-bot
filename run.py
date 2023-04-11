from MainBot import MainBot
from Strategy.SpreadStrategy import SpreadStrategy
import time

def main():

    app = MainBot ()
    app.add_strategy(SpreadStrategy("spread1"))
    app.add_strategy(SpreadStrategy("spread2"))
    app.start()


if __name__ == "__main__":
    main()