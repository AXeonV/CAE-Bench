// Trusted adapter; Cantera API computes every returned quantity.
#include "cantera/thermo/PlasmaPhase.h"
#include "cantera/thermo/ThermoFactory.h"
#include <iostream>
#include <iomanip>
using namespace Cantera;
int main() {
 try {
  size_t n; std::cin>>n;
  std::cout<<std::setprecision(17)<<"[";
  for(size_t i=0;i<n;i++) {
   int mode; double t,te,v,te2,x[3];
   std::cin>>mode>>t>>te>>v>>te2>>x[0]>>x[1]>>x[2];
   auto phase = newThermo("/opt/repair-driver/plasma.yaml","plasma");
   ThermoPhase& p = *phase;
   p.setMoleFractions(x); p.setElectronTemperature(te);
   if(mode==0) p.setState_TD(t,v); else p.setState_TP(t,v);
   p.setElectronTemperature(te2);
   if(mode==1) p.setPressure(v);
   if(i)std::cout<<",";
   std::cout<<"["<<p.pressure()<<","<<dynamic_cast<PlasmaPhase&>(p).electronPressure()<<","<<p.density();
   for(size_t k=0;k<3;k++)std::cout<<","<<p.concentration(k);
   std::cout<<"]";
  }
  std::cout<<"]\n";
 }catch(std::exception& e){std::cerr<<e.what()<<"\n";return 1;}
}
