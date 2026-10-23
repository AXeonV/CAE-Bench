#include "SU2_CFD/include/numerics_simd/flow/convection/common.hpp"
#include "Common/include/CConfig.hpp"
#include <iostream>
#include <sstream>
#include <iomanip>

template<size_t D> void run_one() {
 using Var=CCompressiblePrimitives<D,D+4>;
 double gamma,R,kappa,relax;int muscl,lim;
 std::cin>>gamma>>R>>kappa>>relax>>muscl>>lim;
 std::ostringstream cfg;cfg<<"SOLVER= NAVIER_STOKES\nMATH_PROBLEM= DIRECT\nMACH_NUMBER= .2\nREYNOLDS_NUMBER= 5e6\nCONV_NUM_METHOD_FLOW= ROE\nMUSCL_FLOW= YES\nSLOPE_LIMITER_FLOW= VENKATAKRISHNAN\n";
 std::istringstream buf(cfg.str());auto* saved=std::cout.rdbuf(std::cerr.rdbuf());CConfig config(buf,SU2_COMPONENT::SU2_CFD,false);std::cout.rdbuf(saved);
 su2double velocity[3]={1,0,0};CNSVariable nodes(1,velocity,3e5,2,D,D+2,&config);
 nodes.NonPhysicalEdgeCounter.resize(Double::Size)=0;
 CPair<Var> base;VectorDbl<D> dx;
 for(size_t d=0;d<D;++d){double v;std::cin>>v;dx(d)=v;}
 for(size_t side=0;side<2;++side){auto& v=side?base.j:base.i;
  for(size_t k=0;k<D+4;++k){double x;std::cin>>x;v.all(k)=x;}
  for(size_t k=0;k<D+2;++k)for(size_t d=0;d<D;++d){double x;std::cin>>x;nodes.GetGradient_Reconstruction(side)(k,d)=x;}
  for(size_t k=0;k<D+2;++k){double x;std::cin>>x;nodes.GetLimiter_Primitive()(side,k)=x;}
 }
 Int edge,ip,jp;for(size_t lane=0;lane<Double::Size;++lane){edge[lane]=lane;ip[lane]=0;jp[lane]=1;}
 LIMITER lt=lim==0?LIMITER::NONE:lim==1?LIMITER::VAN_ALBADA_EDGE:LIMITER::VENKATAKRISHNAN;
 auto result=reconstructPrimitives<Var>(edge,ip,jp,gamma,R,muscl,kappa,relax,lt,base,dx,nodes);
 std::cout<<'[';for(size_t side=0;side<2;++side){if(side)std::cout<<',';auto& v=side?result.j:result.i;auto u=compressibleConservatives(v);std::cout<<'[';
  for(size_t k=0;k<D+4;++k){if(k)std::cout<<',';std::cout<<v.all(k)[0];}
  for(size_t k=0;k<D+2;++k)std::cout<<','<<u.all(k)[0];std::cout<<']';
 }std::cout<<']';
}
int main(){std::cout<<std::setprecision(17);int n;if(!(std::cin>>n))return 2;std::cout<<'[';for(int i=0;i<n;++i){if(i)std::cout<<',';int dim;std::cin>>dim;if(dim==2)run_one<2>();else run_one<3>();}std::cout<<"]\n";}
