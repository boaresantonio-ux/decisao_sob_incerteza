from flask import Flask, jsonify, request, render_template_string
import random
import threading
import time

app = Flask(__name__)

# ==============================
# CONFIG
# ==============================
REPLICATION_FACTOR = 2

# ==============================
# NODE
# ==============================
class Node:
    def __init__(self, node_id):
        self.node_id = node_id
        self.alive = True
        self.data = {}

    def store(self, key, value):
        if self.alive:
            self.data[key] = value

    def fail(self):
        self.alive = False

    def recover(self):
        self.alive = True


# ==============================
# CLUSTER
# ==============================
class Cluster:
    def __init__(self):
        self.nodes = []

    def add_node(self, node_id):
        self.nodes.append(Node(node_id))

    def get_alive_nodes(self):
        return [n for n in self.nodes if n.alive]

    def get_node(self, node_id):
        return next((n for n in self.nodes if n.node_id == node_id), None)


cluster = Cluster()
for i in range(1, 4):
    cluster.add_node(f"node{i}")


# ==============================
# REPLICAÇÃO
# ==============================
def replicate(key, value):
    nodes = cluster.get_alive_nodes()
    selected = random.sample(nodes, min(REPLICATION_FACTOR, len(nodes)))

    for node in selected:
        node.store(key, value)


# ==============================
# RECUPERAÇÃO
# ==============================
def recover_node(node):
    for n in cluster.get_alive_nodes():
        for k, v in n.data.items():
            node.store(k, v)
    node.recover()


# ==============================
# HTML (INTERFACE)
# ==============================
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Cluster Multinodal</title>
    <style>
        body { font-family: Arial; padding: 20px; }
        .node { border: 1px solid #ccc; padding: 10px; margin: 10px; }
        .up { color: green; }
        .down { color: red; }
    </style>
</head>
<body>

<h1>🌐 Cluster Multinodal</h1>

<h2>Inserir Dados</h2>
<input id="key" placeholder="Key">
<input id="value" placeholder="Value">
<button onclick="sendData()">Enviar</button>

<h2>Nós</h2>
<div id="nodes"></div>

<script>
async function loadNodes() {
    const res = await fetch('/nodes');
    const data = await res.json();

    let html = "";
    data.forEach(n => {
        html += `
        <div class="node">
            <b>${n.id}</b> - 
            <span class="${n.alive ? 'up' : 'down'}">
                ${n.alive ? 'UP' : 'DOWN'}
            </span>
            <br>
            Dados: ${JSON.stringify(n.data)}
            <br><br>
            <button onclick="fail('${n.id}')">Falhar</button>
            <button onclick="recover('${n.id}')">Recuperar</button>
        </div>
        `;
    });

    document.getElementById("nodes").innerHTML = html;
}

async function sendData() {
    const key = document.getElementById("key").value;
    const value = document.getElementById("value").value;

    await fetch('/replicate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key, value })
    });

    loadNodes();
}

async function fail(id) {
    await fetch('/fail/' + id);
    loadNodes();
}

async function recover(id) {
    await fetch('/recover/' + id);
    loadNodes();
}

setInterval(loadNodes, 2000);
loadNodes();
</script>

</body>
</html>
"""

# ==============================
# ROTAS
# ==============================
@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/nodes")
def nodes():
    return jsonify([
        {
            "id": n.node_id,
            "alive": n.alive,
            "data": n.data
        } for n in cluster.nodes
    ])


@app.route("/replicate", methods=["POST"])
def replicate_route():
    data = request.json
    replicate(data["key"], data["value"])
    return {"status": "ok"}


@app.route("/fail/<node_id>")
def fail(node_id):
    node = cluster.get_node(node_id)
    if node:
        node.fail()
    return {"status": "failed"}


@app.route("/recover/<node_id>")
def recover(node_id):
    node = cluster.get_node(node_id)
    if node:
        recover_node(node)
    return {"status": "recovered"}


# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    app.run(debug=True)
