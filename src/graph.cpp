#include "rcc/v1.hpp"
#include <stdexcept>
namespace rcc_api {
Graph::Graph(std::string id,L v,U n_,std::vector<L> r,std::vector<U> c):identity(std::move(id)),version(v),n(n_),row(std::move(r)),col(std::move(c)) {
 if(identity.empty()||!version||!n||n>0x7fffffff||row.size()!=L(n)+1||row[0]||row.back()!=col.size())throw std::invalid_argument("CSR metadata");
 for(U u=0;u<n;++u)if(row[u]>row[u+1])throw std::invalid_argument("CSR offsets");
 for(U x:col)if(x>=n)throw std::invalid_argument("CSR endpoint");
}
std::shared_ptr<const Graph> Graph::from_edges(std::string id,L v,U n,const std::vector<std::pair<U,U>>& edges){
 std::vector<L> row(L(n)+1);std::vector<U>col(edges.size());
 for(auto [a,b]:edges){if(a>=n||b>=n)throw std::invalid_argument("edge");++row[a+1];}
 for(U u=0;u<n;++u)row[u+1]+=row[u];
 auto cursor=row;
 for(auto [a,b]:edges)col[cursor[a]++]=b;
 return std::make_shared<const Graph>(std::move(id),v,n,std::move(row),std::move(col));
}
}
