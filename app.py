import heapq
from collections import deque, defaultdict
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import streamlit as st

class Graph:
    def __init__(self):
        self.adj_list = defaultdict(dict)

    def add_edge(self, u, v, dis):
        self.adj_list[u][v] = dis
        self.adj_list[v][u] = dis

    def dijkstra(self, src, dest):
        dist = {node: float('inf') for node in self.adj_list}
        prev = {}
        dist[src] = 0
        pq = [(0, src)]
        while pq:
            current_dist, u = heapq.heappop(pq)
            if current_dist > dist[u]:   # skip stale heap entries
                continue
            if u == dest:
                break
            for v, weight in self.adj_list[u].items():
                if dist[u] + weight < dist[v]:
                    dist[v] = dist[u] + weight
                    prev[v] = u
                    heapq.heappush(pq, (dist[v], v))
        return self._reconstruct_path(prev, src, dest)

    def bfs(self, src, dest):
        visited = set()
        prev = {}
        q = deque([src])
        visited.add(src)
        while q:
            u = q.popleft()
            if u == dest:
                break
            for v in self.adj_list[u]:
                if v not in visited:
                    visited.add(v)
                    prev[v] = u
                    q.append(v)
        return self._reconstruct_path(prev, src, dest)

    def dfs(self, src, dest):
        def dfs_helper(u, dest, visited, path):
            visited.add(u)
            path.append(u)
            if u == dest:
                return True
            for v in self.adj_list[u]:
                if v not in visited:
                    if dfs_helper(v, dest, visited, path):
                        return True
            path.pop()
            return False

        visited = set()
        path = []
        if dfs_helper(src, dest, visited, path):
            return path
        return []

    def calculate_dist(self, path):
        total_dist = 0
        for i in range(len(path) - 1):
            total_dist += self.adj_list[path[i]][path[i + 1]]
        return total_dist

    def _reconstruct_path(self, prev, src, dest):
        path = []
        at = dest
        while at in prev:
            path.append(at)
            at = prev[at]
        if at == src:
            path.append(src)
            path.reverse()
            return path
        return []

# Load Excel and create graph
try:
    df = pd.read_excel("HYD_F.xlsx")
except FileNotFoundError:
    st.error("❌ Metro data file (HYD_F.xlsx) not found. Please ensure it is in the same directory as app.py.")
    st.stop()
except Exception as e:
    st.error(f"❌ Failed to load metro data: {e}")
    st.stop()
metro_graph = Graph()
nx_graph = nx.Graph()

for _, row in df.iterrows():
    src, dest, time = row['Source'], row['Destination'], row['Distance']
    metro_graph.add_edge(src, dest, time)
    nx_graph.add_edge(src, dest, weight=time)


st.markdown("""
<style>
    .main { background-color: #0e1117; color: #ffffff; }
    div.stButton > button {
        color: white;
        background-color: #e50914;
        border-radius: 10px;
        height: 3em;
        width: 100%;
        font-size: 18px;
    }
</style>
""", unsafe_allow_html=True)

if 'page' not in st.session_state:
    st.session_state.page = 'main'

if st.session_state.page == 'main':
    st.title("Hyderabad Metro Route Finder")
    st.markdown("Select your route and click *Find Path* to get started!")

    all_stations = sorted(set(df['Source']).union(set(df['Destination'])))

    source = st.selectbox("Select Source Station", all_stations)
    destination = st.selectbox("Select Destination Station", all_stations)
    algo_label_map = {
    "Dijkstra": "Dijkstra - Shortest Distance",
    "BFS": "BFS - Fewest Stops",
    "DFS": "DFS - Random Depth Path"
    }
    algo_display = st.selectbox("Choose Route Strategy", list(algo_label_map.values()))
    algo = [k for k, v in algo_label_map.items() if v == algo_display][0]

  

    if st.button("Find Path"):
        st.session_state.source = source
        st.session_state.destination = destination
        st.session_state.algo = algo
        st.session_state.page = 'result'

elif st.session_state.page == 'result':
    st.title("🚇 Metro Route Result")
    st.write(f"*From:* {st.session_state.source}")
    st.write(f"*To:* {st.session_state.destination}")
    st.write(f"*Algorithm Used:* {st.session_state.algo}")
    
    source = st.session_state.source
    destination = st.session_state.destination
    algo = st.session_state.algo

    if algo == 'Dijkstra':
        path = metro_graph.dijkstra(source, destination)
    elif algo == 'BFS':
        path = metro_graph.bfs(source, destination)
    else:
        path = metro_graph.dfs(source, destination)

    if path:
        tab1, tab2, tab3 = st.tabs(["📍 Route Summary", "📊 Route Table", "🗺 HYD_METRO_MAP(reference)"])
        with tab1:
                    st.success(" → ".join(path))
                    total_dist = metro_graph.calculate_dist(path)
                
                    # Stations where line changes typically happen
                    change_stations = [station for station in ["Ameerpet", "MG Bus Station", "Parade Ground"] if station in path[1:-1]]
                
                    st.markdown("""
                    <style>
                        .ticket {
                            background: #1e293b;
                            padding: 20px;
                            border-radius: 15px;
                            color: white;
                            font-family: 'Courier New', monospace;
                            border: 2px dashed #38bdf8;
                        }
                        .ticket h3 {
                            color: #facc15;
                        }
                        .ticket p {
                            margin: 5px 0;
                        }
                        .transfer-instruction {
                            background-color: #334155;
                            padding: 10px;
                            border-radius: 10px;
                            margin-top: 15px;
                        }
                    </style>
                    """, unsafe_allow_html=True)
                    transfer_html = ""
                    if change_stations:
                        transfer_html += "<div class='transfer-instruction'><strong>🔁 Transfer Instructions:</strong><ul>"
                        transfer_html += ''.join(f"<li>You might need to Change train at <b>{station}</b> to switch lines.refer HYD_METRO_MAP.</li>" for station in change_stations)
                        transfer_html += "</ul></div>"
                    
                    ticket_html = f"""
                    <div class="ticket">
                    <h3>🎫 Hyderabad Metro Ticket</h3>
                    <p><strong>From:</strong> {source}</p>
                    <p><strong>To:</strong> {destination}</p>
                    <p><strong>Total Distance:</strong> {total_dist:.1f} km</p>
                    {transfer_html}
                    </div>
                    <p style="text-align:center; margin-top:20px; font-size:16px; color:#22c55e;">😊 Happy Journey!</p>

                    """
                    
                    st.markdown(ticket_html, unsafe_allow_html=True)

                   
                        

        with tab2:
            st.subheader("Stations on the Route")
            df_path = pd.DataFrame({
                "Stop Number": list(range(1, len(path)+1)),
                "Station": path
            })
            st.table(df_path)

        with tab3:
            st.image('finimg.png')
            
    else:
        st.error("No path found!")

    if st.button("🔙 Back"):
        st.session_state.page = 'main'
