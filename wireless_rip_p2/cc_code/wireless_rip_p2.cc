#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/wifi-module.h"
#include "ns3/mobility-module.h"
#include "ns3/applications-module.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/netanim-module.h"
#include "ns3/rip-helper.h"

#include <fstream>
#include <map>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("WirelessRipP2Detailed");

struct LinkInfo
{
    uint32_t nodeA;
    uint32_t nodeB;
    std::string network;
};

NetDeviceContainer InstallWifiLink(NodeContainer &nodes,
                                   uint32_t a,
                                   uint32_t b,
                                   std::string phyMode)
{
    WifiHelper wifi;
    wifi.SetStandard(WIFI_STANDARD_80211b);

    wifi.SetRemoteStationManager(
        "ns3::ConstantRateWifiManager",
        "DataMode", StringValue(phyMode),
        "ControlMode", StringValue("DsssRate1Mbps")
    );

    YansWifiChannelHelper channel;
    channel.SetPropagationDelay("ns3::ConstantSpeedPropagationDelayModel");
    channel.AddPropagationLoss("ns3::FriisPropagationLossModel");

    YansWifiPhyHelper phy;
    phy.SetChannel(channel.Create());

    WifiMacHelper mac;
    mac.SetType("ns3::AdhocWifiMac",
                "QosSupported", BooleanValue(false));

    NodeContainer pair;
    pair.Add(nodes.Get(a));
    pair.Add(nodes.Get(b));

    return wifi.Install(phy, mac, pair);
}

int main(int argc, char *argv[])
{
    double simulationTime = 20.0;
    double appStartTime = 8.0;

    uint32_t packetSize = 1024;
    double packetInterval = 0.01;

    std::string phyMode = "DsssRate1Mbps";

    CommandLine cmd;
    cmd.AddValue("simulationTime", "Simulation time in seconds", simulationTime);
    cmd.AddValue("packetSize", "UDP packet size in bytes", packetSize);
    cmd.AddValue("packetInterval", "UDP packet interval in seconds", packetInterval);
    cmd.AddValue("phyMode", "WiFi physical data mode", phyMode);
    cmd.Parse(argc, argv);

    std::cout << "Starting detailed 5-node WiFi RIP simulation...\n";
    std::cout << "Packet interval = " << packetInterval << " s\n";
    std::cout << "Packet size = " << packetSize << " bytes\n";
    std::cout << "PHY mode = " << phyMode << "\n";

    NodeContainer nodes;
    nodes.Create(5);

    MobilityHelper mobility;
    Ptr<ListPositionAllocator> pos = CreateObject<ListPositionAllocator>();

    pos->Add(Vector(60.0, 20.0, 0.0));    // Node 0
    pos->Add(Vector(150.0, 55.0, 0.0));   // Node 1
    pos->Add(Vector(80.0, 100.0, 0.0));   // Node 2
    pos->Add(Vector(15.0, 85.0, 0.0));    // Node 3
    pos->Add(Vector(10.0, 45.0, 0.0));    // Node 4

    mobility.SetPositionAllocator(pos);
    mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
    mobility.Install(nodes);

    RipHelper rip;
    Ipv4ListRoutingHelper listRouting;
    listRouting.Add(rip, 10);

    InternetStackHelper internet;
    internet.SetRoutingHelper(listRouting);
    internet.Install(nodes);

    LinkInfo links[] =
    {
        {0, 2, "10.1.1.0"},
        {0, 3, "10.1.2.0"},
        {2, 3, "10.1.3.0"},
        {2, 4, "10.1.4.0"},
        {4, 1, "10.1.5.0"}
    };

    Ipv4AddressHelper address;

    Ipv4InterfaceContainer link02;
    Ipv4InterfaceContainer link03;
    Ipv4InterfaceContainer link23;
    Ipv4InterfaceContainer link24;
    Ipv4InterfaceContainer link41;

    for (uint32_t i = 0; i < 5; i++)
    {
        NetDeviceContainer dev = InstallWifiLink(
            nodes,
            links[i].nodeA,
            links[i].nodeB,
            phyMode
        );

        address.SetBase(links[i].network.c_str(), "255.255.255.0");
        Ipv4InterfaceContainer iface = address.Assign(dev);

        if (i == 0) link02 = iface;
        if (i == 1) link03 = iface;
        if (i == 2) link23 = iface;
        if (i == 3) link24 = iface;
        if (i == 4) link41 = iface;
    }

    std::map<uint32_t, Ipv4Address> dstAddress;
    dstAddress[1] = link41.GetAddress(1);
    dstAddress[2] = link02.GetAddress(1);
    dstAddress[3] = link03.GetAddress(1);
    dstAddress[4] = link24.GetAddress(1);

    std::map<uint32_t, std::string> path;
    path[1] = "0-2-4-1";
    path[2] = "0-2";
    path[3] = "0-3";
    path[4] = "0-2-4";

    std::map<uint32_t, uint32_t> hopCount;
    hopCount[1] = 3;
    hopCount[2] = 1;
    hopCount[3] = 1;
    hopCount[4] = 2;

    std::map<uint32_t, uint32_t> usesNode2;
    usesNode2[1] = 1;
    usesNode2[2] = 1;
    usesNode2[3] = 0;
    usesNode2[4] = 1;

    uint16_t basePort = 9000;

    ApplicationContainer serverApps;
    ApplicationContainer clientApps;

    for (uint32_t i = 1; i <= 4; i++)
    {
        UdpServerHelper server(basePort + i);
        serverApps.Add(server.Install(nodes.Get(i)));
    }

    serverApps.Start(Seconds(1.0));
    serverApps.Stop(Seconds(simulationTime));

    for (uint32_t i = 1; i <= 4; i++)
    {
        UdpClientHelper client(dstAddress[i], basePort + i);

        client.SetAttribute("MaxPackets", UintegerValue(10000000));
        client.SetAttribute("Interval", TimeValue(Seconds(packetInterval)));
        client.SetAttribute("PacketSize", UintegerValue(packetSize));

        clientApps.Add(client.Install(nodes.Get(0)));
    }

    clientApps.Start(Seconds(appStartTime));
    clientApps.Stop(Seconds(simulationTime));

    FlowMonitorHelper flowmon;
    Ptr<FlowMonitor> monitor = flowmon.InstallAll();

    AnimationInterface anim("wireless_rip_p2_netanim.xml");

    anim.SetConstantPosition(nodes.Get(0), 60.0, 20.0);
    anim.SetConstantPosition(nodes.Get(1), 150.0, 55.0);
    anim.SetConstantPosition(nodes.Get(2), 80.0, 100.0);
    anim.SetConstantPosition(nodes.Get(3), 15.0, 85.0);
    anim.SetConstantPosition(nodes.Get(4), 10.0, 45.0);

    anim.UpdateNodeDescription(nodes.Get(0), "Node 0 Source");
    anim.UpdateNodeDescription(nodes.Get(1), "Node 1 Destination");
    anim.UpdateNodeDescription(nodes.Get(2), "Node 2 Router/Bottleneck");
    anim.UpdateNodeDescription(nodes.Get(3), "Node 3 Destination");
    anim.UpdateNodeDescription(nodes.Get(4), "Node 4 Router/Destination");

    Simulator::Stop(Seconds(simulationTime));
    Simulator::Run();

    monitor->CheckForLostPackets();

    Ptr<Ipv4FlowClassifier> classifier =
        DynamicCast<Ipv4FlowClassifier>(flowmon.GetClassifier());

    std::map<FlowId, FlowMonitor::FlowStats> stats = monitor->GetFlowStats();

    std::ofstream csv;
    csv.open("wireless_rip_p2_results.csv");

    csv << "PacketInterval,OfferedLoadPerFlow_kbps,TotalOfferedLoad_kbps,"
        << "DestinationNode,Path,HopCount,UsesNode2,"
        << "SourceAddress,DestinationAddress,TxPackets,RxPackets,LostPackets,"
        << "Throughput_kbps,AverageDelay_ms,PDR_percent\n";

    std::cout << "\n========== UDP Application Flow Results ==========\n";

    double measurementTime = simulationTime - appStartTime;
    double offeredLoadPerFlow =
        (packetSize * 8.0) / packetInterval / 1000.0;
    double totalOfferedLoad = 4.0 * offeredLoadPerFlow;

    for (auto const &flow : stats)
    {
        Ipv4FlowClassifier::FiveTuple t = classifier->FindFlow(flow.first);

        if (t.protocol != 17)
        {
            continue;
        }

        if (t.destinationPort < basePort + 1 || t.destinationPort > basePort + 4)
        {
            continue;
        }

        uint32_t dstNode = t.destinationPort - basePort;

        double throughput = 0.0;
        double averageDelay = 0.0;
        double pdr = 0.0;

        throughput = (flow.second.rxBytes * 8.0) / measurementTime / 1000.0;

        if (flow.second.rxPackets > 0)
        {
            averageDelay =
                flow.second.delaySum.GetSeconds() /
                flow.second.rxPackets *
                1000.0;
        }

        if (flow.second.txPackets > 0)
        {
            pdr =
                (double)flow.second.rxPackets /
                (double)flow.second.txPackets *
                100.0;
        }

        std::cout << "Flow: Node 0 -> Node " << dstNode << "\n";
        std::cout << "Path: " << path[dstNode] << "\n";
        std::cout << "Hop Count: " << hopCount[dstNode] << "\n";
        std::cout << "Uses Node 2: " << usesNode2[dstNode] << "\n";
        std::cout << "Tx Packets: " << flow.second.txPackets << "\n";
        std::cout << "Rx Packets: " << flow.second.rxPackets << "\n";
        std::cout << "Lost Packets: " << flow.second.lostPackets << "\n";
        std::cout << "Throughput: " << throughput << " kbps\n";
        std::cout << "Average Delay: " << averageDelay << " ms\n";
        std::cout << "PDR: " << pdr << " %\n";
        std::cout << "----------------------------------------\n";

        csv << packetInterval << ","
            << offeredLoadPerFlow << ","
            << totalOfferedLoad << ","
            << dstNode << ","
            << path[dstNode] << ","
            << hopCount[dstNode] << ","
            << usesNode2[dstNode] << ","
            << t.sourceAddress << ","
            << t.destinationAddress << ","
            << flow.second.txPackets << ","
            << flow.second.rxPackets << ","
            << flow.second.lostPackets << ","
            << throughput << ","
            << averageDelay << ","
            << pdr << "\n";
    }

    csv.close();

    monitor->SerializeToXmlFile("wireless_rip_p2_flowmonitor.xml", true, true);

    Simulator::Destroy();

    std::cout << "\nSimulation finished successfully.\n";
    std::cout << "CSV file: wireless_rip_p2_results.csv\n";
    std::cout << "FlowMonitor XML: wireless_rip_p2_flowmonitor.xml\n";
    std::cout << "NetAnim XML: wireless_rip_p2_netanim.xml\n";

    return 0;
}