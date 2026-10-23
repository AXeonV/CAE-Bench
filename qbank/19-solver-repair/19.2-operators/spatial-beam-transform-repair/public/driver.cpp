#include "includes/model_part.h"
#include "includes/kratos_application.h"
#include "geometries/line_3d_2.h"
#include "structural_mechanics_application_variables.h"
#include "custom_elements/beam_elements/timoshenko_beam_element_3D2N.h"
#include "custom_constitutive/timoshenko_beam_elastic_constitutive_law_3d.h"
#include <fstream>
#include <iomanip>
using namespace Kratos;
int main(int argc,char** argv) { try {
 if(argc!=3) return 2;
 std::ifstream in(argv[1]); std::ofstream out(argv[2]); out<<std::setprecision(17);
 KratosApplication core("KratosMultiphysics"); core.Register();
 KRATOS_REGISTER_VARIABLE(CROSS_AREA); KRATOS_REGISTER_VARIABLE(I22); KRATOS_REGISTER_VARIABLE(I33); KRATOS_REGISTER_VARIABLE(IT);
 KRATOS_REGISTER_VARIABLE(AREA_EFFECTIVE_Y); KRATOS_REGISTER_VARIABLE(AREA_EFFECTIVE_Z);
 KRATOS_REGISTER_3D_VARIABLE_WITH_COMPONENTS(LOCAL_AXIS_2);
 size_t count; in>>count;
 for(size_t k=0;k<count;++k) {
 double x[6],axis[3],mat[9],acc[3]; for(auto& v:x)in>>v; for(auto&v:axis)in>>v;for(auto&v:mat)in>>v;for(auto&v:acc)in>>v;
 if(!in)throw std::runtime_error("bad driver input");
 VariablesList::Pointer vars=Kratos::make_intrusive<VariablesList>(); vars->Add(DISPLACEMENT);vars->Add(ROTATION);vars->Add(VOLUME_ACCELERATION);
 auto n0=Kratos::make_intrusive<Node>(1,x[0],x[1],x[2]);auto n1=Kratos::make_intrusive<Node>(2,x[3],x[4],x[5]);
 for(auto n:{n0,n1}){n->SetSolutionStepVariablesList(vars);n->SetBufferSize(1);n->FastGetSolutionStepValue(DISPLACEMENT)=ZeroVector(3);n->FastGetSolutionStepValue(ROTATION)=ZeroVector(3);for(int i=0;i<3;++i)n->FastGetSolutionStepValue(VOLUME_ACCELERATION)[i]=acc[i];}
 auto geom=Kratos::make_shared<Line3D2<Node>>(n0,n1);array_1d<double,3>a;for(int i=0;i<3;++i)a[i]=axis[i];geom->SetValue(LOCAL_AXIS_2,a);
 auto props=Kratos::make_shared<Properties>(1);
 props->SetValue(YOUNG_MODULUS,mat[0]);props->SetValue(POISSON_RATIO,mat[1]);props->SetValue(CROSS_AREA,mat[2]);props->SetValue(I22,mat[3]);props->SetValue(I33,mat[4]);props->SetValue(IT,mat[5]);props->SetValue(AREA_EFFECTIVE_Y,mat[6]);props->SetValue(AREA_EFFECTIVE_Z,mat[7]);props->SetValue(DENSITY,mat[8]);
 props->SetValue(CONSTITUTIVE_LAW,Kratos::make_shared<TimoshenkoBeamElasticConstitutiveLaw3D>());
 LinearTimoshenkoBeamElement3D2N elem(1,geom,props); ProcessInfo info;info[IS_RESTARTED]=false;elem.Initialize(info);
 Matrix K,Ksingle;Vector f,fsingle;elem.CalculateLocalSystem(K,f,info);elem.CalculateLeftHandSide(Ksingle,info);elem.CalculateRightHandSide(fsingle,info);
 for(size_t i=0;i<12;++i)for(size_t j=0;j<12;++j)out<<K(i,j)<<' ';out<<'\n';for(auto v:f)out<<v<<' ';out<<'\n';
 for(size_t i=0;i<12;++i)for(size_t j=0;j<12;++j)out<<Ksingle(i,j)<<' ';out<<'\n';for(auto v:fsingle)out<<v<<' ';out<<'\n';
 }
 return 0;
 }catch(std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}

