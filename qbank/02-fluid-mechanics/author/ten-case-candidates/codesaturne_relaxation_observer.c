/* Read-only native-field monitor and finite stopping. No PDE/state updates. */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include "cs_defs.h"
#include "cs_domain.h"
#include "cs_field.h"
#include "cs_mesh.h"
#include "cs_mesh_quantities.h"
#include "cs_time_step.h"
#include "cs_physical_constants.h"
static double *previous = NULL;
static int consecutive = 0, converged = 0;
static double last_change = 1., last_mass_error = 1.;
void cs_user_extra_operations(cs_domain_t *domain)
{
  (void)domain;
  const cs_lnum_t n=cs_glob_mesh->n_cells;
  const double *u=cs_field_by_name("velocity")->val;
  const double *p=cs_field_by_name("pressure")->val;
  const double *T=cs_field_by_name("temperature")->val;
  const double *rho=cs_field_by_name("density")->val;
  double maxchange=0., mass=0., vol=0.;
  if (!previous) previous=calloc((size_t)n*6,sizeof(double));
  for (cs_lnum_t i=0;i<n;i++) {
    const double a[6]={u[3*i],u[3*i+1],u[3*i+2],p[i],T[i],rho[i]};
    for (int j=0;j<6;j++) {
      double v=fabs(a[j]-previous[6*i+j])/fmax(1.,fabs(a[j]));
      maxchange=fmax(maxchange,v); previous[6*i+j]=a[j];
    }
    mass+=rho[i]*cs_glob_mesh_quantities->cell_vol[i];
    vol+=cs_glob_mesh_quantities->cell_vol[i];
  }
  last_change=maxchange;
  last_mass_error=fabs(mass/(vol*cs_glob_fluid_properties->ro0)-1.);
  FILE *f=fopen("caeoj-convergence.csv","a");
  if (f) {fprintf(f,"%d,%.17g,%.17g,%.17g\n",cs_glob_time_step->nt_cur,cs_glob_time_step->t_cur,last_change,last_mass_error);fclose(f);}
  if (cs_glob_time_step->nt_cur>=50 && cs_glob_time_step->t_cur>=1000.
      && last_change<1.e-8 && last_mass_error<1.e-6) consecutive++;
  else consecutive=0;
  if (consecutive>=20) {
    converged=1;
    cs_time_step_define_nt_max(cs_glob_time_step->nt_cur);
  }
}
void cs_user_extra_operations_finalize(cs_domain_t *domain)
{
  (void)domain;
  FILE *f=fopen("caeoj-native-final.csv","w");
  const double *u=cs_field_by_name("velocity")->val;
  const double *p=cs_field_by_name("pressure")->val;
  const double *T=cs_field_by_name("temperature")->val;
  const double *rho=cs_field_by_name("density")->val;
  if (f) {
    fprintf(f,"id,x,y,z,volume,ux,uy,uz,p,T,rho\n");
    for (cs_lnum_t i=0;i<cs_glob_mesh->n_cells;i++) {
      const double *x=&cs_glob_mesh_quantities->cell_cen[3*i];
      fprintf(f,"%ld,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g\n",(long)i,x[0],x[1],x[2],cs_glob_mesh_quantities->cell_vol[i],u[3*i],u[3*i+1],u[3*i+2],p[i],T[i],rho[i]);
    }
    fclose(f);
  }
  f=fopen("caeoj-native-stop.json","w");
  if (f) {fprintf(f,"{\"converged\":%s,\"steps\":%d,\"physical_time\":%.17g,\"relative_change\":%.17g,\"relative_mass_error\":%.17g,\"numerical_validation\":false}\n",converged?"true":"false",cs_glob_time_step->nt_cur,cs_glob_time_step->t_cur,last_change,last_mass_error);fclose(f);}
  free(previous);
}
