#include <meep.hpp>
#include <iostream>
#include <fstream>
#include <iomanip>
#include <memory>
#include <vector>
#include <stdexcept>
using namespace meep;
static double c2value,c3value,region_lo,region_hi;
double eps(const vec&){return 1.;}
double c2(const vec& p){return p.z()>=region_lo && p.z()<=region_hi ? c2value:0.;}
double c3(const vec& p){return p.z()>=region_lo && p.z()<=region_hi ? c3value:0.;}
int main(int argc,char**argv){initialize init(argc,argv);verbosity=0;
 try{double length,res,pml_width,fc,df,amp,cutoff,after,monitor;int nchunks,stride,nfreq;
 if(!(std::cin>>length>>res>>pml_width>>fc>>df>>amp>>cutoff>>after>>c2value>>c3value>>region_lo>>region_hi>>nchunks>>stride>>monitor>>nfreq))throw std::runtime_error("Invalid trusted payload");
 std::vector<double> frequencies(nfreq);for(double& q:frequencies)std::cin>>q;
 grid_volume gv=vol1d(length,res);gv.center_origin();structure material(gv,eps,pml(pml_width),identity(),nchunks);material.set_chi2(c2);material.set_chi3(c3);fields simulation(&material);simulation.use_real_fields();
 gaussian_src_time source(fc,df,cutoff);simulation.add_point_source(Ex,source,vec(-length*.5+pml_width),amp);vec point(monitor);component components[2]={Ex,Hy};
 auto observation=simulation.add_dft_fields(components,2,volume(point),frequencies,true,stride);
 dft_chunk* chunks[2]={nullptr,nullptr};
 for(auto* chunk=observation.chunks;chunk;chunk=chunk->next_in_dft){int k=chunk->c==Ex?0:chunk->c==Hy?1:-1;if(k<0 || chunks[k] || chunk->N!=1)throw std::runtime_error("Observation must be one genuine Yee-aligned sample per component");chunks[k]=chunk;}
 if(chunks[0] && chunks[1] && chunks[0]->get_decimation_factor()!=chunks[1]->get_decimation_factor())throw std::runtime_error("Inconsistent real observation strides");
 if(!chunks[0] || !chunks[1])throw std::runtime_error("Missing actual field accumulator");
 std::unique_ptr<std::ofstream> trace;if(argc==2){trace=std::make_unique<std::ofstream>(argv[1]);*trace<<std::setprecision(17)<<"time,e,h\n";}
 while(simulation.time()<simulation.last_source_time()+after){simulation.step();if(trace)*trace<<simulation.time()<<","<<simulation.get_field(Ex,point).real()<<","<<simulation.get_field(Hy,point).real()<<"\n";}
 std::cout<<std::setprecision(17)<<"{\"dt\":"<<simulation.dt<<",\"final_time\":"<<simulation.time()<<",\"stride\":"<<chunks[0]->get_decimation_factor()<<",\"spectrum\":[";
 for(int i=0;i<nfreq;++i){if(i)std::cout<<",";std::cout<<"[";for(int k=0;k<2;++k){if(k)std::cout<<",";auto v=chunks[k]->dft[i];std::cout<<v.real()<<","<<v.imag();}std::cout<<"]";}std::cout<<"]}\n";
 }catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}
