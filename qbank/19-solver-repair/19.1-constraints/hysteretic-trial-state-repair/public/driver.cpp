#include <HystereticMaterial.h>
#include <HystereticSMMaterial.h>
#include <StandardStream.h>
#include <OPS_Globals.h>
#include <Vector.h>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <memory>
#include <stdexcept>
#include <vector>
StandardStream sserr;
OPS_Stream *opserrPtr = &sserr;

template<class M> void execute(M& m,std::istream& in,std::ostream& out){
 int nh,nq,nc;double delta,rollback;
 in>>nh;for(int j=0;j<nh;++j){double e;in>>e;if(m.setTrialStrain(e)||m.commitState())throw std::runtime_error("history API failure");}
 auto observe=[&](){out<<m.getStrain()<<' '<<m.getStress()<<' '<<m.getTangent()<<' '<<m.getEnergy()<<'\n';};
 observe();double committed=m.getStrain();
 in>>nq;for(int j=0;j<nq;++j){double e;in>>e;if(m.setTrialStrain(e))throw std::runtime_error("trial API failure");}
 in>>delta;if(m.setTrialStrain(committed+delta))throw std::runtime_error("return API failure");observe();
 if(m.commitState())throw std::runtime_error("accept API failure");observe();
 in>>nc;for(int j=0;j<nc;++j){double e;in>>e;if(m.setTrialStrain(e)||m.commitState())throw std::runtime_error("continue API failure");}observe();
 in>>rollback;if(m.setTrialStrain(rollback)||m.revertToLastCommit())throw std::runtime_error("rollback API failure");observe();
 if(m.revertToStart())throw std::runtime_error("reset API failure");observe();
}
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("input and output required");std::ifstream in(argv[1]);std::ofstream out(argv[2]);out<<std::setprecision(17);int count;in>>count;
 for(int i=0;i<count;++i){int kind,np,nn;double px,py,beta;in>>kind>>np>>nn>>px>>py>>beta;Vector pos(2*np),neg(2*nn);for(int j=0;j<2*np;++j)in>>pos(j);for(int j=0;j<2*nn;++j)in>>neg(j);
 if(kind==0){if(np!=nn||(np!=2&&np!=3))throw std::runtime_error("Hysteretic envelope size");
 if(np==2){HystereticMaterial m(i+1,pos(0),pos(1),pos(2),pos(3),neg(0),neg(1),neg(2),neg(3),px,py,0,0,beta);execute(m,in,out);}
 else{HystereticMaterial m(i+1,pos(0),pos(1),pos(2),pos(3),pos(4),pos(5),neg(0),neg(1),neg(2),neg(3),neg(4),neg(5),px,py,0,0,beta);execute(m,in,out);}}
 else if(kind==1){Vector pinch(2),empty,internal(39);pinch(0)=px;pinch(1)=py;HystereticSMMaterial m(i+1,pos,neg,pinch,empty,beta,empty,empty,empty,empty,internal);execute(m,in,out);}
 else throw std::runtime_error("unknown material");
 }if(!in||!out)throw std::runtime_error("material IO failure");return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
