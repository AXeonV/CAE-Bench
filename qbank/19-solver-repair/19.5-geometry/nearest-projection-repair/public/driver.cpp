#include <Eigen/Core>
#include <algorithm>
#include <iostream>
#include <vector>
#include "nlohmann/json.hpp"
#include "logging/LogConfiguration.hpp"
#include "mesh/Mesh.hpp"
#include "query/Index.hpp"
using json=nlohmann::json;
int main(){try{
  precice::logging::setupLogging(precice::logging::LoggingConfiguration{},false);
  json a;std::cin>>a;int d=a.at("dimension");
  precice::mesh::Mesh mesh("source",d,0);
  for(const auto& v:a.at("vertices")){Eigen::VectorXd x(d);for(int k=0;k<d;++k)x(k)=v.at(k).get<double>();mesh.createVertex(x);}
  for(const auto& e:a.at("edges"))mesh.createEdge(mesh.vertices().at(e.at(0)),mesh.vertices().at(e.at(1)));
  for(const auto& f:a.at("triangles"))mesh.createTriangle(mesh.vertices().at(f.at(0)),mesh.vertices().at(f.at(1)),mesh.vertices().at(f.at(2)));
  for(const auto& t:a.at("tetrahedra"))mesh.createTetrahedron(mesh.vertices().at(t.at(0)),mesh.vertices().at(t.at(1)),mesh.vertices().at(t.at(2)),mesh.vertices().at(t.at(3)));
  int n=std::max({1,int(mesh.edges().size()),int(mesh.triangles().size())});json out=json::array();
  for(const auto& q:a.at("queries")){
    Eigen::VectorXd x(d);for(int k=0;k<d;++k)x(k)=q.at(k).get<double>();
    auto match=a.at("mode")=="nearest"?mesh.index().findNearestProjection(x,n):mesh.index().findCellOrProjection(x,n);
    std::vector<double>w(mesh.vertices().size(),0),point(d,0),value(3,0);
    for(const auto& e:match.polation.getWeightedElements())w.at(e.vertexID)+=e.weight;
    for(size_t i=0;i<w.size();++i){for(int k=0;k<d;++k)point[k]+=w[i]*a.at("vertices").at(i).at(k).get<double>();for(int k=0;k<3;++k)value[k]+=w[i]*a.at("values").at(i).at(k).get<double>();}
    out.push_back({{"point",point},{"distance",match.polation.distance()},{"weights",w},{"value",value}});
  }
  std::cout<<out.dump()<<std::endl;
}catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 1;}}
