import time
import threading
import requests
import os
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room

# ─────────────────────────────────────────────────────────────────────────────
# Flask + SocketIO Setup
# ─────────────────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'secret-key-change-in-production')
# Use threading mode for Python 3.12+ compatibility (eventlet doesn't work with Python 3.12+)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

POLL_INTERVAL = 10  # seconds
matches = {}
poll_threads = {}
poll_lock = threading.Lock()


# ─────────────────────────────────────────────────────────────────────────────
# REAL SPORTS API FETCHERS  (ESPN — No API key needed)
# ─────────────────────────────────────────────────────────────────────────────
ESPN_FOOTBALL_URL = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard"
ESPN_CRICKET_URL = "https://site.api.espn.com/apis/site/v2/sports/cricket/scoreboard"

def fetch_football_data():
    """Fetch real football match data from ESPN."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        res = requests.get(ESPN_FOOTBALL_URL, timeout=10, headers=headers)
        res.raise_for_status()
        data = res.json()
        print(f"API Response: Status {res.status_code}, Events: {len(data.get('events', []))}")
        return data
    except requests.exceptions.Timeout:
        print("Error: API request timed out")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"Error: HTTP {e.response.status_code} - {e.response.reason}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching football data: {e}")
        return None
    except ValueError as e:
        print(f"Error parsing JSON response: {e}")
        return None


def fetch_cricket_data():
    """Fetch real cricket match data from ESPN."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        res = requests.get(ESPN_CRICKET_URL, timeout=10, headers=headers)
        res.raise_for_status()
        data = res.json()
        print(f"Cricket API Response: Status {res.status_code}, Events: {len(data.get('events', []))}")
        return data
    except requests.exceptions.Timeout:
        print("Error: Cricket API request timed out")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"Error: HTTP {e.response.status_code} - {e.response.reason}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching cricket data: {e}")
        return None
    except ValueError as e:
        print(f"Error parsing JSON response: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Convert ESPN JSON → our internal state format
# ─────────────────────────────────────────────────────────────────────────────
def map_football_state(data):
    """
    Converts ESPN JSON → clean internal state:
    - teams
    - score
    - possession (if available)
    - status
    """
    if not data:
        print("Error: No data received from API")
        return None
        
    if "events" not in data:
        print(f"Error: 'events' key not found in API response. Keys: {list(data.keys())}")
        return None
        
    if len(data["events"]) == 0:
        print("Warning: No events found in API response (no matches currently available)")
        return None

    try:
        ev = data["events"][0]                     # first match
        if "competitions" not in ev or len(ev["competitions"]) == 0:
            print("Error: No competitions found in event")
            return None
            
        comp = ev["competitions"][0]
        if "competitors" not in comp:
            print("Error: No competitors found in competition")
            return None
            
        teams = comp["competitors"]
        
        if len(teams) < 2:
            print(f"Error: Not enough teams found ({len(teams)} teams)")
            return None
    except (KeyError, IndexError) as e:
        print(f"Error parsing ESPN data structure: {e}")
        import traceback
        traceback.print_exc()
        return None

    try:
        teamA = teams[0]["team"]["displayName"]
        teamB = teams[1]["team"]["displayName"]
    except (KeyError, IndexError) as e:
        print(f"Error extracting team names: {e}")
        return None

    # Get possession stats safely
    def get_possession(team_data):
        """Extract possession percentage from team statistics."""
        if "statistics" not in team_data or not team_data["statistics"]:
            return "0%"
        # Look for possession stat in statistics array
        for stat in team_data["statistics"]:
            if stat.get("name") == "possession" or stat.get("name") == "timeOfPossession":
                return stat.get("displayValue", "0%")
        # If not found, return first stat or default
        return team_data["statistics"][0].get("displayValue", "0%") if team_data["statistics"] else "0%"
    
    state = {
        "sport": "football",
        "last_updated": time.time(),
        "teams": [teamA, teamB],
        "score": {
            teamA: int(teams[0].get("score", 0)),
            teamB: int(teams[1].get("score", 0))
        },
        "status": comp.get("status", {}).get("type", {}).get("description", "Unknown"),
        "possession": {
            teamA: get_possession(teams[0]),
            teamB: get_possession(teams[1])
        }
    }

    return state


def map_cricket_state(data):
    """
    Converts ESPN Cricket JSON → clean internal state:
    - teams
    - score (runs, wickets, overs)
    - status
    """
    if not data:
        print("Error: No cricket data received from API")
        return None
        
    if "events" not in data:
        print(f"Error: 'events' key not found in cricket API response. Keys: {list(data.keys())}")
        return None
        
    if len(data["events"]) == 0:
        print("Warning: No cricket events found in API response (no matches currently available)")
        return None

    try:
        ev = data["events"][0]                     # first match
        if "competitions" not in ev or len(ev["competitions"]) == 0:
            print("Error: No competitions found in cricket event")
            return None
            
        comp = ev["competitions"][0]
        if "competitors" not in comp:
            print("Error: No competitors found in cricket competition")
            return None
            
        teams = comp["competitors"]
        
        if len(teams) < 2:
            print(f"Error: Not enough teams found ({len(teams)} teams)")
            return None
    except (KeyError, IndexError) as e:
        print(f"Error parsing ESPN cricket data structure: {e}")
        import traceback
        traceback.print_exc()
        return None

    try:
        teamA = teams[0]["team"]["displayName"]
        teamB = teams[1]["team"]["displayName"]
    except (KeyError, IndexError) as e:
        print(f"Error extracting cricket team names: {e}")
        return None

    # Get cricket innings data - ESPN cricket API structure
    def get_innings_data(team_data):
        """Extract innings information from team data."""
        # Try multiple ways to get score
        score = 0
        wickets = 0
        overs = "0.0"
        
        # Method 1: Direct score field
        if "score" in team_data:
            score = int(team_data.get("score", 0))
        
        # Method 2: From linescores array
        if "linescores" in team_data and team_data["linescores"]:
            for line in team_data["linescores"]:
                name = line.get("name", "").lower()
                value = line.get("value", 0)
                display_value = line.get("displayValue", "")
                
                if "run" in name or "score" in name:
                    try:
                        score = int(value) if value else 0
                    except:
                        score = 0
                elif "wicket" in name:
                    try:
                        wickets = int(value) if value else 0
                    except:
                        wickets = 0
                elif "over" in name:
                    overs = display_value or str(value) or "0.0"
        
        # Method 3: From statistics
        if "statistics" in team_data and team_data["statistics"]:
            for stat in team_data["statistics"]:
                name = stat.get("name", "").lower()
                value = stat.get("value", 0)
                display_value = stat.get("displayValue", "")
                
                if "run" in name or "score" in name:
                    try:
                        score = int(value) if value else score
                    except:
                        pass
                elif "wicket" in name:
                    try:
                        wickets = int(value) if value else wickets
                    except:
                        pass
                elif "over" in name:
                    overs = display_value or overs
        
        return {
            "runs": score,
            "wickets": wickets,
            "overs_balls": overs
        }
    
    teamA_data = get_innings_data(teams[0])
    teamB_data = get_innings_data(teams[1])
    
    # Create innings array for display
    current_innings = [teamA_data]
    
    state = {
        "sport": "cricket",
        "last_updated": time.time(),
        "teams": [teamA, teamB],
        "score": {
            teamA: teamA_data["runs"],
            teamB: teamB_data["runs"]
        },
        "status": comp.get("status", {}).get("type", {}).get("description", "Unknown"),
        "innings": current_innings,
        "wickets": {
            teamA: teamA_data["wickets"],
            teamB: teamB_data["wickets"]
        }
    }

    return state


# ─────────────────────────────────────────────────────────────────────────────
# POLLING LOOP (Runs every 10s, fetches real data)
# ─────────────────────────────────────────────────────────────────────────────
def poll_loop(match_id, sport="football"):
    print(f"Poll loop started for {match_id} (sport: {sport})")
    # Wait for initial fetch in subscribe handler to complete
    time.sleep(1)
    
    while True:
        try:
            if sport == "cricket":
                api_data = fetch_cricket_data()
                mapped = map_cricket_state(api_data)
            else:
                api_data = fetch_football_data()
                mapped = map_football_state(api_data)

            if mapped:
                matches[match_id] = mapped
                print(f"Match data updated for {match_id}: {mapped['teams'][0]} vs {mapped['teams'][1]}")

                if sport == "cricket":
                    socketio.emit("match:update", {
                        "id": match_id,
                        "sport": "cricket",
                        "raw": mapped,
                        "stats": {
                            "run_rate": "N/A",  # Calculate if needed
                            "top_scorer": {"name": "N/A", "runs": 0}
                        },
                        "last_updated": mapped["last_updated"]
                    }, room=match_id)
                else:
                    socketio.emit("match:update", {
                        "id": match_id,
                        "sport": "football",
                        "raw": mapped,
                        "stats": {
                            "possession": mapped["possession"],
                            "top_scorer": {"name": "N/A", "goals": "?"}
                        },
                        "last_updated": mapped["last_updated"]
                    }, room=match_id)
            else:
                print(f"No match data available for {match_id} (API may have no active matches)")

        except Exception as e:
            print(f"POLL ERROR for {match_id}: {e}")
            import traceback
            traceback.print_exc()

        time.sleep(POLL_INTERVAL)


# ─────────────────────────────────────────────────────────────────────────────
# Socket Events
# ─────────────────────────────────────────────────────────────────────────────
@socketio.on("match:subscribe")
def subscribe(data):
    match_id = data.get("match_id")
    sport = data.get("sport", "football")

    join_room(match_id)
    print(f"Client subscribed to {match_id} (sport: {sport})")

    # Create unique key for match_id + sport combination
    poll_key = f"{match_id}:{sport}"

    # start poller if not running
    with poll_lock:
        if poll_key not in poll_threads:
            print(f"Starting poll thread for {sport} data...")
            t = threading.Thread(target=poll_loop, args=(match_id, sport), daemon=True)
            poll_threads[poll_key] = t
            t.start()
            
            # Fetch data immediately instead of waiting for first poll interval
            print(f"Fetching initial {sport} data for {match_id}...")
            try:
                if sport == "cricket":
                    api_data = fetch_cricket_data()
                    mapped = map_cricket_state(api_data)
                else:
                    api_data = fetch_football_data()
                    mapped = map_football_state(api_data)
                
                if mapped:
                    matches[match_id] = mapped
                    print(f"Initial match data fetched for {match_id}: {mapped['teams'][0]} vs {mapped['teams'][1]}")
                    
                    if sport == "cricket":
                        socketio.emit("match:update", {
                            "id": match_id,
                            "sport": "cricket",
                            "raw": mapped,
                            "stats": {
                                "run_rate": "N/A",
                                "top_scorer": {"name": "N/A", "runs": 0}
                            },
                            "last_updated": mapped["last_updated"]
                        }, room=match_id)
                    else:
                        socketio.emit("match:update", {
                            "id": match_id,
                            "sport": "football",
                            "raw": mapped,
                            "stats": {
                                "possession": mapped["possession"],
                                "top_scorer": {"name": "N/A", "goals": "?"}
                            },
                            "last_updated": mapped["last_updated"]
                        }, room=match_id)
                else:
                    socketio.emit("match:update", {
                        "info": "No active matches found. Waiting for matches to become available...",
                        "id": match_id,
                        "sport": sport
                    }, room=match_id)
            except Exception as e:
                print(f"Error fetching initial data for {match_id}: {e}")
                import traceback
                traceback.print_exc()
                socketio.emit("match:update", {
                    "info": f"Error fetching match data: {str(e)}",
                    "id": match_id,
                    "sport": sport
                }, room=match_id)
        else:
            # Poll thread already running, just send current data if available
            print(f"Poll thread already running for {poll_key}, sending cached data")
            if match_id in matches:
                mapped = matches[match_id]
                current_sport = mapped.get("sport", sport)
                
                if current_sport == "cricket":
                    socketio.emit("match:update", {
                        "id": match_id,
                        "sport": "cricket",
                        "raw": mapped,
                        "stats": {
                            "run_rate": "N/A",
                            "top_scorer": {"name": "N/A", "runs": 0}
                        },
                        "last_updated": mapped["last_updated"]
                    }, room=match_id)
                else:
                    socketio.emit("match:update", {
                        "id": match_id,
                        "sport": "football",
                        "raw": mapped,
                        "stats": {
                            "possession": mapped.get("possession", {}),
                            "top_scorer": {"name": "N/A", "goals": "?"}
                        },
                        "last_updated": mapped["last_updated"]
                    }, room=match_id)
            else:
                # Trigger immediate fetch for existing subscription
                print(f"No cached data for {match_id}, triggering immediate fetch...")
                try:
                    if sport == "cricket":
                        api_data = fetch_cricket_data()
                        mapped = map_cricket_state(api_data)
                    else:
                        api_data = fetch_football_data()
                        mapped = map_football_state(api_data)
                    
                    if mapped:
                        matches[match_id] = mapped
                        print(f"Match data fetched for {match_id}: {mapped['teams'][0]} vs {mapped['teams'][1]}")
                        
                        if sport == "cricket":
                            socketio.emit("match:update", {
                                "id": match_id,
                                "sport": "cricket",
                                "raw": mapped,
                                "stats": {
                                    "run_rate": "N/A",
                                    "top_scorer": {"name": "N/A", "runs": 0}
                                },
                                "last_updated": mapped["last_updated"]
                            }, room=match_id)
                        else:
                            socketio.emit("match:update", {
                                "id": match_id,
                                "sport": "football",
                                "raw": mapped,
                                "stats": {
                                    "possession": mapped["possession"],
                                    "top_scorer": {"name": "N/A", "goals": "?"}
                                },
                                "last_updated": mapped["last_updated"]
                            }, room=match_id)
                    else:
                        socketio.emit("match:update", {
                            "info": "No active matches found. Waiting for matches to become available...",
                            "id": match_id,
                            "sport": sport
                        }, room=match_id)
                except Exception as e:
                    print(f"Error fetching data for existing subscription {match_id}: {e}")
                    socketio.emit("match:update", {
                        "info": f"Error fetching match data: {str(e)}",
                        "id": match_id,
                        "sport": sport
                    }, room=match_id)


@socketio.on("match:unsubscribe")
def unsubscribe(data):
    match_id = data.get("match_id")
    leave_room(match_id)
    print(f"Client unsubscribed from {match_id}")


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/test")
@app.route("/api/test/<sport>")
def test_api(sport="football"):
    """Test endpoint to check if ESPN API is working."""
    try:
        if sport == "cricket":
            api_data = fetch_cricket_data()
        else:
            api_data = fetch_football_data()
            
        if api_data:
            events_count = len(api_data.get("events", []))
            return jsonify({
                "status": "success",
                "sport": sport,
                "events_count": events_count,
                "has_data": events_count > 0,
                "sample_keys": list(api_data.keys()) if api_data else []
            })
        else:
            return jsonify({
                "status": "error",
                "sport": sport,
                "message": f"Failed to fetch data from ESPN {sport} API"
            }), 500
    except Exception as e:
        return jsonify({
            "status": "error",
            "sport": sport,
            "message": str(e)
        }), 500


@app.route("/api/match/<match_id>")
def get_match(match_id):
    """Get current match data for a given match_id."""
    if match_id in matches:
        return jsonify(matches[match_id])
    else:
        return jsonify({"error": "Match not found"}), 404


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    print(f"Server running at http://0.0.0.0:{port}")
    # Use threading mode explicitly to avoid eventlet issues with Python 3.12+
    socketio.run(app, host="0.0.0.0", port=port, debug=False, allow_unsafe_werkzeug=True)
