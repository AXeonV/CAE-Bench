// Trusted Cantera API adapter; no analytic correction or reference lookup.
#include "cantera/base/Solution.h"
#include "cantera/base/Interface.h"
#include "cantera/base/AnyMap.h"
#include "cantera/thermo/ThermoPhase.h"
#include "cantera/thermo/SurfPhase.h"
#include "cantera/kinetics/Kinetics.h"
#include "cantera/zeroD/FlowReactor.h"
#include "cantera/zeroD/ReactorSurface.h"
#include "cantera/zeroD/ReactorNet.h"
#include <iostream>
#include <iomanip>
using namespace Cantera;
int main(){try{
 size_t n;std::cin>>n;std::cout<<std::setprecision(17)<<"[";
 std::vector<std::vector<string>> orders={{"A","B","I"},{"A","I","B"},{"B","A","I"},{"B","I","A"},{"I","A","B"},{"I","B","A"}};
 for(size_t row=0;row<n;row++){
  int order;double T,P,u,a,n0,ka,kd,kc,z,x[3],theta[2]={.5,.5};int raw=0;
  std::cin>>order>>T>>P>>u>>a>>n0>>ka>>kd>>kc>>z>>x[0]>>x[1]>>x[2];
  std::cin>>theta[0]>>theta[1]>>raw;
  auto root=AnyMap::fromYamlFile("/opt/cantera1996-driver/mechanism.yaml");
  auto& phases=root["phases"].asVector<AnyMap>();phases[0]["species"]=orders.at(order);
  auto gas=newSolution(phases[0],root,"none");
  auto surface=newInterface(phases[1],root,std::vector<std::shared_ptr<Solution>>{gas});
  auto& g=*gas->thermo();auto& s=dynamic_cast<SurfPhase&>(*surface->thermo());
  g.setState_TPX(T,P,Composition{{"A",x[0]},{"B",x[1]},{"I",x[2]}});
  s.setState_TP(T,P);s.setSiteDensity(n0);
  auto& kin=*surface->kinetics();kin.setMultiplier(0,ka/1e12);kin.setMultiplier(1,kd/1e4);kin.setMultiplier(2,kc/1e4);
  if(raw)s.setCoveragesNoNorm(theta);else s.setCoverages(theta);
  double direct_c[2],direct_rop[3];s.getConcentrations(direct_c);kin.getFwdRatesOfProgress(direct_rop);double direct_density=s.density();
  s.setCoverages(theta);
  FlowReactor r(gas);r.setArea(1e-4);r.setMassFlowRate(u*g.density()*r.area());r.setSurfaceAreaToVolumeRatio(a);r.setEnergy(0);r.setInletSurfaceRtol(1e-7);r.setInletSurfaceAtol(1e-12);
  ReactorSurface rs;rs.setKinetics(surface->kinetics().get());r.addSurface(&rs);
  ReactorNet net;net.addReactor(r);net.setTolerances(1e-9,1e-12);net.setMaxSteps(20000);net.advance(z);
  double final_theta[2];rs.getCoverages(final_theta);
  if(row)std::cout<<",";
  std::cout<<"["<<g.massFraction(g.speciesIndex("A"))<<","<<g.massFraction(g.speciesIndex("B"))<<","<<g.massFraction(g.speciesIndex("I"))<<","<<final_theta[0]<<","<<final_theta[1]<<","<<g.pressure()<<","<<g.density()<<","<<r.speed();
  double final_c[2];s.getConcentrations(final_c);
  for(double v:direct_c)std::cout<<","<<v;std::cout<<","<<direct_density;
  for(double v:direct_rop)std::cout<<","<<v;for(double v:final_c)std::cout<<","<<v;
  std::cout<<"]";
 }
 std::cout<<"]\n";
}catch(std::exception& e){std::cerr<<e.what()<<"\n";return 1;}}
