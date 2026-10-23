#include <meep.hpp>
#include <iostream>
#include <iomanip>
#include <cstdlib>
#include <fstream>
#include <memory>
using namespace meep;
double one(const vec&){return 1;}
int main(int argc,char**argv){initialize init(argc,argv);verbosity=0;
 try{double radius,height,rpml,zpml,res,m,amplitude,tau,cutoff,after;
 if(!(std::cin>>radius>>height>>rpml>>zpml>>res>>m>>amplitude>>tau>>cutoff>>after))throw std::runtime_error("Invalid trusted payload");
 grid_volume gv=volcyl(radius+rpml,2*(height+zpml),res);gv.center_origin();structure s(gv,one,pml(rpml,R)+pml(zpml,Z));fields f(&s,m);
 gaussian_src_time src(1,1/tau,cutoff);f.add_point_source(Er,src,veccyl(0,0),amplitude);
 auto a=f.add_dft_flux(Z,volume(veccyl(0,height),veccyl(radius,height)),1,1,1,true,true,1);
 auto b=f.add_dft_flux(R,volume(veccyl(radius,-height),veccyl(radius,height)),1,1,1,true,true,1);
 auto c=f.add_dft_flux(Z,volume(veccyl(0,-height),veccyl(radius,-height)),1,1,1,true,true,1);
 component cs[6]={Er,Ep,Ez,Hr,Hp,Hz};double frequency[1]={1};vec point=gv[iveccyl(2*int(res)+1,1)];auto fields_dft=f.add_dft_fields(cs,6,volume(point),frequency,1,true,1);dft_chunk* chunks[6]={};for(auto*q=fields_dft.chunks;q;q=q->next_in_dft){int k=0;while(k<6 && q->c!=cs[k])++k;if(k==6||chunks[k]||q->N!=1)throw std::runtime_error("Expected one native centered sample");chunks[k]=q;}
 std::unique_ptr<std::ofstream> trace;if(argc==2){trace=std::make_unique<std::ofstream>(argv[1]);*trace<<std::setprecision(17)<<"time,Er_re,Er_im,Ep_re,Ep_im,Ez_re,Ez_im,Hr_re,Hr_im,Hp_re,Hp_im,Hz_re,Hz_im\n";}
 while(f.time()<f.last_source_time()+after){f.step();if(trace){*trace<<f.time();for(auto field:cs){auto value=f.get_field(field,point);*trace<<","<<value.real()<<","<<value.imag();}*trace<<"\n";}}double*A=a.flux(),*B=b.flux(),*C=c.flux();
 std::cout<<std::setprecision(17)<<"{\"m\":"<<m<<",\"R\":"<<radius<<",\"Z\":"<<height<<",\"pml\":"<<rpml<<",\"resolution\":"<<res<<",\"flux\":["<<A[0]<<","<<B[0]<<","<<-C[0]<<"],\"time\":"<<f.time()<<",\"dt\":"<<f.dt<<",\"probe\":["<<point.r()<<","<<point.z()<<"],\"fields\":[";for(int k=0;k<6;k++){if(k)std::cout<<",";if(!chunks[k])throw std::runtime_error("Missing native field");auto v=chunks[k]->dft[0];std::cout<<"["<<v.real()<<","<<v.imag()<<"]";}std::cout<<"]}\n";delete[]A;delete[]B;delete[]C; }catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}
