import gspread
import time
import pandas as pd
from tqdm import tqdm
import datetime
from gspread_formatting  import color, textFormat, cellFormat, format_cell_ranges, format_cell_range
from draftkings_scraper import DraftKingsScraper
from prizepicks_scraper import PrizePicksNBAScraper
from plyer import notification


old_props = []

def update_DK_data(dk_wks):
    print("    Updating DK worksheet")
    dk_wks.format("A:Z", {
        "backgroundColor": {
            "red": 1.0,
            "green": 1.0,
            "blue": 1.0
        },
        "horizontalAlignment": "LEFT",
        "textFormat": {
            "foregroundColor": {
                "red": 0.0,
                "green": 0.0,
                "blue": 0.0
            },
            "fontSize": 11,
            "bold": False
        }
    })
    dk_scraper = DraftKingsScraper("https://sportsbook.draftkings.com/leagues/basketball/nba?category=player-", "NBA")
    dk_data = dk_scraper.generateData()
    if dk_data is None:
        return None
    dk_wks.delete_rows(3, dk_wks.row_count)
    dk_wks.clear()
    dk_wks.insert_row(['Player', 'Type', 'Label', 'Line', 'Odd', 'Percentage'], index=1)
    dk_wks.insert_rows(dk_data, row=2)
    dk_wks.format(f"A1:F1", {"backgroundColor": {"red": 0,"green": 0,"blue": 0}, "textFormat": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "fontSize": 11, "bold": True}})
    print("    Success")
    return dk_data

def update_PP_data(pp_wks):
    print("    Updating PP worksheet")
    pp_wks.format("A:Z", {
        "backgroundColor": {
            "red": 1.0,
            "green": 1.0,
            "blue": 1.0
        },
        "horizontalAlignment": "LEFT",
        "textFormat": {
            "foregroundColor": {
                "red": 0.0,
                "green": 0.0,
                "blue": 0.0
            },
            "fontSize": 11,
            "bold": False
        }
    })
    pp_data = pp_scraper.generateData()
    if pp_data is None:
        return None
    pp_wks.delete_rows(3, pp_wks.row_count)
    pp_wks.clear()
    pp_wks.insert_row(['Player', 'Line', 'Type'], index=1)
    pp_wks.insert_rows(pp_data, row=2)
    pp_wks.format(f"A1:C1", {"backgroundColor": {"red": 0,"green": 0,"blue": 0}, "textFormat": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "fontSize": 11, "bold": True}})
    print("    Success")
    return pp_data


def calculate_weighted_odds(ou, dk_odds, dk_line, pp_line, play_type):
    dk_odds = int(dk_odds.replace("−", "-"))
    dk_line = float(dk_line)
    pp_line = float(pp_line)
    offset = 40
    if play_type == "PTS":
        offset = 30
    if dk_line == pp_line:
        return dk_odds
    else:
        if ou == 'O':
            if pp_line < dk_line:
                return dk_odds - (offset) * (dk_line - pp_line)
            else:
                return dk_odds + (offset) * (pp_line - dk_line)
        elif ou == 'U':
            if pp_line < dk_line:
                return dk_odds + (offset + 10) * (dk_line - pp_line)
            else:
                return dk_odds - (offset + 10) * (pp_line - dk_line)
        

def generate_EV_data(dk_data, pp_data):
    print("    Generating EV data")
    ev_data = []
    dk_df = pd.DataFrame(columns=["Player", "Type", "O/U", "DK Line", "Odds", "Percentage"], data=dk_data)
    weighted_odds = []
    weighted_percentages = []
    for i in tqdm(range(len(pp_data))):
        row = pp_data[i]
        player = row[0]
        line = row[1]
        play_type = row[2]
        match = dk_df[(dk_df['Player'] == player) & (dk_df['Type'] == play_type)].values.tolist()
        if len(match):
            match = match[0]
            ev_data.append([match[0], match[1], match[2], match[4], match[5], match[3], line])
            weighted_odd = calculate_weighted_odds(match[2], match[4], match[3], line, play_type)
            weighted_odds.append(weighted_odd)
            weighted_percentages.append(round(((weighted_odd / (weighted_odd - 100)) * 100), 2) if weighted_odd < 0 else round(((100 / (weighted_odd + 100)) * 100), 2))
    ev_df = pd.DataFrame(columns=["Player", "Type", "O/U", "Odds", "Percentage", "DK Line", "PP Line"], data=ev_data)
    ev_df['Weighted Odds'] = weighted_odds
    ev_df['Weighted Percentage'] = weighted_percentages
    ev_df.sort_values('Weighted Percentage', ascending=False, inplace=True)
    print("    Success")
    return ev_df.values.tolist()


def update_EV_data(ev_wks, ev_data):
    print("    Updating EV worksheet")
    ev_wks.delete_rows(3, ev_wks.row_count)
    ev_wks.clear()
    ev_wks.format("A:Z", {
        "backgroundColor": {
            "red": 1.0,
            "green": 1.0,
            "blue": 1.0
        },
        "horizontalAlignment": "LEFT",
        "textFormat": {
            "foregroundColor": {
                "red": 0.0,
                "green": 0.0,
                "blue": 0.0
            },
            "fontSize": 11,
            "bold": False
        }
    })
    ev_wks.insert_row(["Player", "Type", "O/U", "Odds", "Percentage", "DK Line", "PP Line", "Weighted Odds (BETA)", "Weighted Percentage (BETA)"], index=1)
    ev_wks.insert_rows(ev_data, row=2)
    highlight_ev_rows(ev_wks, ev_data)
    print("    Success")


def highlight_ev_rows(ev_wks, ev_data):
    great_rows = []
    good_rows = []
    curr_props = []
    global old_props
    for i in range(len(ev_data)):
        if (ev_data[i][5] == ev_data[i][6]) and (ev_data[i][4] > 59):
            great_rows.append(i + 2)
            curr_props.append((ev_data[i][0], ev_data[i][1]))
        elif ev_data[i][8] > 59:
            good_rows.append(i + 2)
            curr_props.append((ev_data[i][0], ev_data[i][1]))
    curr_props = sorted(curr_props)
    if curr_props != old_props:
        notification.notify(
            title = 'EV Tool',
            message = 'New prop found!',
            app_icon = None,
            timeout = 20,
        )
        old_props = curr_props
    for row in great_rows:
        ev_wks.format(f"A{row}:I{row}", {"backgroundColor": {"red": 0.0,"green": 0.9,"blue": 0.0}, "textFormat": {"fontSize": 11, "bold": True}})
    for row in good_rows:
        ev_wks.format(f"A{row}:I{row}", {"backgroundColor": {"red": 0.8,"green": 1.0,"blue": 0.0}, "textFormat": {"fontSize": 11, "bold": True}})
    ev_wks.format(f"A1:I1", {"backgroundColor": {"red": 0,"green": 0,"blue": 0}, "textFormat": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "fontSize": 11, "bold": True}})


def generate_timestamp():
    now = datetime.datetime.now()
    return now, now.strftime("%Y-%m-%d %H:%M:%S")


def update_timestamps(current_time, next_run_time, wks):
    wks.update_cell(2, 11, "Last Updated:")
    wks.update_cell(2, 12, current_time)
    wks.update_cell(3, 11, "Next Updated At:")
    wks.update_cell(3, 12, next_run_time)


def update_all_worksheet_timestamps(current_timestamp, next_timestamp, pp_wks, dk_wks, ev_wks):
    update_timestamps(current_timestamp, next_timestamp, dk_wks)
    update_timestamps(current_timestamp, next_timestamp, pp_wks)
    update_timestamps(current_timestamp, next_timestamp, ev_wks)


def run(dk_wks, pp_wks, ev_wks):
    process_start_time = time.time()
    dk_data = update_DK_data(dk_wks)
    if dk_data is None:
        return 100
    pp_data = update_PP_data(pp_wks)
    if pp_data is None:
        return 100
    ev_data = generate_EV_data(dk_data, pp_data)
    update_EV_data(ev_wks, ev_data)
    process_end_time = time.time() 
    process_duration = process_end_time - process_start_time
    return process_duration


if __name__ == "__main__":
    
    try:
        pp_scraper = PrizePicksNBAScraper()
        pp_scraper.startDriver()
        if pp_scraper.league != "NBA":
            print("No PrizePicks NBA Props Currently.")
            quit()

        sa = gspread.service_account(".\config\gspread-auth.json") 
        sh = sa.open("TL EV Tool")
        dk_wks = sh.worksheet("DK Data")
        pp_wks = sh.worksheet("PP Data")
        ev_wks = sh.worksheet("EV Tool")

        while True:
            print("Starting process...")
            process_duration = run(dk_wks, pp_wks, ev_wks)
            sleep_duration = 120 - process_duration
            print(f"Process duration: {process_duration} seconds")
            print(f"Next run in {sleep_duration} seconds.")
            print("")
            
            current_datetime, current_timestamp = generate_timestamp()
            next_timestamp = (current_datetime + datetime.timedelta(0, sleep_duration)).strftime("%Y-%m-%d %H:%M:%S")
            update_all_worksheet_timestamps(current_timestamp, next_timestamp, pp_wks, dk_wks, ev_wks)

            try:
                time.sleep(sleep_duration)
            except ValueError:
                time.sleep(20)
    except KeyboardInterrupt:
        print("EV Tool shutting down.")
        quit()