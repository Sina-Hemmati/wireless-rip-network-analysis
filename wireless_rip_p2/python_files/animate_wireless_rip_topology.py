import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

# -----------------------------
# Node positions
# -----------------------------
pos = {
    0: np.array([2.5, 4.0]),
    1: np.array([5.0, 2.5]),
    2: np.array([3.0, 1.2]),
    3: np.array([1.2, 1.8]),
    4: np.array([0.8, 3.0]),
}

links = [
    (0, 2),
    (0, 3),
    (2, 3),
    (2, 4),
    (4, 1),
]

flows = {
    "Node 0 → Node 1": [0, 2, 4, 1],
    "Node 0 → Node 2": [0, 2],
    "Node 0 → Node 3": [0, 3],
    "Node 0 → Node 4": [0, 2, 4],
}

colors = {
    "Node 0 → Node 1": "tab:red",
    "Node 0 → Node 2": "tab:blue",
    "Node 0 → Node 3": "tab:green",
    "Node 0 → Node 4": "tab:orange",
}

# -----------------------------
# Helper: interpolate along path
# -----------------------------
def get_packet_position(path, progress):
    points = [pos[n] for n in path]
    segments = len(points) - 1

    if progress >= 1:
        return points[-1]

    segment_float = progress * segments
    segment_index = int(segment_float)
    local_progress = segment_float - segment_index

    start = points[segment_index]
    end = points[segment_index + 1]

    return start + local_progress * (end - start)

# -----------------------------
# Figure
# -----------------------------
fig, ax = plt.subplots(figsize=(8, 6))

def draw_base():
    ax.clear()
    ax.set_xlim(0, 5.7)
    ax.set_ylim(0.5, 4.6)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("UDP Traffic Paths in the Wi-Fi RIP Topology", fontsize=14)

    # Draw links
    for a, b in links:
        x = [pos[a][0], pos[b][0]]
        y = [pos[a][1], pos[b][1]]
        ax.plot(x, y, color="gray", linewidth=2, alpha=0.6)

    # Draw nodes
    for node, p in pos.items():
        ax.scatter(p[0], p[1], s=900, color="white", edgecolor="black", linewidth=2, zorder=3)
        ax.text(p[0], p[1], f"{node}", ha="center", va="center", fontsize=16, fontweight="bold", zorder=4)

    # Highlight important nodes
    ax.text(pos[0][0], pos[0][1] + 0.35, "Source", ha="center", fontsize=10)
    ax.text(pos[2][0], pos[2][1] - 0.45, "Main forwarding node", ha="center", fontsize=10)
    ax.text(pos[4][0], pos[4][1] + 0.35, "Forwards to Node 1", ha="center", fontsize=10)

# -----------------------------
# Animation update
# -----------------------------
def update(frame):
    draw_base()

    total_frames = 120

    for i, (label, path) in enumerate(flows.items()):
        delay = i * 15
        progress = ((frame - delay) % total_frames) / total_frames

        packet_pos = get_packet_position(path, progress)

        ax.scatter(
            packet_pos[0],
            packet_pos[1],
            s=180,
            color=colors[label],
            edgecolor="black",
            zorder=5,
            label=label
        )

    ax.legend(loc="upper right", fontsize=9)

ani = animation.FuncAnimation(
    fig,
    update,
    frames=180,
    interval=80,
    repeat=True
)

ani.save("wireless_rip_packet_animation.gif", writer="pillow", fps=12)

print("Animation saved as wireless_rip_packet_animation.gif")