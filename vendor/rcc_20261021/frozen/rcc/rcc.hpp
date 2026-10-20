#pragma once
// Reachability Closure Certificates (RCC), CPU reference implementation.
// Exact unweighted directed BFS. No GPU execution; no concurrency guarantee.
// The graph is immutable. Only a completed exact search may publish a bound.
#include <algorithm>
#include <cstdint>
#include <limits>
#include <memory>
#include <stdexcept>
#include <utility>
#include <vector>

namespace rcc {
using Vertex=std::uint32_t;
using Offset=std::uint64_t;

class Graph {
    Vertex n_;
    std::uint64_t version_;
    std::vector<Offset> row_;
    std::vector<Vertex> col_;
public:
    Graph(Vertex n, std::uint64_t version,
          const std::vector<std::pair<Vertex,Vertex>>& edges)
        : n_(n),version_(version),row_(std::size_t(n)+1,0),col_(edges.size()) {
        if (!n || n>Vertex(std::numeric_limits<std::int32_t>::max()) || !version)
            throw std::invalid_argument("nonempty graph / int32 distances / nonzero version required");
        for (auto [u,v]: edges) {
            if (u>=n || v>=n) throw std::invalid_argument("edge endpoint outside graph");
            ++row_[std::size_t(u)+1];
        }
        for (Vertex u=0;u<n;++u) row_[u+1]+=row_[u];
        auto p=row_;
        for (auto [u,v]: edges) col_[p[u]++]=v;
    }
    Vertex n()const noexcept{return n_;}
    Offset m()const noexcept{return col_.size();}
    std::uint64_t version()const noexcept{return version_;}
    const std::vector<Offset>& row()const noexcept{return row_;}
    const std::vector<Vertex>& col()const noexcept{return col_;}
    std::size_t bytes()const noexcept{return row_.capacity()*sizeof(Offset)+col_.capacity()*sizeof(Vertex);}
};
using GraphPtr=std::shared_ptr<const Graph>;
inline GraphPtr checked_graph(GraphPtr g){if(!g)throw std::invalid_argument("null graph");return g;}
struct Workspace {
    std::vector<std::int32_t> distance;
    std::vector<Vertex> queue;
    explicit Workspace(Vertex n):distance(n),queue(n){}
    std::size_t bytes()const noexcept{return distance.capacity()*4+queue.capacity()*4;}
};
struct Run {
    Vertex discovered=0, expanded=0, bound=0;
    std::uint64_t edges_read=0, queued_edges_avoided=0, publish_visits=0, publish_writes=0;
    bool complete=false, stopped_by_bound=false;
};

// Identical queue traversal is shared by the no-certificate and certificate
// variants; the only traversal distinction is its valid stopping upper bound.
// Runtime checks: source, workspace, and reachable-count consistency.
// Budgeted abort is a logical test/embedding feature, not a real-time watchdog.
template<bool Diagnose=false, bool SkipSinks=false>
Run queue_bfs(const Graph& g, Vertex source, Workspace& w, Vertex upper,
              Offset max_expansions=std::numeric_limits<Offset>::max()) {
    if (source>=g.n() || w.distance.size()!=g.n() || w.queue.size()!=g.n())
        throw std::invalid_argument("source or workspace mismatch");
    if (upper==0 || upper>g.n()) throw std::invalid_argument("invalid bound");
    auto* d=w.distance.data();auto* q=w.queue.data();
    const auto* row=g.row().data(); const auto* col=g.col().data();
    std::fill_n(d,g.n(),-1);d[source]=0;
    Vertex head=0,tail=0,discovered=1;
    if constexpr(SkipSinks){if(row[source]!=row[source+1])q[tail++]=source;}
    else q[tail++]=source;
    Run r;r.bound=upper;
    while(head<tail && discovered<upper){
        if(head>=max_expansions){r.discovered=discovered;r.expanded=head;return r;}
        Vertex u=q[head++];const auto nd=d[u]+1;
        for(Offset e=row[u];e<row[u+1];++e){
            if constexpr(Diagnose)++r.edges_read;
            Vertex v=col[e];
            if(d[v]<0){
                d[v]=nd;++discovered;
                if constexpr(SkipSinks){if(row[v]!=row[v+1])q[tail++]=v;}
                else q[tail++]=v;
            }
        }
    }
    if(discovered>upper)throw std::logic_error("invalid reachability certificate");
    r.discovered=discovered;r.expanded=head;r.complete=true;
    r.stopped_by_bound=discovered==upper && head<tail;
    if constexpr(Diagnose)for(Vertex j=head;j<tail;++j)r.queued_edges_avoided+=row[q[j]+1]-row[q[j]];
    return r;
}

// Unmodified queue-push baseline: no early termination.
template<bool Diagnose=false>
Run plain_bfs(const Graph& g, Vertex source, Workspace& w) {
    if(source>=g.n() || w.distance.size()!=g.n() || w.queue.size()!=g.n())
        throw std::invalid_argument("source/workspace");
    auto* d=w.distance.data();auto* q=w.queue.data();const auto* row=g.row().data();const auto* col=g.col().data();
    std::fill_n(d,g.n(),-1);d[source]=0;Vertex head=0,tail=1;q[0]=source;Run r;r.bound=g.n();
    while(head<tail){Vertex u=q[head++];const auto nd=d[u]+1;
        for(Offset e=row[u];e<row[u+1];++e){if constexpr(Diagnose)++r.edges_read;Vertex v=col[e];
            if(d[v]<0){d[v]=nd;q[tail++]=v;}}
    }
    r.discovered=tail;r.expanded=head;r.complete=true;return r;
}

// V0: generalizes the n-vertices stopping test using the *last completed*
// search's reachable-set membership. No certificate-building edge scan.
// It retains one extra n-entry distance buffer; this memory is NOT free.
// distance() is valid until the next run/reset. Single-owner, serial queries.
class LastClosure {
    GraphPtr graph_;
    std::vector<std::int32_t> previous_;
    Vertex previous_count_=0;
public:
    explicit LastClosure(GraphPtr g):graph_(checked_graph(std::move(g))),previous_(graph_->n(),-1){}
    void reset() {previous_count_=0;std::fill(previous_.begin(),previous_.end(),-1);}
    Vertex bound(Vertex s)const {
        if(s>=graph_->n())throw std::out_of_range("source");
        return previous_count_ && previous_[s]>=0 ? previous_count_ : graph_->n();
    }
    const std::vector<std::int32_t>& distance()const noexcept{return previous_;}
    std::size_t bytes()const noexcept{return previous_.capacity()*sizeof(std::int32_t);}
    void release_result(Workspace& w) { previous_.swap(w.distance); previous_count_=0; }
    template<bool Diagnose=false> Run run(Vertex s, Workspace& w) {
        Run r=queue_bfs<Diagnose>(*graph_,s,w,bound(s));
        previous_.swap(w.distance);previous_count_=r.discovered;return r;
    }
};

// V1: persistent upper-bound table. Default bound n is always valid.
// If a search from s reaches exactly R, then for every u in R:
// Reach(u) subseteq R; |Reach(u)| <= |R|. Publishing min(old,|R|) is safe.
// A new query stops only if discovered == bound[source].
// No future query/source or true future reachability count is consulted.
class ClosureTable {
    GraphPtr graph_;
    std::vector<Vertex> upper_;
    std::size_t updates_left_;
    bool enabled_;
public:
    // A payload cap below 4*n selects safe no-certificate fallback.
    explicit ClosureTable(GraphPtr g,
          std::size_t payload_cap=std::numeric_limits<std::size_t>::max(),
          std::size_t update_budget=std::numeric_limits<std::size_t>::max())
        :graph_(checked_graph(std::move(g))),updates_left_(update_budget),enabled_(std::size_t(graph_->n())*sizeof(Vertex)<=payload_cap) {
        if(enabled_)upper_.assign(graph_->n(),graph_->n());
    }
    const Graph& graph()const noexcept{return *graph_;}
    bool enabled()const noexcept{return enabled_;}
    std::size_t bytes()const noexcept{return upper_.capacity()*sizeof(Vertex);}
    const std::vector<Vertex>& debug_upper()const noexcept{return upper_;}
    Vertex bound(Vertex s)const {
        if(s>=graph_->n())throw std::out_of_range("source");
        return enabled_?upper_[s]:graph_->n();
    }
    void reset(std::size_t update_budget=std::numeric_limits<std::size_t>::max()){
        if(enabled_) std::fill(upper_.begin(),upper_.end(),graph_->n());
        updates_left_=update_budget;
    }
    // Graph replacement requires a fresh object; graph_ pins immutable identity.
    // An incomplete/aborted BFS never publishes, even if partial nodes are valid.
    template<bool Diagnose=false> Run run(Vertex s, Workspace& w,
                Offset max_expansions=std::numeric_limits<Offset>::max()) {
        const Vertex before=bound(s);
        Run r=queue_bfs<Diagnose>(*graph_,s,w,before,max_expansions);
        if(!r.complete || !enabled_ || r.discovered>=before || updates_left_==0) return r;
        // queue contains all discovered vertices (no sink filtering here).
        std::size_t num=std::min<std::size_t>(r.discovered,updates_left_);
        for(std::size_t k=0;k<num;++k){
            Vertex u=w.queue[k];
            if constexpr(Diagnose)++r.publish_visits;
            if(upper_[u]>r.discovered){upper_[u]=r.discovered;if constexpr(Diagnose)++r.publish_writes;}
        }
        if(updates_left_!=std::numeric_limits<std::size_t>::max())updates_left_-=num;
        return r;
    }
};

// Trusted output import is deliberately NOT exposed: claiming that an arbitrary
// partially explored set is a closure would be unsound. Use run() to publish.
} // namespace rcc
