// New post-submission verification, October 2026. Not a recovered publication file.
// Standalone C++17: no project solvers, graph libraries, or structural lower bound.
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

using Mask = std::uint64_t;
using Edge = std::pair<int, int>;
constexpr int MAX_N = 24; // Exhaustive search; intentionally restricted to small graphs.

struct Graph {
    int n = 0;
    std::vector<Edge> edges;
    std::array<Mask, MAX_N> neighbors{};
};

Graph decode_graph6(const std::string& code) {
    if (code.empty()) throw std::runtime_error("empty graph6 record");
    for (unsigned char ch : code)
        if (ch < 63 || ch > 126) throw std::runtime_error("invalid graph6 character");
    Graph g;
    g.n = static_cast<unsigned char>(code[0]) - 63;
    if (g.n > MAX_N) throw std::runtime_error("only single-byte graph6 orders 0..24 supported");
    const int bits = g.n * (g.n - 1) / 2;
    if (code.size() != 1 + static_cast<std::size_t>((bits + 5) / 6))
        throw std::runtime_error("incorrect graph6 length");
    int bit = 0;
    for (int v = 1; v < g.n; ++v) {
        for (int u = 0; u < v; ++u, ++bit) {
            const int value = static_cast<unsigned char>(code[1 + bit / 6]) - 63;
            if ((value >> (5 - bit % 6)) & 1) {
                g.edges.emplace_back(u, v);
                g.neighbors[u] |= Mask{1} << v;
                g.neighbors[v] |= Mask{1} << u;
            }
        }
    }
    if (bits % 6 && ((static_cast<unsigned char>(code.back()) - 63) & ((1 << (6 - bits % 6)) - 1)))
        throw std::runtime_error("nonzero graph6 padding");
    return g;
}

// Rebuild the entire vertex-induced subgraph, including all cross edges.
bool induced_forest(const Graph& g, Mask vertices) {
    std::array<int, MAX_N> parent{};
    for (int v = 0; v < g.n; ++v) parent[v] = v;
    auto root = [&parent](int v) {
        while (parent[v] != v) v = parent[v];
        return v;
    };
    for (const auto& [u, v] : g.edges) {
        if (!(vertices & (Mask{1} << u)) || !(vertices & (Mask{1} << v))) continue;
        const int a = root(u), b = root(v);
        if (a == b) return false;
        parent[a] = b;
    }
    return true;
}

int first_vertex(Mask mask) {
    int v = 0;
    while (!(mask & 1)) { mask >>= 1; ++v; }
    return v;
}

// Definition-level recursion; it also works without assuming the graph is a forest.
bool perfect_matching(const Graph& g, Mask vertices, std::vector<Edge>& witness) {
    if (!vertices) return true;
    const int u = first_vertex(vertices);
    Mask choices = g.neighbors[u] & vertices;
    while (choices) {
        const int v = first_vertex(choices);
        choices &= choices - 1;
        witness.emplace_back(u, v);
        if (perfect_matching(g, vertices ^ (Mask{1} << u) ^ (Mask{1} << v), witness)) return true;
        witness.pop_back();
    }
    return false;
}

bool maximal_endpoints(const Graph& g, Mask vertices) {
    for (const auto& [u, v] : g.edges) {
        const Mask endpoints = (Mask{1} << u) | (Mask{1} << v);
        if (!(vertices & endpoints) && induced_forest(g, vertices | endpoints)) return false;
    }
    return true;
}

struct Layer {
    int k;
    std::uint64_t tested = 0, forests = 0, perfect = 0;
};

std::string json_string(const std::string& value) {
    std::string out = "\"";
    for (const char ch : value) {
        if (ch == '\\' || ch == '\"') out += '\\';
        out += ch;
    }
    return out + "\"";
}

void solve(const Graph& g, const std::string& code, std::size_t index) {
    const auto start = std::chrono::steady_clock::now();
    std::vector<Layer> layers;
    std::vector<Edge> witness;
    Mask answer = 0;
    int optimum = -1;
    const Mask limit = Mask{1} << g.n;
    // Start at zero, including every smaller cardinality. Never consult a theorem,
    // a manuscript histogram, Solver B/C, or an externally supplied upper bound.
    for (int k = 0; 2 * k <= g.n && optimum < 0; ++k) {
        Layer layer{k};
        Mask subset = (Mask{1} << (2 * k)) - 1;
        while (subset < limit) {
            ++layer.tested;
            if (induced_forest(g, subset)) {
                ++layer.forests;
                witness.clear();
                if (perfect_matching(g, subset, witness)) {
                    ++layer.perfect;
                    if (maximal_endpoints(g, subset)) {
                        answer = subset;
                        optimum = k;
                        break;
                    }
                }
            }
            if (!subset) break; // The unique empty subset.
            // Gosper's next fixed-population bit mask, in increasing numeric order.
            const Mask low = subset & (~subset + 1);
            const Mask next = subset + low;
            subset = next | (((next ^ subset) >> 2) / low);
        }
        layers.push_back(layer);
    }
    if (optimum < 0) throw std::runtime_error("no maximal acyclic matching found");
    const double seconds = std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
    std::cout << "{\"index\":" << index << ",\"graph6\":" << json_string(code)
              << ",\"n\":" << g.n << ",\"mu\":" << optimum
              << ",\"endpoint_mask\":" << answer << ",\"matching\":[";
    for (std::size_t i = 0; i < witness.size(); ++i) {
        if (i) std::cout << ',';
        std::cout << '[' << witness[i].first << ',' << witness[i].second << ']';
    }
    std::cout << "],\"layers\":[";
    for (std::size_t i = 0; i < layers.size(); ++i) {
        if (i) std::cout << ',';
        const auto& l = layers[i];
        std::cout << "{\"k\":" << l.k << ",\"tested\":" << l.tested
                  << ",\"forests\":" << l.forests << ",\"perfect\":" << l.perfect << '}';
    }
    std::cout << "],\"seconds\":" << std::setprecision(9) << seconds << "}\n";
}

int main(int argc, char** argv) {
    try {
        if (argc != 2) throw std::runtime_error("usage: endpoint_audit INPUT.g6");
        std::ifstream input(argv[1]);
        if (!input) throw std::runtime_error("cannot open input");
        std::string code;
        std::size_t index = 0;
        while (std::getline(input, code)) {
            if (!code.empty() && code.back() == '\r') code.pop_back();
            if (code == ">>graph6<<") continue;
            if (code.rfind(">>graph6<<", 0) == 0) code.erase(0, 10);
            if (code.empty()) throw std::runtime_error("empty input record");
            solve(decode_graph6(code), code, index++);
        }
        if (!index) throw std::runtime_error("no graph records");
        if (!std::cout) throw std::runtime_error("output write failed");
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "endpoint audit failed: " << error.what() << '\n';
        return 1;
    }
}
