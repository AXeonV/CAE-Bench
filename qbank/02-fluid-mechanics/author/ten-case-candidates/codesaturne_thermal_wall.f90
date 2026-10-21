! Boundary data only, through the stock v6.0 Fortran user interface.
! cfxtcl converts temperature code 5 to the native total-energy condition.
! No PDE, constitutive law, interior state or iteration criterion is changed.
subroutine cs_f_user_boundary_conditions &
 (nvar, nscal, icodcl, itrifb, itypfb, izfppp, dt, rcodcl)
use paramx
use numvar
use ppppar
use ppthch
use ppincl
use cfpoin
use mesh
implicit none
integer nvar, nscal
integer icodcl(nfabor,nvar), itrifb(nfabor), itypfb(nfabor)
integer izfppp(nfabor), ifac, itk
double precision dt(ncelet), rcodcl(nfabor,nvar,3)
itk = isca(itempk)
do ifac = 1, nfabor
  select case (izfppp(ifac))
  case (1)
    icodcl(ifac,itk) = 5
    rcodcl(ifac,itk,1) = 305.d0
  case (2)
    icodcl(ifac,itk) = 5
    rcodcl(ifac,itk,1) = 295.d0
  case (3)
    icodcl(ifac,itk) = 3
    rcodcl(ifac,itk,3) = 0.d0
  end select
enddo
end subroutine cs_f_user_boundary_conditions

! iniusi calls this after csphys/cssca3 and before computing EOS cv0.
! cssca3 uses lambda/Cp for the thermal scalar; cfener requires lambda/Cv.
! This fixed producer case has frozen lambda=.02 and Cv=717.5 SI.
subroutine usipsu(nmodpp)
use paramx
use numvar
use optcal, only: visls0
use cstphy
use ppppar
use ppthch
use ppincl
use cfpoin
implicit none
integer nmodpp
visls0(ienerg) = 0.02d0 / 717.5d0
end subroutine usipsu
