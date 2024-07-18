from dash import Dash, dcc, html, Input, Output, State, dash_table
from nba_api.stats.endpoints import commonallplayers, playercareerstats
import pandas as pd
import matplotlib.pyplot as plt
import base64
from io import BytesIO

# Define the functions
def get_player_data(firstlast):
    all_players = commonallplayers.CommonAllPlayers(is_only_current_season=0).get_data_frames()[0]
    player = all_players[all_players['DISPLAY_FIRST_LAST'] == firstlast]
    if player.empty:
        return pd.DataFrame()
    player_id = player['PERSON_ID'].iloc[0]
    career = playercareerstats.PlayerCareerStats(player_id=player_id)
    career_data = career.get_data_frames()[0]
    return career_data

def get_player_pga_visualization(firstlast):
    all_players = commonallplayers.CommonAllPlayers(is_only_current_season=0).get_data_frames()[0]
    player = all_players[all_players['DISPLAY_FIRST_LAST'] == firstlast]
    if player.empty:
        return "No player found with the name {}. Check for a misspelling.".format(firstlast)
    player_id = player['PERSON_ID'].iloc[0]
    career = playercareerstats.PlayerCareerStats(player_id=player_id)
    career_data = career.get_data_frames()[0]
    career_data['Year'] = career_data.reset_index().index + 1
    career_data['PRA/G'] = (career_data['PTS'] + career_data['AST'] + career_data['REB']) / career_data['GP']
    x = career_data['Year']
    y1 = career_data['PRA/G']
    plt.figure(figsize=(10, 6))
    plt.plot(x, y1, marker='o', linestyle='-')
    plt.xlabel('Year')
    plt.ylabel('PRA/G')
    plt.title('Points + Rebounds + Assists Per Game')
    plt.grid(True)
    plt.tight_layout()
    img = BytesIO()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode()

def avg_countingstats_comparison_tool(*players):
    all_players = commonallplayers.CommonAllPlayers(is_only_current_season=0).get_data_frames()[0]
    comparison_data = []
    for p in players:
        player1 = all_players[all_players['DISPLAY_FIRST_LAST'] == p]
        if player1.empty:
            return f"No player found with the name {p}. Check for a misspelling."
        player_id1 = player1['PERSON_ID'].iloc[0]
        career1 = playercareerstats.PlayerCareerStats(player_id=player_id1)
        career_data1 = career1.get_data_frames()[0]
        career_filtered1 = career_data1[['PTS', 'REB', 'AST', 'STL', 'BLK', 'GP']]
        total_sum1 = career_filtered1[['PTS', 'REB', 'AST', 'STL', 'BLK']].sum()
        total_gp1 = career_filtered1['GP'].sum()
        avg_stats1 = total_sum1 / total_gp1
        comparison_data.append(avg_stats1)
    comparison_df = pd.DataFrame(comparison_data, index=players).transpose()
    comparison_df.reset_index(inplace=True)
    comparison_df.rename(columns={'index': 'Stat'}, inplace=True)
    return comparison_df

# Initialize the Dash app
app = Dash(__name__)
server = app.server

# Define the layout of the app
app.layout = html.Div([
    html.Div([
        html.Img(src='/assets/nbalogo.png', style={'width': '70px', 'height': '50px', 'margin-left': '0.1px'}),
        html.H1('NBA Statistics Tool')],
        style={'display': 'flex', 'align-items': 'center'}),
    html.P("This Dashboard allows you to find and compare career stats of NBA players quickly and efficiently. The dashboard is connected to the NBA API found here (https://github.com/swar/nba_api)"),

    # Section for get_player_data
    html.Div([
        html.H3("Getting a Player's Career Stats"),
        html.P("Enter a player name to get their career statistics as a table."),
        dcc.Input(
            id='input-player-name',
            type='text',
            placeholder='Enter player name',
            style={'width': '50%'}
        ),
        html.Button('Submit', id='submit-button-player-data', n_clicks=0),
        dash_table.DataTable(id='player-data-table')
    ]),
    
    # Section for get_player_pga_visualization
    html.Div([
        html.H3("Visualizing Points + Rebounds + Assists Over Time"),
        html.P("Enter a player name to get a visualization of their Points + Rebounds + Assists Per Game over their career."),
        dcc.Input(
            id='input-player-name-pga',
            type='text',
            placeholder='Enter player name',
            style={'width': '50%'}
        ),
        html.Button('Submit', id='submit-button-player-pga', n_clicks=0),
        html.Img(id='player-pga-visualization')
    ]),
    
    # Section for avg_countingstats_comparison_tool
    html.Div([
        html.H3("Comparing Per Career Averages Counting Stats of Multiple Players"),
        html.P("Enter multiple player names (comma-separated) to compare their average counting stats (PTS, REB, AST, STL, BLK)."),
        dcc.Input(
            id='input-player-names-comparison',
            type='text',
            placeholder='Enter player names (comma-separated)',
            style={'width': '50%'}
        ),
        html.Button('Submit', id='submit-button-stats-comparison', n_clicks=0),
        dash_table.DataTable(id='stats-comparison-table')
    ]),
])

# Define the callback to update the player data table
@app.callback(
    Output('player-data-table', 'data'),
    Output('player-data-table', 'columns'),
    Input('submit-button-player-data', 'n_clicks'),
    State('input-player-name', 'value')
)
def update_player_data(n_clicks, value):
    if n_clicks > 0 and value:
        data = get_player_data(value)
        if data.empty:
            return [], []
        columns = [{"name": i, "id": i} for i in data.columns]
        data = data.to_dict('records')
        return data, columns
    return [], []

# Define the callback to update the player PGA visualization
@app.callback(
    Output('player-pga-visualization', 'src'),
    Input('submit-button-player-pga', 'n_clicks'),
    State('input-player-name-pga', 'value')
)
def update_player_pga_visualization(n_clicks, value):
    if n_clicks > 0 and value:
        img_base64 = get_player_pga_visualization(value)
        if img_base64.startswith("No player found"):
            return ''
        return 'data:image/png;base64,{}'.format(img_base64)
    return ''

# Define the callback to update the stats comparison table
@app.callback(
    Output('stats-comparison-table', 'data'),
    Output('stats-comparison-table', 'columns'),
    Input('submit-button-stats-comparison', 'n_clicks'),
    State('input-player-names-comparison', 'value')
)
def update_stats_comparison(n_clicks, value):
    if n_clicks > 0 and value:
        player_names = [name.strip() for name in value.split(',')]
        comparison_df = avg_countingstats_comparison_tool(*player_names)
        if isinstance(comparison_df, str):  # Check if the function returned an error message
            return [], []
        columns = [{"name": i, "id": i} for i in comparison_df.columns]
        data = comparison_df.to_dict('records')
        return data, columns
    return [], []

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
