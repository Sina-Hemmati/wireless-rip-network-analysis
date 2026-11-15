import os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ============================================================
# Final Plotting and Analysis Script
# Wi-Fi MAC + RIP Routing Project
# Portable version: automatically finds CSV files
# ============================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

OUTPUT_DIR = os.path.join(PROJECT_DIR, "final_plots")
os.makedirs(OUTPUT_DIR, exist_ok=True)

plt.rcParams.update({
    "figure.figsize": (8.5, 5.2),
    "figure.dpi": 120,
    "savefig.dpi": 300,
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.labelsize": 12,
    "legend.fontsize": 9,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "axes.grid": True,
    "grid.alpha": 0.35,
    "grid.linestyle": "--",
})

# ============================================================
# Automatically locate CSV files
# ============================================================

files = sorted(
    glob.glob(
        os.path.join(PROJECT_DIR, "**", "wireless_rip_p2_results_*.csv"),
        recursive=True
    )
)

if not files:
    raise FileNotFoundError(
        "No wireless_rip_p2_results_*.csv files were found anywhere inside the project folder."
    )

print("CSV files found:")
for file in files:
    print(" -", file)

df_list = []

for file in files:
    temp = pd.read_csv(file)
    temp["SourceFile"] = os.path.basename(file)
    df_list.append(temp)

df = pd.concat(df_list, ignore_index=True)

df = df.drop_duplicates(
    subset=[
        "PacketInterval",
        "DestinationNode",
        "TxPackets",
        "RxPackets",
        "Throughput_kbps",
        "AverageDelay_ms",
        "PDR_percent"
    ]
)

df = df.sort_values(["OfferedLoadPerFlow_kbps", "DestinationNode"])

df["DestinationLabel"] = "Node " + df["DestinationNode"].astype(str)

df["ForwardedThroughNode2"] = df["DestinationNode"].isin([1, 4]).astype(int)

df["ForwardingClass"] = df["ForwardedThroughNode2"].map({
    1: "Forwarded through Node 2",
    0: "Not forwarded through Node 2"
})

df["ThroughputUtilization_percent"] = (
    df["Throughput_kbps"] / df["OfferedLoadPerFlow_kbps"] * 100
)

df["NetworkEfficiency_percent"] = (
    df["RxPackets"] / df["TxPackets"] * 100
)

# ============================================================
# Required summary table
# ============================================================

summary_table = df[[
    "PacketInterval",
    "OfferedLoadPerFlow_kbps",
    "DestinationNode",
    "Path",
    "HopCount",
    "ForwardingClass",
    "TxPackets",
    "RxPackets",
    "LostPackets",
    "Throughput_kbps",
    "AverageDelay_ms",
    "PDR_percent"
]].copy()

summary_table = summary_table.rename(columns={
    "PacketInterval": "Packet Interval (s)",
    "OfferedLoadPerFlow_kbps": "Offered Load per Flow (kbps)",
    "DestinationNode": "Destination Node",
    "Path": "RIP Path",
    "HopCount": "Hop Count",
    "ForwardingClass": "Forwarding Class",
    "TxPackets": "Transmitted Packets",
    "RxPackets": "Received Packets",
    "LostPackets": "Packet Loss",
    "Throughput_kbps": "Throughput / Average Received Rate (kbps)",
    "AverageDelay_ms": "Average End-to-End Delay (ms)",
    "PDR_percent": "Packet Delivery Ratio (%)"
})

summary_table.to_csv(
    os.path.join(OUTPUT_DIR, "required_metrics_summary_table.csv"),
    index=False
)

# ============================================================
# Helper functions
# ============================================================

def save_line_plot(metric, ylabel, title, filename, ylim=None):
    plt.figure()

    for node in sorted(df["DestinationNode"].unique()):
        temp = df[df["DestinationNode"] == node]

        plt.plot(
            temp["OfferedLoadPerFlow_kbps"],
            temp[metric],
            marker="o",
            linewidth=2.3,
            markersize=6,
            label=f"Node {node}"
        )

    plt.xlabel("Offered Load per Flow (kbps)")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend(title="Destination")
    if ylim is not None:
        plt.ylim(ylim)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()


def save_heatmap(metric, title, filename, colorbar_label, fmt=".1f"):
    pivot = df.pivot(
        index="DestinationNode",
        columns="OfferedLoadPerFlow_kbps",
        values=metric
    )

    pivot = pivot.reindex(sorted(pivot.columns), axis=1)

    plt.figure(figsize=(10.5, 4.8))
    image = plt.imshow(pivot, aspect="auto")

    plt.colorbar(image, label=colorbar_label)

    plt.xticks(
        range(len(pivot.columns)),
        [f"{x:.0f}" for x in pivot.columns],
        rotation=45
    )

    plt.yticks(
        range(len(pivot.index)),
        [f"Node {x}" for x in pivot.index]
    )

    plt.xlabel("Offered Load per Flow (kbps): light traffic → heavy traffic")
    plt.ylabel("Destination Node")
    plt.title(title)

    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            value = pivot.iloc[i, j]
            plt.text(
                j,
                i,
                f"{value:{fmt}}",
                ha="center",
                va="center",
                fontsize=8
            )

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()


def save_grouped_forwarding_plot(metric, ylabel, title, filename, ylim=None):
    grouped = df.groupby(["OfferedLoadPerFlow_kbps", "ForwardingClass"]).agg({
        metric: "mean"
    }).reset_index()

    plt.figure()

    for group in grouped["ForwardingClass"].unique():
        temp = grouped[grouped["ForwardingClass"] == group]

        plt.plot(
            temp["OfferedLoadPerFlow_kbps"],
            temp[metric],
            marker="o",
            linewidth=2.3,
            markersize=6,
            label=group
        )

    plt.xlabel("Offered Load per Flow (kbps)")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    if ylim is not None:
        plt.ylim(ylim)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.close()

# ============================================================
# Required homework plots
# ============================================================

save_line_plot(
    "Throughput_kbps",
    "Average Received Throughput (kbps)",
    "Required Metric: Throughput per Destination Node",
    "required_throughput_per_destination_node.png"
)

save_line_plot(
    "AverageDelay_ms",
    "Average End-to-End Delay (ms)",
    "Required Metric: End-to-End Delay per Destination Node",
    "required_end_to_end_delay_per_destination_node.png"
)

save_line_plot(
    "PDR_percent",
    "Packet Delivery Ratio (%)",
    "Required Metric: Packet Delivery Ratio per Destination Node",
    "required_packet_delivery_ratio_per_destination_node.png",
    ylim=(0, 105)
)

save_line_plot(
    "LostPackets",
    "Lost Packets",
    "Packet Loss per Destination Node",
    "packet_loss_per_destination_node.png"
)

# ============================================================
# Heatmaps
# ============================================================

save_heatmap(
    "Throughput_kbps",
    "Throughput Heatmap",
    "throughput_heatmap.png",
    "Throughput (kbps)"
)

save_heatmap(
    "AverageDelay_ms",
    "End-to-End Delay Heatmap",
    "delay_heatmap.png",
    "Delay (ms)"
)

save_heatmap(
    "PDR_percent",
    "Packet Delivery Ratio Heatmap",
    "pdr_heatmap.png",
    "PDR (%)"
)

save_heatmap(
    "LostPackets",
    "Packet Loss Heatmap",
    "packet_loss_heatmap.png",
    "Lost Packets",
    fmt=".0f"
)

# ============================================================
# Forwarding-through-Node-2 analysis
# ============================================================

save_grouped_forwarding_plot(
    "Throughput_kbps",
    "Average Throughput (kbps)",
    "Impact of Forwarding Through Node 2 on Throughput",
    "node2_forwarding_throughput.png"
)

save_grouped_forwarding_plot(
    "AverageDelay_ms",
    "Average Delay (ms)",
    "Impact of Forwarding Through Node 2 on Delay",
    "node2_forwarding_delay.png"
)

save_grouped_forwarding_plot(
    "PDR_percent",
    "Average PDR (%)",
    "Impact of Forwarding Through Node 2 on PDR",
    "node2_forwarding_pdr.png",
    ylim=(0, 105)
)

save_grouped_forwarding_plot(
    "LostPackets",
    "Average Lost Packets",
    "Impact of Forwarding Through Node 2 on Packet Loss",
    "node2_forwarding_packet_loss.png"
)

# ============================================================
# Forwarding burden plot
# ============================================================

forwarding_burden = pd.DataFrame({
    "Node": ["Node 0", "Node 1", "Node 2", "Node 3", "Node 4"],
    "ForwardedFlows": [0, 0, 2, 0, 1]
})

plt.figure()
bars = plt.bar(
    forwarding_burden["Node"],
    forwarding_burden["ForwardedFlows"]
)

plt.xlabel("Network Node")
plt.ylabel("Number of Forwarded UDP Flows")
plt.title("Packet Forwarding Responsibility in the RIP Topology")
plt.ylim(0, 2.5)

for bar in bars:
    value = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        value + 0.05,
        f"{value:.0f}",
        ha="center",
        va="bottom"
    )

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "node_forwarding_burden.png"))
plt.close()

# ============================================================
# Delay vs hop count
# ============================================================

hop_delay = df.groupby("HopCount").agg({
    "AverageDelay_ms": "mean"
}).reset_index()

plt.figure()
plt.plot(
    hop_delay["HopCount"],
    hop_delay["AverageDelay_ms"],
    marker="o",
    linewidth=2.3,
    markersize=7
)

plt.xlabel("RIP Path Hop Count")
plt.ylabel("Average End-to-End Delay (ms)")
plt.title("End-to-End Delay vs RIP Hop Count")
plt.xticks(sorted(df["HopCount"].unique()))
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "delay_vs_hop_count.png"))
plt.close()

# ============================================================
# Throughput utilization
# ============================================================

save_line_plot(
    "ThroughputUtilization_percent",
    "Throughput Utilization (%)",
    "Throughput Utilization vs Offered Load",
    "throughput_utilization.png",
    ylim=(0, 110)
)

# ============================================================
# Overall network efficiency
# ============================================================

network_efficiency = df.groupby("OfferedLoadPerFlow_kbps").agg({
    "TxPackets": "sum",
    "RxPackets": "sum"
}).reset_index()

network_efficiency["Efficiency_percent"] = (
    network_efficiency["RxPackets"] /
    network_efficiency["TxPackets"] * 100
)

plt.figure()
plt.plot(
    network_efficiency["OfferedLoadPerFlow_kbps"],
    network_efficiency["Efficiency_percent"],
    marker="o",
    linewidth=2.3,
    markersize=7
)

plt.xlabel("Offered Load per Flow (kbps)")
plt.ylabel("Overall Packet Delivery Efficiency (%)")
plt.title("Overall Network Efficiency vs Offered Load")
plt.ylim(0, 105)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "network_efficiency.png"))
plt.close()

# ============================================================
# Final conclusion table
# ============================================================

destination_summary = df.groupby(
    ["DestinationNode", "Path", "HopCount", "ForwardingClass"]
).agg({
    "Throughput_kbps": "mean",
    "AverageDelay_ms": "mean",
    "PDR_percent": "mean",
    "LostPackets": "mean",
    "ThroughputUtilization_percent": "mean"
}).reset_index()

destination_summary["Conclusion"] = destination_summary["DestinationNode"].map({
    1: "Longest RIP route; traffic passes through Node 2 and Node 4, so delay and loss increase under high load.",
    2: "Direct destination on the Node 0--Node 2 link; affected by Node 2 contention but not by multi-hop forwarding.",
    3: "Direct route that does not rely on Node 2 forwarding; usually shows the most stable performance.",
    4: "Two-hop route through Node 2 and also a forwarding point toward Node 1; strongly affected by congestion."
})

destination_summary.to_csv(
    os.path.join(OUTPUT_DIR, "final_conclusion_table.csv"),
    index=False
)

# ============================================================
# Final print
# ============================================================

print("\nDone. All final figures and tables were saved in:")
print(OUTPUT_DIR)

print("\nRequired figures:")
print("required_throughput_per_destination_node.png")
print("required_end_to_end_delay_per_destination_node.png")
print("required_packet_delivery_ratio_per_destination_node.png")

print("\nTables:")
print("required_metrics_summary_table.csv")
print("final_conclusion_table.csv")