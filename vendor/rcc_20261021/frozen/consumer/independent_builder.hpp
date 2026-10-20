#pragma once
#include <algorithm>
#include <atomic>
#include <cstdint>
#include <fstream>
#include <limits>
#include <memory>
#include <mutex>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace independent {
using U=std::uint32_t; using L=std::uint64_t;
inline void require(bool b,const char* text){if(!b)throw std::runtime_error(text);}
inline L add_checked(L a,L b){if(b>std::numeric_limits<L>::max()-a)throw std::overflow_error("byte/offset sum");return a+b;}
inline L mul_checked(L a,L b){if(a&&b>std::numeric_limits<L>::max()/a)throw std::overflow_error("byte product");return a*b;}

// Payload allocations are tracked. C++ allocator headers/control blocks and RSS are separate.
struct Account {
    mutable std::mutex mutex; L current=0,peak=0,allocated=0,calls=0,limit; long fail_after=-1;
    explicit Account(L cap):limit(cap){}
    void take(L bytes){std::lock_guard<std::mutex> l(mutex);if((fail_after>=0&&calls>=L(fail_after))||bytes>limit-current)throw std::bad_alloc();++calls;current+=bytes;allocated=add_checked(allocated,bytes);peak=std::max(peak,current);}
    void give(L bytes){std::lock_guard<std::mutex> l(mutex);require(bytes<=current,"account underflow");current-=bytes;}
    L live()const{std::lock_guard<std::mutex> l(mutex);return current;}
};
template<class T> class Buffer {
    std::shared_ptr<Account> account_;std::unique_ptr<T[]> data_;std::size_t size_=0;
public:
    Buffer()=default;
    Buffer(std::shared_ptr<Account> a,std::size_t n,bool zero=false):account_(std::move(a)),size_(n){
        const L bytes=mul_checked(n,sizeof(T));if(!n)return;account_->take(bytes);
        try{data_.reset(new T[n]);}catch(...){account_->give(bytes);throw;}
        if(zero)std::fill_n(data_.get(),n,T{});
    }
    Buffer(const Buffer&)=delete;Buffer&operator=(const Buffer&)=delete;
    Buffer(Buffer&& b)noexcept:account_(std::move(b.account_)),data_(std::move(b.data_)),size_(b.size_){b.size_=0;}
    Buffer&operator=(Buffer&& b)noexcept{if(this!=&b){clear();account_=std::move(b.account_);data_=std::move(b.data_);size_=b.size_;b.size_=0;}return *this;}
    ~Buffer(){clear();}
    void clear()noexcept{if(data_){data_.reset();account_->give(L(size_)*sizeof(T));}size_=0;}
    T&operator[](std::size_t i){return data_[i];}const T&operator[](std::size_t i)const{return data_[i];}
    std::size_t size()const{return size_;}T*data(){return data_.get();}const T*data()const{return data_.get();}
};

class Graph {
    U n_;L version_;std::vector<L> row_;std::vector<U> col_;
public:
    Graph(U n,L version,const std::vector<std::pair<U,U>>& edges):n_(n),version_(version),row_(std::size_t(n)+1,0),col_(edges.size()){
        require(version>0,"zero graph version");require(edges.size()<=std::numeric_limits<U>::max(),"CPU fixture edge ABI limit");
        for(auto e:edges){require(e.first<n&&e.second<n,"invalid edge endpoint");++row_[e.first+1];}
        for(U v=0;v<n;++v){row_[v+1]+=row_[v];}
        auto cursor=row_;
        for(auto e:edges)col_[cursor[e.first]++]=e.second;
    }
    U n()const{return n_;}L m()const{return col_.size();}L version()const{return version_;}
    const std::vector<L>&row()const{return row_;}const std::vector<U>&col()const{return col_;}
    L payload_bytes()const{return L(row_.capacity())*8+L(col_.capacity())*4;}
    static std::shared_ptr<const Graph> load(const std::string& path,U n,L version){
        std::ifstream f(path);require(bool(f),"fixture open");std::vector<std::pair<U,U>> edges;std::string line;
        while(std::getline(f,line)){if(line.empty()||line[0]=='#'||line[0]=='%')continue;auto p=line.find_first_of(" \t");require(p!=std::string::npos,"edge syntax");unsigned long a=std::stoul(line.substr(0,p)),b=std::stoul(line.substr(p));require(a<n&&b<n,"edge range");edges.emplace_back(U(a),U(b));}
        return std::make_shared<const Graph>(n,version,edges);
    }
};

struct BfsWorkspace {std::vector<int> distance;std::vector<U> queue;explicit BfsWorkspace(U n):distance(n),queue(n){}L bytes()const{return 4*(L(distance.capacity())+queue.capacity());}};
// Plan A only reads Graph and owns its BFS workspace. No preparation callback or queue.
inline void plan_a(const Graph& g,U source,BfsWorkspace& w){
    require(source<g.n(),"BFS source");std::fill(w.distance.begin(),w.distance.end(),-1);w.distance[source]=0;L head=0,tail=1;w.queue[0]=source;
    while(head<tail){U u=w.queue[head++];for(L e=g.row()[u];e<g.row()[u+1];++e){U v=g.col()[e];if(w.distance[v]<0){w.distance[v]=w.distance[u]+1;w.queue[tail++]=v;}}}
}

class Builder;class LegacyReference;
class Reverse {
    friend class Builder;friend class LegacyReference;
    std::shared_ptr<const Graph> graph_;Buffer<L> row_;Buffer<U> source_,edge_;
public:
    Reverse(std::shared_ptr<const Graph> g,std::shared_ptr<Account> a,bool provenance):graph_(std::move(g)),row_(a,L(graph_->n())+1),source_(a,graph_->m()),edge_(a,provenance?graph_->m():0){}
    const Graph&graph()const{return *graph_;}const std::shared_ptr<const Graph>&graph_ptr()const{return graph_;}
    const L*row()const{return row_.data();}const U*source()const{return source_.data();}const U*edge_ids()const{return edge_.data();}
    bool has_provenance()const{return edge_.size()!=0;}
    L payload_bytes()const{return L(row_.size())*8+4*(L(source_.size())+edge_.size());}
};
inline void followup(const Reverse& r,U source,BfsWorkspace& w){
    require(source<r.graph().n(),"BFS source");std::fill(w.distance.begin(),w.distance.end(),-1);w.distance[source]=0;
    U level=0;bool changed=true;while(changed){changed=false;for(U v=0;v<r.graph().n();++v)if(w.distance[v]<0){for(L p=r.row()[v];p<r.row()[v+1];++p)if(w.distance[r.source()[p]]==int(level)){w.distance[v]=int(level)+1;changed=true;break;}}++level;require(level<=L(r.graph().n())+1,"BFS termination");}
}

enum class Stage {COUNT,SCAN,CURSOR,SCATTER,VERIFY,COMPLETE,CANCELLED,FAILED,PUBLISHED};
inline const char*name(Stage s){switch(s){case Stage::COUNT:return "COUNT";case Stage::SCAN:return "SCAN";case Stage::CURSOR:return "CURSOR";case Stage::SCATTER:return "SCATTER";case Stage::VERIFY:return "VERIFY";case Stage::COMPLETE:return "COMPLETE";case Stage::CANCELLED:return "CANCELLED";case Stage::FAILED:return "FAILED";case Stage::PUBLISHED:return "PUBLISHED";}return "INVALID";}
struct Progress {L counted,scanned,scattered;Stage stage;};
class Builder {
    std::shared_ptr<const Graph> graph_;std::shared_ptr<Account> account_;bool provenance_;
    Buffer<L> counts_,cursor_;std::shared_ptr<Reverse> out_;
    Stage stage_=Stage::COUNT;L count_=0,scan_=0,cursor_at_=0,scatter_=0,verify_=0;U source_=0;
    std::atomic<bool> cancelled_{false};std::atomic<L> counted_{0},scanned_{0},scattered_{0};std::atomic<Stage> visible_{Stage::COUNT};
    void checkpoint(){counted_.store(count_,std::memory_order_release);scanned_.store(scan_,std::memory_order_release);scattered_.store(scatter_,std::memory_order_release);visible_.store(stage_,std::memory_order_release);}
public:
    Builder(std::shared_ptr<const Graph> g,std::shared_ptr<Account> a,bool provenance=false):graph_(std::move(g)),account_(std::move(a)),provenance_(provenance),counts_(account_,graph_->n(),true){}
    Builder(const Builder&)=delete;Builder&operator=(const Builder&)=delete;
    void cancel(){cancelled_.store(true,std::memory_order_release);}
    Progress progress()const{return {counted_.load(std::memory_order_acquire),scanned_.load(std::memory_order_acquire),scattered_.load(std::memory_order_acquire),visible_.load(std::memory_order_acquire)};}
    Stage stage()const{return stage_;} // owner thread only; concurrent readers use progress()
    void step(L operations,bool count_only=false){
        if(stage_==Stage::FAILED||stage_==Stage::CANCELLED||stage_==Stage::PUBLISHED)return;
        try{while(operations--&&stage_!=Stage::COMPLETE){
            if(cancelled_.load(std::memory_order_acquire)){stage_=Stage::CANCELLED;break;}
            if(stage_==Stage::COUNT){if(count_<graph_->m()){++counts_[graph_->col()[count_++]];}else{if(count_only)break;out_=std::make_shared<Reverse>(graph_,account_,provenance_);out_->row_[0]=0;stage_=Stage::SCAN;}}
            else if(stage_==Stage::SCAN){if(scan_<graph_->n()){out_->row_[scan_+1]=add_checked(out_->row_[scan_],counts_[scan_]);++scan_;}else{require(out_->row_[graph_->n()]==graph_->m(),"histogram sum");cursor_=Buffer<L>(account_,graph_->n());stage_=Stage::CURSOR;}}
            else if(stage_==Stage::CURSOR){if(cursor_at_<graph_->n()){cursor_[cursor_at_]=out_->row_[cursor_at_];++cursor_at_;}else{stage_=Stage::SCATTER;}}
            else if(stage_==Stage::SCATTER){if(scatter_<graph_->m()){while(source_<graph_->n()&&scatter_>=graph_->row()[source_+1])++source_;require(source_<graph_->n(),"source range");U v=graph_->col()[scatter_];L at=cursor_[v]++;require(at<out_->row_[v+1],"scatter range");out_->source_[at]=source_;if(provenance_)out_->edge_[at]=U(scatter_);++scatter_;}else stage_=Stage::VERIFY;}
            else if(stage_==Stage::VERIFY){if(verify_<graph_->n()){require(cursor_[verify_]==out_->row_[verify_+1],"scatter completeness");++verify_;}else stage_=Stage::COMPLETE;}
        }}catch(...){stage_=Stage::FAILED;checkpoint();throw;}checkpoint();
    }
    void finish(){while(stage_!=Stage::COMPLETE&&stage_!=Stage::FAILED&&stage_!=Stage::CANCELLED&&stage_!=Stage::PUBLISHED)step(4096);}
    void prepare_counts(){while(count_<graph_->m()&&stage_==Stage::COUNT)step(4096,true);checkpoint();}
    std::shared_ptr<const Reverse> take(){require(stage_==Stage::COMPLETE&&!cancelled_.load(std::memory_order_acquire),"partial/failed/cancelled state cannot publish");std::shared_ptr<const Reverse> ready=out_;out_.reset();counts_.clear();cursor_.clear();stage_=Stage::PUBLISHED;checkpoint();return ready;}
};

// Publication changes only a fully immutable object. Old shared readers retain ownership.
class Catalog {
public:struct Ticket {std::shared_ptr<const Graph> graph;L epoch;};
private:
    mutable std::mutex mutex_;std::shared_ptr<const Graph> graph_;L epoch_=0;std::shared_ptr<const Reverse> ready_;
public:
    explicit Catalog(std::shared_ptr<const Graph> graph):graph_(std::move(graph)){}
    Ticket begin(){std::lock_guard<std::mutex> l(mutex_);require(epoch_<std::numeric_limits<L>::max(),"generation wrap");return {graph_,++epoch_};}
    void replace(std::shared_ptr<const Graph> graph){std::lock_guard<std::mutex> l(mutex_);require(graph->version()>graph_->version(),"version must increase");require(epoch_<std::numeric_limits<L>::max(),"generation wrap");graph_=std::move(graph);++epoch_;ready_.reset();}
    bool publish(const Ticket& ticket,std::shared_ptr<const Reverse> value){std::lock_guard<std::mutex> l(mutex_);if(!value||ticket.epoch!=epoch_||ticket.graph.get()!=graph_.get()||value->graph_ptr().get()!=graph_.get())return false;ready_=std::move(value);return true;}
    std::shared_ptr<const Reverse> acquire(L version)const{std::lock_guard<std::mutex> l(mutex_);return ready_&&version==graph_->version()?ready_:nullptr;}
};

inline L fixed_service_bytes(const Graph&g){return add_checked(g.payload_bytes(),mul_checked(g.n(),8));}
inline L full_build_payload(const Graph&g,bool provenance){return add_checked(mul_checked(g.n(),24)+8,mul_checked(g.m(),provenance?8:4));}
inline L minimum_final_payload(const Graph&g){return add_checked(mul_checked(L(g.n())+1,8),mul_checked(g.m(),4));}
} // namespace independent
