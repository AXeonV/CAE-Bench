// Trusted observation adapter: read the actual MOOSE derivative property API.
// No constitutive formula, finite difference, or replacement value is computed here.
#include "ElementAverageMaterialProperty.h"
#include "DerivativeMaterialInterface.h"

class RepairDerivativeAverage : public DerivativeMaterialInterface<ElementAverageMaterialProperty>
{
public:
  static InputParameters validParams()
  {
    auto p = ElementAverageMaterialProperty::validParams();
    p.addParam<std::vector<SymbolName>>("derivatives", {}, "Derivative variable names in order");
    return p;
  }
  RepairDerivativeAverage(const InputParameters & p)
    : DerivativeMaterialInterface<ElementAverageMaterialProperty>(p),
      _observed(getMaterialPropertyDerivativeByName<Real>(
          getParam<MaterialPropertyName>("mat_prop"),
          getParam<std::vector<SymbolName>>("derivatives")))
  {}
protected:
  Real computeQpIntegral() override { return _observed[_qp]; }
  const MaterialProperty<Real> & _observed;
};

registerMooseObject("PhaseFieldApp", RepairDerivativeAverage);
