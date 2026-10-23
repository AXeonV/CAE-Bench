// Trusted metadata adapter: expose actual libMesh node/variable DOF identities.
#include "GeneralVectorPostprocessor.h"
#include "FEProblemBase.h"
#include "NonlinearSystemBase.h"
#include "MooseMesh.h"
#include "libmesh/node.h"
#include "libmesh/system.h"
class RepairDofMap : public GeneralVectorPostprocessor
{
public:
  static InputParameters validParams()
  {
    auto p = GeneralVectorPostprocessor::validParams();
    p.addRequiredParam<std::vector<NonlinearVariableName>>("variables", "Nonlinear variable names");
    return p;
  }
  RepairDofMap(const InputParameters & p)
    : GeneralVectorPostprocessor(p), _names(getParam<std::vector<NonlinearVariableName>>("variables")),
      _ids(declareVector("node_id")), _x(declareVector("x"))
  {
    for (const auto & name : _names)
      _dofs.push_back(&declareVector("dof_" + name));
  }
  void initialize() override
  {
    _ids.clear(); _x.clear();
    for (auto * v : _dofs) v->clear();
  }
  void execute() override
  {
    const auto & sys = _fe_problem.getNonlinearSystemBase(0).system();
    for (const auto * node : _fe_problem.mesh().getMesh().local_node_ptr_range())
    {
      _ids.push_back(node->id()); _x.push_back((*node)(0));
      for (std::size_t j = 0; j < _names.size(); ++j)
        _dofs[j]->push_back(node->dof_number(sys.number(), sys.variable_number(_names[j]), 0));
    }
  }
  void finalize() override {}
protected:
  std::vector<NonlinearVariableName> _names;
  VectorPostprocessorValue & _ids, & _x;
  std::vector<VectorPostprocessorValue *> _dofs;
};
registerMooseObject("PhaseFieldApp", RepairDofMap);
