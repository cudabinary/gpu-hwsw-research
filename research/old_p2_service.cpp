#include "adapter.hpp"
#include <array>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <sys/resource.h>
using namespace merged;
using Clock = std::chrono::steady_clock;
static double ns(Clock::time_point t) {
    return std::chrono::duration<double, std::nano>(Clock::now() - t).count();
}
struct Case {
    std::string name;
    std::shared_ptr<const Graph> graph;
    std::vector<U> sources;
    std::vector<std::vector<int>> expected;
};
static std::vector<Case> load() {
    std::ifstream input("vendor/rcc_20261021/fixtures/cases.txt");
    require(bool(input), "cases open");
    std::vector<Case> cases;
    std::string line;
    while (std::getline(input, line)) {
        std::istringstream row(line);
        std::string name, schedule, file;
        U n;
        row >> name >> schedule >> file >> n;
        if (schedule != "original" || (name != "livejournal_sampled_4096" && name != "lj_permuted")) continue;
        Case c;
        c.name = name;
        c.graph = Graph::load("vendor/rcc_20261021/fixtures/" + file, n, 20261021);
        U source;
        while (row >> source) c.sources.push_back(source);
        require(c.sources.size() == 33, "fixed 33 sources");
        for (U s : c.sources) c.expected.push_back(oracle(*c.graph, s));
        cases.push_back(std::move(c));
    }
    require(cases.size() == 2, "two fixed fixtures");
    return cases;
}
struct Variant { const char* mode; const char* path; };
static constexpr std::array<Variant, 4> variants{{
    {"PUSH_N", "csr"}, {"PUSH_RCC_TABLE", "csr"},
    {"OLD_P2", "deferred"}, {"OLD_P2", "ready"}
}};
struct Timing {
    double total=0, a_compute=0, a_done=0, b_ready=0, prior=0;
    double validation=0, release=0, cleanup_window=0, lifecycle=0;
    L payload=0, arrays=0;
};
static Timing service(const Case& c, Variant v, U q, std::ostream* dump=nullptr) {
    Timing st;
    const auto life = Clock::now();
    Clock::time_point start;
    {
        const Mode m = mode(v.mode);
        const std::string path(v.path);
        std::shared_ptr<const Reverse> reverse;
        std::shared_ptr<Account> account;
        std::unique_ptr<Builder> builder;
        if (path == "ready") {
            const auto prep = Clock::now();
            reverse = build(c.graph);
            st.prior = ns(prep);
        }
        // Match the historical window: graph loading, oracle and this reserve
        // are outside total_ns; real workspace/cache allocation is inside it.
        std::vector<Result> outputs;
        outputs.reserve(q + 1);
        start = Clock::now();
        {
            consumer::Workspace workspace(c.graph->n(), !m.push);
            Executor executor(c.graph, reverse, m, 32ULL << 20, false, !m.push);
            outputs.push_back(executor.run_a(c.sources[0], workspace, st.a_compute).first);
            st.a_done = ns(start);
            if (path == "deferred") {
                account = std::make_shared<Account>(32ULL << 20);
                builder = std::make_unique<Builder>(c.graph, account);
                builder->finish();
                reverse = builder->take();
            }
            if (!m.push) {
                executor.bind_reverse(reverse);
                st.b_ready = ns(start);
            }
            for (U i = 1; i <= q; ++i) outputs.push_back(executor.run(c.sources[i], workspace).first);
            st.total = ns(start);
            st.payload = c.graph->payload_bytes() + workspace.bytes() + executor.cache_bytes()
                + 4ULL * c.graph->n() * (q + 2) + (!m.push ? full_build_payload(*c.graph, false) : 0);
            require(st.payload <= (32ULL << 20), "payload cap");
            const auto validation = Clock::now();
            for (U i = 0; i <= q; ++i) {
                require(outputs[i] && outputs[i]->identity() == c.graph.get(), "owned graph identity");
                require(outputs[i]->source() == c.sources[i], "owned source");
                require(outputs[i]->distance() == c.expected[i], "full distance mismatch");
                for (U j = 0; j < i; ++j) require(outputs[i].get() != outputs[j].get(), "independent output ownership");
                ++st.arrays;
            }
            st.validation = ns(validation);
            if (dump) {
                for (U i = 0; i <= q; ++i) {
                    *dump << "{\"graph\":\"" << c.name << "\",\"mode\":\"" << v.mode
                          << "\",\"path\":\"" << v.path << "\",\"q\":" << q
                          << ",\"query\":" << i << ",\"source\":" << c.sources[i] << ",\"distance\":[";
                    for (U j = 0; j < c.graph->n(); ++j) { if (j) *dump << ','; *dump << outputs[i]->distance()[j]; }
                    *dump << "]}\n";
                }
            }
            const auto release = Clock::now();
            outputs.clear();
            st.release = ns(release);
        }
        // Workspace and executor destruction is charged to cleanup_window_ns.
    }
    // Also includes output vector, reverse, builder and account destruction.
    st.cleanup_window = ns(start);
    st.lifecycle = ns(life);
    return st;
}
int main(int argc, char** argv) {
    try {
        require(argc == 4, "command session/output output");
        auto cases = load();
        std::string command(argv[1]);
        if (command == "correctness") {
            std::ofstream dump(argv[3]);
            require(bool(dump), "dump open");
            L arrays=0;
            for (const auto& c : cases) for (U q : {8, 32}) for (auto v : variants) arrays += service(c, v, q, &dump).arrays;
            std::cout << "{\"status\":\"PASS\",\"arrays\":" << arrays << "}\n";
        } else {
            require(command == "worker", "command");
            int session = std::stoi(argv[2]);
            require(session >= 0 && session < 3, "session");
            std::ofstream csv(argv[3]);
            require(bool(csv), "csv open");
            csv << std::setprecision(17)
                << "session,round,sweep,order_index,graph,mode,path,q,total_ns,a_compute_ns,a_completion_ns,b_ready_ns,historical_prepare_ns,validation_ns,release_ns,payload_upper_bytes,cleanup_window_ns,lifecycle_ns,arrays\n";
            L trials=0, arrays=0;
            for (int round=0; round<7; ++round) for (const auto& c : cases) for (U q : {8, 32}) {
                std::array<unsigned,4> order{};
                for (unsigned i=0; i<4; ++i) order[i]=(i+round+session)%4;
                if ((session+round)%2) std::reverse(order.begin(), order.end());
                for (int sweep=0; sweep<2; ++sweep) {
                    if (sweep) std::reverse(order.begin(), order.end());
                    for (unsigned i=0; i<4; ++i) {
                        const auto v=variants[order[i]];
                        const auto z=service(c,v,q);
                        csv << session << ',' << round << ',' << sweep << ',' << i << ',' << c.name << ','
                            << v.mode << ',' << v.path << ',' << q << ',' << z.total << ',' << z.a_compute << ','
                            << z.a_done << ',' << z.b_ready << ',' << z.prior << ',' << z.validation << ','
                            << z.release << ',' << z.payload << ',' << z.cleanup_window << ',' << z.lifecycle << ',' << z.arrays << '\n';
                        ++trials; arrays+=z.arrays;
                    }
                }
            }
            csv.flush();
            require(bool(csv), "csv write");
            rusage usage{};
            getrusage(RUSAGE_SELF, &usage);
            std::cout << "{\"status\":\"PASS\",\"session\":" << session << ",\"trials\":" << trials
                      << ",\"arrays\":" << arrays << ",\"rss_peak_kib\":" << usage.ru_maxrss << "}\n";
        }
        return 0;
    } catch (const std::exception& e) { std::cerr << "FAIL " << e.what() << '\n'; return 2; }
}
