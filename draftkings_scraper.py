from bs4 import BeautifulSoup
import requests as r
import pandas as pd
import numpy as np
from tqdm import tqdm


class DraftKingsScraper:

    def __init__(self, url, sport):
        self.url = url
        self.sport = sport
    
    # Initializes BeautifulSoup object
    def makeSoup(self, suffix):
        try:
            # print("Attempting to make soup.")
            response = r.get(self.url + suffix)
            self.soup = BeautifulSoup(response.text, 'html.parser')
            # print("Soup successfully made.")
            return self.soup
        except Exception as e:
            print(e)

    # Returns an array of arrays containing DraftKings player prop data
    def generateData(self):
        print("    Generating DK data")
        dk_df = pd.DataFrame({"Player": [], "Type": [], "O/U": [], "DK Line": [], "Odds": [], "Percentage": []})
        url_suffixes = ["points", "rebounds", "assists", "threes", "blocks/steals&subcategory=blocks-", "blocks/steals&subcategory=steals-", "blocks/steals&subcategory=steals-%2B-blocks"]
        types = ['PTS', 'REB', "AST", '3PT', 'BLK', 'STL', "BLK+STL"]

        # print("Attempting to generate CSV.")
        for i in tqdm(range(len(url_suffixes))):
            suffix = url_suffixes[i]
            play_type = types[i]

            try:
                # print(f"Scraping {self.url + suffix}...")
                soup = self.makeSoup(suffix)
                name_tags = soup.find_all(class_="sportsbook-row-name")
                label_tags = soup.find_all(class_="sportsbook-outcome-cell__label")
                line_tags = soup.find_all(class_="sportsbook-outcome-cell__line")
                odd_tags = soup.find_all(class_="sportsbook-odds")
                names = np.repeat(list(map(lambda tag: tag.text, name_tags)), 2)
                labels = list(map(lambda tag: tag.text, label_tags))
                lines = list(map(lambda tag: tag.text, line_tags))
                odds = list(map(lambda tag: tag.text, odd_tags))
                int_odds = [int(odd.replace("−", "-")) for odd in odds]
                percentages = [round(((int_odd / (int_odd - 100)) * 100), 2) if int_odd < 0 else round(((100 / (int_odd + 100)) * 100), 2) for int_odd in int_odds]
                # print(len(names))
                # print(len(labels))
                # print(len(lines))
                # print(len(odds))
                # print(len(percentages))
                dk_concat_df = pd.DataFrame({"Player": names, "Type": play_type, "O/U": labels, "DK Line": lines, "Odds": odds, "Percentage": percentages})
                dk_df = pd.concat([dk_df, dk_concat_df], ignore_index=True)
                # print("CSV successfully made.")
            except Exception as e:
                print(e)
                return None

        print("    Success")
        dk_df.sort_values('Percentage', ascending=False, inplace=True)
        return dk_df.values.tolist()