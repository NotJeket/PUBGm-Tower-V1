import dash,json,requests
import pandas as pd
from dash import dcc, html
from dash.dependencies import Output, Input

external_stylesheets = ['assets/style.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, serve_locally=True)

def get_data():
    # API endpoints
    all_info_url = "http://127.0.0.1:5000/data1"
    team_info_url = "http://127.0.0.1:5000/data2"
    # Make API calls and parse the JSON responses
    all_info_response = requests.get(all_info_url)
    player_data = all_info_response.json()["allinfo"]["TotalPlayerList"]
    team_info_response = requests.get(team_info_url)
    team_data = team_info_response.json()["teamInfoList"]
    # Update killNum and rank for each team in teams dictionary
    teams = {}
    for team in team_data:
        teams[team["teamName"]] = {"killNum": team["killNum"], "rank": None, "liveState": [], "isOutsideBlueCircle": False}
    for player in player_data:
        teams[player["teamName"]]["liveState"].append(player["liveState"])
        teams[player["teamName"]]["rank"] = player["rank"]
        if player["isOutsideBlueCircle"]:
            teams[player["teamName"]]["isOutsideBlueCircle"] = True
    df = pd.DataFrame(teams)
    df = df.transpose()
    df["logo"] = df.index.map(lambda x: f"/assets/logos/{x}.png")
    df["liveStateCount"] = df["liveState"].map(lambda x: len([p for p in x if p in [0, 1, 2, 3]]))
    # Sort the DataFrame first by the number of players alive, then by killNum in descending order
    df = df.sort_values(by=["liveStateCount", "killNum"], ascending=[False, False])
    df["background_image"] = df.apply(
        #test 2 in case of separate picture\/
        lambda row: ("assets/test2.png", "pulsing", "assets/test2.png") if row["isOutsideBlueCircle"] else (
        "assets/test.png", "", "assets/test.png"), axis=1)
    return df

app.layout = html.Div(
    [
        html.Table(
            [
                html.Tbody(id="table-body"),
            ],
            style={"border-collapse": "collapse","border": "none","margin-left": "0","margin-right": "5px"}
        ),
        dcc.Interval(
            id='interval-component',
            interval=2*1000, # update every 5 seconds
            n_intervals=0
        ),
    ],
    className="animate-bottom-container"
)

@app.callback(Output("table-body", "children"), [Input("interval-component", "n_intervals")])
def update_table(n):
    teams_sorted = get_data()
    rows = []
    dead_rows = []
    # Create the legend row
    legend_row = html.Tr([
        html.Td(""),
        html.Td("MATCH RANKINGS", className="legend-name"),
        html.Td("PTS", className="legend-pts"),
        html.Td("ALIVE", className="legend-status")
    ], className="legend-row")
    rows.append(legend_row)
    for team_name, team_data in teams_sorted.iterrows():
        if all(live_state > 3 for live_state in team_data["liveState"]):
            # The team is dead, so display the rank instead of the logo
            logo = html.Td(str(team_data["rank"]), className="team-rank")
        else:
            # The team is alive, so display the logo
            logo = html.Td(html.Img(src=team_data["logo"], style={"height": "35px", "padding": "5px","padding-right":"15px"}),
                           className="team-logo")
        kill_num = html.Td(str(team_data["killNum"]), className="team-pts")
        team_name = html.Td(team_name, className="team-name")
        live_state_icons = []
        is_dead = all(live_state > 3 for live_state in team_data["liveState"])
        for live_state in team_data["liveState"]:
            if live_state == 0 or live_state == 1 or live_state == 2 or live_state == 3:
                icon = html.Img(src="assets/poze/alive.png", className="team-status")
            elif live_state == 4:
                icon = html.Img(src="assets/poze/knock.png", className="team-status")
            else:
                icon = html.Img(src="assets/poze/dead.png", className="team-status")
            live_state_icons.append(
                html.Td(icon, className="team-status"))
        # Set the background image for the row based on the team name
        background_image = team_data['background_image'][0]
        if team_data['background_image'][1] == "pulsing":
            background_image = team_data['background_image'][2]
        row_style = {
            "background-image": f"url({background_image})",
            "background-size": "cover",
            "background-repeat": "no-repeat",
            "background-position": "center"
        }
        if is_dead:
            row_style["filter"] = "grayscale(100%)"
        row_class_name = "team-row dead-row" if is_dead else "team-row" + " " + team_data["background_image"][1]
        row = html.Tr(
            [
                html.Td(logo),
                team_name,
                kill_num,
                html.Td(live_state_icons),
            ],
            className=row_class_name,
            id=f"row-{team_name}",
            style=row_style,
        )
        rows.append(row)
        if is_dead:
            dead_rows.append(row)
    # Move dead rows to the bottom of the table and add fade-in-down animation
    for i, row in enumerate(dead_rows):
        row_id = f"row-{teams_sorted.index[-(i + 1)]}"
        row.className = "animate__animated animate__fadeInDown team-row dead-row"
        if row_id != row.id:
            row.id = row_id
            rows.remove(row)
            rows.append(row)
    table_body = html.Tbody(rows, className="team-row")
    return table_body


if __name__ == "__main__":
    app.run_server(debug=False, port=8050, host="127.0.0.1")