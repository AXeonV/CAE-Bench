! Read-only input adapter. No evolution, constitutive law or PDE is implemented.
MODULE CAEInitialKEData
  USE DefUtils
  IMPLICIT NONE
  REAL(KIND=dp), ALLOCATABLE, SAVE :: KValues(:), EValues(:)
CONTAINS
  SUBROUTINE LoadInitialKE()
    INTEGER :: n, i, tag, io, unit
    IF (ALLOCATED(KValues)) RETURN
    OPEN(NEWUNIT=unit, FILE='initial-ke.dat', STATUS='old', ACTION='read', IOSTAT=io)
    IF (io /= 0) CALL Fatal('InitialKE', 'Cannot open initial-ke.dat')
    READ(unit,*,IOSTAT=io) n
    IF (io /= 0 .OR. n < 1) CALL Fatal('InitialKE', 'Invalid node count')
    ALLOCATE(KValues(n), EValues(n))
    DO i=1,n
      READ(unit,*,IOSTAT=io) tag, KValues(i), EValues(i)
      IF (io /= 0 .OR. tag /= i) CALL Fatal('InitialKE', 'Invalid node record')
    END DO
    CLOSE(unit)
  END SUBROUTINE
END MODULE

FUNCTION InitialK(Model, Node, Input) RESULT(Value)
  USE CAEInitialKEData
  IMPLICIT NONE
  TYPE(Model_t) :: Model
  INTEGER :: Node, GlobalNode
  REAL(KIND=dp) :: Input, Value
  CALL LoadInitialKE()
  GlobalNode = Node
  IF (ASSOCIATED(Model % Mesh % ParallelInfo % GlobalDOFs)) &
    GlobalNode = Model % Mesh % ParallelInfo % GlobalDOFs(Node)
  IF (GlobalNode < 1 .OR. GlobalNode > SIZE(KValues)) CALL Fatal('InitialKE', 'Invalid node')
  Value = KValues(GlobalNode)
END FUNCTION

FUNCTION InitialEpsilon(Model, Node, Input) RESULT(Value)
  USE CAEInitialKEData
  IMPLICIT NONE
  TYPE(Model_t) :: Model
  INTEGER :: Node, GlobalNode
  REAL(KIND=dp) :: Input, Value
  CALL LoadInitialKE()
  GlobalNode = Node
  IF (ASSOCIATED(Model % Mesh % ParallelInfo % GlobalDOFs)) &
    GlobalNode = Model % Mesh % ParallelInfo % GlobalDOFs(Node)
  IF (GlobalNode < 1 .OR. GlobalNode > SIZE(EValues)) CALL Fatal('InitialKE', 'Invalid node')
  Value = EValues(GlobalNode)
END FUNCTION
