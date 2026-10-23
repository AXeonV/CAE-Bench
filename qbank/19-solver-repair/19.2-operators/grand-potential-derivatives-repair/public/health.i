[Mesh]
 [segment0]
  type = GeneratedMeshGenerator
  dim = 1
  nx = 1
  xmin = 0
  xmax = 1
  subdomain_ids = 1
 []
 [segment1]
  type = GeneratedMeshGenerator
  dim = 1
  nx = 1
  xmin = 3
  xmax = 4
  subdomain_ids = 2
 []
 [segment2]
  type = GeneratedMeshGenerator
  dim = 1
  nx = 1
  xmin = 6
  xmax = 7
  subdomain_ids = 3
 []
 [segment3]
  type = GeneratedMeshGenerator
  dim = 1
  nx = 1
  xmin = 9
  xmax = 10
  subdomain_ids = 4
 []
 [collection]
  type = MeshCollectionGenerator
  inputs = 'segment0 segment1 segment2 segment3'
 []
[]
[Functions]
 [initial_phi]
  type = ParsedFunction
  expression = 'if(x<2,-0.10000000000000001,if(x<5,0,if(x<8,1,1.1000000000000001)))'
 []
 [initial_potential]
  type = ParsedFunction
  expression = 'if(x<2,0,if(x<5,0,if(x<8,0,0)))'
 []
 [initial_concentration]
  type = ParsedFunction
  expression = 'if(x<2,0.20000000000000001,if(x<5,0.80000000000000004,if(x<8,0,1)))'
 []
 [initial_temperature]
  type = ParsedFunction
  expression = 'if(x<2,250,if(x<5,833.33333333333337,if(x<8,1416.6666666666667,2000)))'
 []
 [initial_eta0]
  type = ParsedFunction
  expression = 'if(x<2,0,if(x<5,0.20000000000000001,if(x<8,0.80000000000000004,1)))'
 []
 [initial_eta1]
  type = ParsedFunction
  expression = 'if(x<2,0,if(x<5,0,if(x<8,0,0)))'
 []
 [initial_eta2]
  type = ParsedFunction
  expression = 'if(x<2,0,if(x<5,0,if(x<8,0,0)))'
 []
 [initial_eta3]
  type = ParsedFunction
  expression = 'if(x<2,0,if(x<5,0,if(x<8,0,0)))'
 []
[]
[Variables]
 [pore_state]
 []
 [grain_a]
 []
 [grain_b]
 []
 [grain_c]
 []
 [grain_d]
 []
 [mu_state]
 []
 [fraction_state]
 []
[]
[AuxVariables]
 [thermal_state]
 []
[]
[ICs]
 [state_phi]
  type = FunctionIC
  variable = pore_state
  function = initial_phi
 []
 [state_potential]
  type = FunctionIC
  variable = mu_state
  function = initial_potential
 []
 [state_concentration]
  type = FunctionIC
  variable = fraction_state
  function = initial_concentration
 []
 [state_temperature]
  type = FunctionIC
  variable = thermal_state
  function = initial_temperature
 []
 [state_eta0]
  type = FunctionIC
  variable = grain_a
  function = initial_eta0
 []
 [state_eta1]
  type = FunctionIC
  variable = grain_b
  function = initial_eta1
 []
 [state_eta2]
  type = FunctionIC
  variable = grain_c
  function = initial_eta2
 []
 [state_eta3]
  type = FunctionIC
  variable = grain_d
  function = initial_eta3
 []
[]
[Materials]
 [constants]
  type = GenericConstantMaterial
  prop_names = 'ks kv'
  prop_values = '320000000 480000000'
 []
 [equilibrium]
  type = DerivativeParsedMaterial
  property_name = ceq
  coupled_variables = 'grain_a'
  expression = '0.40000000000000002+(0)*grain_a+(0)*grain_a*grain_a'
  derivative_order = 2
  enable_jit = false
 []
 [grand_potential]
  type = GrandPotentialSinteringMaterial
  etas = 'grain_a'
  chemical_potential = mu_state
  void_op = pore_state
  Temperature = thermal_state
  solid_energy_coefficient = ks
  void_energy_coefficient = kv
  equilibrium_vacancy_concentration = ceq
  atomic_volume = 3.9999999999999998e-29
  surface_energy = 0.16
  grainboundary_energy = 0.112
  int_width = 1.0000000000000001e-09
  surface_switch_value = 0.29999999999999999
  solid_energy_model = PARABOLIC
  mass_conservation = true
 []
[]
[Kernels]
 [anchor_phi]
  type = Reaction
  variable = pore_state
 []
 [anchor_force_phi]
  type = BodyForce
  variable = pore_state
  function = initial_phi
 []
 [anchor_eta0]
  type = Reaction
  variable = grain_a
 []
 [anchor_force_eta0]
  type = BodyForce
  variable = grain_a
  function = initial_eta0
 []
 [anchor_eta1]
  type = Reaction
  variable = grain_b
 []
 [anchor_force_eta1]
  type = BodyForce
  variable = grain_b
  function = initial_eta1
 []
 [anchor_eta2]
  type = Reaction
  variable = grain_c
 []
 [anchor_force_eta2]
  type = BodyForce
  variable = grain_c
  function = initial_eta2
 []
 [anchor_eta3]
  type = Reaction
  variable = grain_d
 []
 [anchor_force_eta3]
  type = BodyForce
  variable = grain_d
  function = initial_eta3
 []
 [anchor_potential]
  type = Reaction
  variable = mu_state
 []
 [anchor_force_potential]
  type = BodyForce
  variable = mu_state
  function = initial_potential
 []
 [concentration]
  type = Reaction
  variable = fraction_state
 []
 [void_response]
  type = MatReaction
  variable = fraction_state
  v = mu_state
  reaction_rate = hv_over_kVa
  args = 'pore_state grain_a'
 []
 [solid_response]
  type = MatReaction
  variable = fraction_state
  v = mu_state
  reaction_rate = hs_over_kVa
  args = 'pore_state grain_a'
 []
 [void_minimum]
  type = MatBodyForce
  variable = fraction_state
  material_property = hv_c_min
  coupled_variables = 'pore_state grain_a'
 []
 [solid_minimum]
  type = MatBodyForce
  variable = fraction_state
  material_property = hs_c_min
  coupled_variables = 'pore_state grain_a'
 []
[]
[Postprocessors]
 [p0_void_minimum_0]
  type = ElementAverageMaterialProperty
  mat_prop = hv_c_min
  block = 1
  execute_on = INITIAL
 []
 [p0_void_minimum_gradient_0]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'pore_state'
 []
 [p0_void_minimum_gradient_1]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_a'
 []
 [p0_void_minimum_gradient_2]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_b'
 []
 [p0_void_minimum_gradient_3]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_c'
 []
 [p0_void_minimum_gradient_4]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_d'
 []
 [p0_void_minimum_hessian_0]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'pore_state pore_state'
 []
 [p0_void_minimum_hessian_1]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'pore_state grain_a'
 []
 [p0_void_minimum_hessian_2]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'pore_state grain_b'
 []
 [p0_void_minimum_hessian_3]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'pore_state grain_c'
 []
 [p0_void_minimum_hessian_4]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'pore_state grain_d'
 []
 [p0_void_minimum_hessian_5]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_a pore_state'
 []
 [p0_void_minimum_hessian_6]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_a grain_a'
 []
 [p0_void_minimum_hessian_7]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_a grain_b'
 []
 [p0_void_minimum_hessian_8]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_a grain_c'
 []
 [p0_void_minimum_hessian_9]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_a grain_d'
 []
 [p0_void_minimum_hessian_10]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_b pore_state'
 []
 [p0_void_minimum_hessian_11]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_b grain_a'
 []
 [p0_void_minimum_hessian_12]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_b grain_b'
 []
 [p0_void_minimum_hessian_13]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_b grain_c'
 []
 [p0_void_minimum_hessian_14]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_b grain_d'
 []
 [p0_void_minimum_hessian_15]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_c pore_state'
 []
 [p0_void_minimum_hessian_16]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_c grain_a'
 []
 [p0_void_minimum_hessian_17]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_c grain_b'
 []
 [p0_void_minimum_hessian_18]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_c grain_c'
 []
 [p0_void_minimum_hessian_19]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_c grain_d'
 []
 [p0_void_minimum_hessian_20]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_d pore_state'
 []
 [p0_void_minimum_hessian_21]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_d grain_a'
 []
 [p0_void_minimum_hessian_22]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_d grain_b'
 []
 [p0_void_minimum_hessian_23]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_d grain_c'
 []
 [p0_void_minimum_hessian_24]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_d grain_d'
 []
 [p0_solid_minimum_0]
  type = ElementAverageMaterialProperty
  mat_prop = hs_c_min
  block = 1
  execute_on = INITIAL
 []
 [p0_solid_minimum_gradient_0]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'pore_state'
 []
 [p0_solid_minimum_gradient_1]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_a'
 []
 [p0_solid_minimum_gradient_2]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_b'
 []
 [p0_solid_minimum_gradient_3]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_c'
 []
 [p0_solid_minimum_gradient_4]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_d'
 []
 [p0_solid_minimum_hessian_0]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'pore_state pore_state'
 []
 [p0_solid_minimum_hessian_1]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'pore_state grain_a'
 []
 [p0_solid_minimum_hessian_2]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'pore_state grain_b'
 []
 [p0_solid_minimum_hessian_3]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'pore_state grain_c'
 []
 [p0_solid_minimum_hessian_4]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'pore_state grain_d'
 []
 [p0_solid_minimum_hessian_5]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_a pore_state'
 []
 [p0_solid_minimum_hessian_6]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_a grain_a'
 []
 [p0_solid_minimum_hessian_7]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_a grain_b'
 []
 [p0_solid_minimum_hessian_8]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_a grain_c'
 []
 [p0_solid_minimum_hessian_9]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_a grain_d'
 []
 [p0_solid_minimum_hessian_10]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_b pore_state'
 []
 [p0_solid_minimum_hessian_11]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_b grain_a'
 []
 [p0_solid_minimum_hessian_12]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_b grain_b'
 []
 [p0_solid_minimum_hessian_13]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_b grain_c'
 []
 [p0_solid_minimum_hessian_14]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_b grain_d'
 []
 [p0_solid_minimum_hessian_15]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_c pore_state'
 []
 [p0_solid_minimum_hessian_16]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_c grain_a'
 []
 [p0_solid_minimum_hessian_17]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_c grain_b'
 []
 [p0_solid_minimum_hessian_18]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_c grain_c'
 []
 [p0_solid_minimum_hessian_19]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_c grain_d'
 []
 [p0_solid_minimum_hessian_20]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_d pore_state'
 []
 [p0_solid_minimum_hessian_21]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_d grain_a'
 []
 [p0_solid_minimum_hessian_22]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_d grain_b'
 []
 [p0_solid_minimum_hessian_23]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_d grain_c'
 []
 [p0_solid_minimum_hessian_24]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_d grain_d'
 []
 [p0_void_response_0]
  type = ElementAverageMaterialProperty
  mat_prop = hv_over_kVa
  block = 1
  execute_on = INITIAL
 []
 [p0_void_response_gradient_0]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'pore_state'
 []
 [p0_void_response_gradient_1]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_a'
 []
 [p0_void_response_gradient_2]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_b'
 []
 [p0_void_response_gradient_3]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_c'
 []
 [p0_void_response_gradient_4]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_d'
 []
 [p0_void_response_hessian_0]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'pore_state pore_state'
 []
 [p0_void_response_hessian_1]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'pore_state grain_a'
 []
 [p0_void_response_hessian_2]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'pore_state grain_b'
 []
 [p0_void_response_hessian_3]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'pore_state grain_c'
 []
 [p0_void_response_hessian_4]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'pore_state grain_d'
 []
 [p0_void_response_hessian_5]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_a pore_state'
 []
 [p0_void_response_hessian_6]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_a grain_a'
 []
 [p0_void_response_hessian_7]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_a grain_b'
 []
 [p0_void_response_hessian_8]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_a grain_c'
 []
 [p0_void_response_hessian_9]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_a grain_d'
 []
 [p0_void_response_hessian_10]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_b pore_state'
 []
 [p0_void_response_hessian_11]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_b grain_a'
 []
 [p0_void_response_hessian_12]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_b grain_b'
 []
 [p0_void_response_hessian_13]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_b grain_c'
 []
 [p0_void_response_hessian_14]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_b grain_d'
 []
 [p0_void_response_hessian_15]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_c pore_state'
 []
 [p0_void_response_hessian_16]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_c grain_a'
 []
 [p0_void_response_hessian_17]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_c grain_b'
 []
 [p0_void_response_hessian_18]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_c grain_c'
 []
 [p0_void_response_hessian_19]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_c grain_d'
 []
 [p0_void_response_hessian_20]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_d pore_state'
 []
 [p0_void_response_hessian_21]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_d grain_a'
 []
 [p0_void_response_hessian_22]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_d grain_b'
 []
 [p0_void_response_hessian_23]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_d grain_c'
 []
 [p0_void_response_hessian_24]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_d grain_d'
 []
 [p0_solid_response_0]
  type = ElementAverageMaterialProperty
  mat_prop = hs_over_kVa
  block = 1
  execute_on = INITIAL
 []
 [p0_solid_response_gradient_0]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'pore_state'
 []
 [p0_solid_response_gradient_1]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_a'
 []
 [p0_solid_response_gradient_2]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_b'
 []
 [p0_solid_response_gradient_3]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_c'
 []
 [p0_solid_response_gradient_4]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_d'
 []
 [p0_solid_response_hessian_0]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'pore_state pore_state'
 []
 [p0_solid_response_hessian_1]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'pore_state grain_a'
 []
 [p0_solid_response_hessian_2]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'pore_state grain_b'
 []
 [p0_solid_response_hessian_3]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'pore_state grain_c'
 []
 [p0_solid_response_hessian_4]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'pore_state grain_d'
 []
 [p0_solid_response_hessian_5]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_a pore_state'
 []
 [p0_solid_response_hessian_6]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_a grain_a'
 []
 [p0_solid_response_hessian_7]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_a grain_b'
 []
 [p0_solid_response_hessian_8]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_a grain_c'
 []
 [p0_solid_response_hessian_9]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_a grain_d'
 []
 [p0_solid_response_hessian_10]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_b pore_state'
 []
 [p0_solid_response_hessian_11]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_b grain_a'
 []
 [p0_solid_response_hessian_12]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_b grain_b'
 []
 [p0_solid_response_hessian_13]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_b grain_c'
 []
 [p0_solid_response_hessian_14]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_b grain_d'
 []
 [p0_solid_response_hessian_15]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_c pore_state'
 []
 [p0_solid_response_hessian_16]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_c grain_a'
 []
 [p0_solid_response_hessian_17]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_c grain_b'
 []
 [p0_solid_response_hessian_18]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_c grain_c'
 []
 [p0_solid_response_hessian_19]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_c grain_d'
 []
 [p0_solid_response_hessian_20]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_d pore_state'
 []
 [p0_solid_response_hessian_21]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_d grain_a'
 []
 [p0_solid_response_hessian_22]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_d grain_b'
 []
 [p0_solid_response_hessian_23]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_d grain_c'
 []
 [p0_solid_response_hessian_24]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 1
  execute_on = INITIAL
  derivatives = 'grain_d grain_d'
 []
 [p0_void_number_density_0]
  type = ElementAverageMaterialProperty
  mat_prop = rhov
  block = 1
  execute_on = INITIAL
 []
 [p0_solid_number_density_0]
  type = ElementAverageMaterialProperty
  mat_prop = rhos
  block = 1
  execute_on = INITIAL
 []
 [p0_void_grand_potential_0]
  type = ElementAverageMaterialProperty
  mat_prop = omegav
  block = 1
  execute_on = INITIAL
 []
 [p0_solid_grand_potential_0]
  type = ElementAverageMaterialProperty
  mat_prop = omegas
  block = 1
  execute_on = INITIAL
 []
 [p1_void_minimum_0]
  type = ElementAverageMaterialProperty
  mat_prop = hv_c_min
  block = 2
  execute_on = INITIAL
 []
 [p1_void_minimum_gradient_0]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'pore_state'
 []
 [p1_void_minimum_gradient_1]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_a'
 []
 [p1_void_minimum_gradient_2]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_b'
 []
 [p1_void_minimum_gradient_3]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_c'
 []
 [p1_void_minimum_gradient_4]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_d'
 []
 [p1_void_minimum_hessian_0]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'pore_state pore_state'
 []
 [p1_void_minimum_hessian_1]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'pore_state grain_a'
 []
 [p1_void_minimum_hessian_2]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'pore_state grain_b'
 []
 [p1_void_minimum_hessian_3]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'pore_state grain_c'
 []
 [p1_void_minimum_hessian_4]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'pore_state grain_d'
 []
 [p1_void_minimum_hessian_5]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_a pore_state'
 []
 [p1_void_minimum_hessian_6]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_a grain_a'
 []
 [p1_void_minimum_hessian_7]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_a grain_b'
 []
 [p1_void_minimum_hessian_8]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_a grain_c'
 []
 [p1_void_minimum_hessian_9]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_a grain_d'
 []
 [p1_void_minimum_hessian_10]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_b pore_state'
 []
 [p1_void_minimum_hessian_11]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_b grain_a'
 []
 [p1_void_minimum_hessian_12]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_b grain_b'
 []
 [p1_void_minimum_hessian_13]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_b grain_c'
 []
 [p1_void_minimum_hessian_14]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_b grain_d'
 []
 [p1_void_minimum_hessian_15]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_c pore_state'
 []
 [p1_void_minimum_hessian_16]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_c grain_a'
 []
 [p1_void_minimum_hessian_17]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_c grain_b'
 []
 [p1_void_minimum_hessian_18]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_c grain_c'
 []
 [p1_void_minimum_hessian_19]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_c grain_d'
 []
 [p1_void_minimum_hessian_20]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_d pore_state'
 []
 [p1_void_minimum_hessian_21]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_d grain_a'
 []
 [p1_void_minimum_hessian_22]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_d grain_b'
 []
 [p1_void_minimum_hessian_23]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_d grain_c'
 []
 [p1_void_minimum_hessian_24]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_d grain_d'
 []
 [p1_solid_minimum_0]
  type = ElementAverageMaterialProperty
  mat_prop = hs_c_min
  block = 2
  execute_on = INITIAL
 []
 [p1_solid_minimum_gradient_0]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'pore_state'
 []
 [p1_solid_minimum_gradient_1]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_a'
 []
 [p1_solid_minimum_gradient_2]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_b'
 []
 [p1_solid_minimum_gradient_3]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_c'
 []
 [p1_solid_minimum_gradient_4]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_d'
 []
 [p1_solid_minimum_hessian_0]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'pore_state pore_state'
 []
 [p1_solid_minimum_hessian_1]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'pore_state grain_a'
 []
 [p1_solid_minimum_hessian_2]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'pore_state grain_b'
 []
 [p1_solid_minimum_hessian_3]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'pore_state grain_c'
 []
 [p1_solid_minimum_hessian_4]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'pore_state grain_d'
 []
 [p1_solid_minimum_hessian_5]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_a pore_state'
 []
 [p1_solid_minimum_hessian_6]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_a grain_a'
 []
 [p1_solid_minimum_hessian_7]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_a grain_b'
 []
 [p1_solid_minimum_hessian_8]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_a grain_c'
 []
 [p1_solid_minimum_hessian_9]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_a grain_d'
 []
 [p1_solid_minimum_hessian_10]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_b pore_state'
 []
 [p1_solid_minimum_hessian_11]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_b grain_a'
 []
 [p1_solid_minimum_hessian_12]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_b grain_b'
 []
 [p1_solid_minimum_hessian_13]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_b grain_c'
 []
 [p1_solid_minimum_hessian_14]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_b grain_d'
 []
 [p1_solid_minimum_hessian_15]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_c pore_state'
 []
 [p1_solid_minimum_hessian_16]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_c grain_a'
 []
 [p1_solid_minimum_hessian_17]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_c grain_b'
 []
 [p1_solid_minimum_hessian_18]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_c grain_c'
 []
 [p1_solid_minimum_hessian_19]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_c grain_d'
 []
 [p1_solid_minimum_hessian_20]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_d pore_state'
 []
 [p1_solid_minimum_hessian_21]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_d grain_a'
 []
 [p1_solid_minimum_hessian_22]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_d grain_b'
 []
 [p1_solid_minimum_hessian_23]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_d grain_c'
 []
 [p1_solid_minimum_hessian_24]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_d grain_d'
 []
 [p1_void_response_0]
  type = ElementAverageMaterialProperty
  mat_prop = hv_over_kVa
  block = 2
  execute_on = INITIAL
 []
 [p1_void_response_gradient_0]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'pore_state'
 []
 [p1_void_response_gradient_1]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_a'
 []
 [p1_void_response_gradient_2]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_b'
 []
 [p1_void_response_gradient_3]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_c'
 []
 [p1_void_response_gradient_4]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_d'
 []
 [p1_void_response_hessian_0]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'pore_state pore_state'
 []
 [p1_void_response_hessian_1]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'pore_state grain_a'
 []
 [p1_void_response_hessian_2]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'pore_state grain_b'
 []
 [p1_void_response_hessian_3]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'pore_state grain_c'
 []
 [p1_void_response_hessian_4]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'pore_state grain_d'
 []
 [p1_void_response_hessian_5]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_a pore_state'
 []
 [p1_void_response_hessian_6]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_a grain_a'
 []
 [p1_void_response_hessian_7]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_a grain_b'
 []
 [p1_void_response_hessian_8]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_a grain_c'
 []
 [p1_void_response_hessian_9]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_a grain_d'
 []
 [p1_void_response_hessian_10]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_b pore_state'
 []
 [p1_void_response_hessian_11]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_b grain_a'
 []
 [p1_void_response_hessian_12]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_b grain_b'
 []
 [p1_void_response_hessian_13]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_b grain_c'
 []
 [p1_void_response_hessian_14]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_b grain_d'
 []
 [p1_void_response_hessian_15]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_c pore_state'
 []
 [p1_void_response_hessian_16]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_c grain_a'
 []
 [p1_void_response_hessian_17]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_c grain_b'
 []
 [p1_void_response_hessian_18]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_c grain_c'
 []
 [p1_void_response_hessian_19]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_c grain_d'
 []
 [p1_void_response_hessian_20]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_d pore_state'
 []
 [p1_void_response_hessian_21]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_d grain_a'
 []
 [p1_void_response_hessian_22]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_d grain_b'
 []
 [p1_void_response_hessian_23]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_d grain_c'
 []
 [p1_void_response_hessian_24]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_d grain_d'
 []
 [p1_solid_response_0]
  type = ElementAverageMaterialProperty
  mat_prop = hs_over_kVa
  block = 2
  execute_on = INITIAL
 []
 [p1_solid_response_gradient_0]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'pore_state'
 []
 [p1_solid_response_gradient_1]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_a'
 []
 [p1_solid_response_gradient_2]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_b'
 []
 [p1_solid_response_gradient_3]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_c'
 []
 [p1_solid_response_gradient_4]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_d'
 []
 [p1_solid_response_hessian_0]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'pore_state pore_state'
 []
 [p1_solid_response_hessian_1]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'pore_state grain_a'
 []
 [p1_solid_response_hessian_2]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'pore_state grain_b'
 []
 [p1_solid_response_hessian_3]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'pore_state grain_c'
 []
 [p1_solid_response_hessian_4]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'pore_state grain_d'
 []
 [p1_solid_response_hessian_5]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_a pore_state'
 []
 [p1_solid_response_hessian_6]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_a grain_a'
 []
 [p1_solid_response_hessian_7]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_a grain_b'
 []
 [p1_solid_response_hessian_8]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_a grain_c'
 []
 [p1_solid_response_hessian_9]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_a grain_d'
 []
 [p1_solid_response_hessian_10]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_b pore_state'
 []
 [p1_solid_response_hessian_11]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_b grain_a'
 []
 [p1_solid_response_hessian_12]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_b grain_b'
 []
 [p1_solid_response_hessian_13]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_b grain_c'
 []
 [p1_solid_response_hessian_14]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_b grain_d'
 []
 [p1_solid_response_hessian_15]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_c pore_state'
 []
 [p1_solid_response_hessian_16]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_c grain_a'
 []
 [p1_solid_response_hessian_17]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_c grain_b'
 []
 [p1_solid_response_hessian_18]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_c grain_c'
 []
 [p1_solid_response_hessian_19]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_c grain_d'
 []
 [p1_solid_response_hessian_20]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_d pore_state'
 []
 [p1_solid_response_hessian_21]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_d grain_a'
 []
 [p1_solid_response_hessian_22]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_d grain_b'
 []
 [p1_solid_response_hessian_23]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_d grain_c'
 []
 [p1_solid_response_hessian_24]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 2
  execute_on = INITIAL
  derivatives = 'grain_d grain_d'
 []
 [p1_void_number_density_0]
  type = ElementAverageMaterialProperty
  mat_prop = rhov
  block = 2
  execute_on = INITIAL
 []
 [p1_solid_number_density_0]
  type = ElementAverageMaterialProperty
  mat_prop = rhos
  block = 2
  execute_on = INITIAL
 []
 [p1_void_grand_potential_0]
  type = ElementAverageMaterialProperty
  mat_prop = omegav
  block = 2
  execute_on = INITIAL
 []
 [p1_solid_grand_potential_0]
  type = ElementAverageMaterialProperty
  mat_prop = omegas
  block = 2
  execute_on = INITIAL
 []
 [p2_void_minimum_0]
  type = ElementAverageMaterialProperty
  mat_prop = hv_c_min
  block = 3
  execute_on = INITIAL
 []
 [p2_void_minimum_gradient_0]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'pore_state'
 []
 [p2_void_minimum_gradient_1]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_a'
 []
 [p2_void_minimum_gradient_2]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_b'
 []
 [p2_void_minimum_gradient_3]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_c'
 []
 [p2_void_minimum_gradient_4]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_d'
 []
 [p2_void_minimum_hessian_0]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'pore_state pore_state'
 []
 [p2_void_minimum_hessian_1]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'pore_state grain_a'
 []
 [p2_void_minimum_hessian_2]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'pore_state grain_b'
 []
 [p2_void_minimum_hessian_3]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'pore_state grain_c'
 []
 [p2_void_minimum_hessian_4]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'pore_state grain_d'
 []
 [p2_void_minimum_hessian_5]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_a pore_state'
 []
 [p2_void_minimum_hessian_6]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_a grain_a'
 []
 [p2_void_minimum_hessian_7]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_a grain_b'
 []
 [p2_void_minimum_hessian_8]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_a grain_c'
 []
 [p2_void_minimum_hessian_9]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_a grain_d'
 []
 [p2_void_minimum_hessian_10]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_b pore_state'
 []
 [p2_void_minimum_hessian_11]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_b grain_a'
 []
 [p2_void_minimum_hessian_12]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_b grain_b'
 []
 [p2_void_minimum_hessian_13]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_b grain_c'
 []
 [p2_void_minimum_hessian_14]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_b grain_d'
 []
 [p2_void_minimum_hessian_15]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_c pore_state'
 []
 [p2_void_minimum_hessian_16]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_c grain_a'
 []
 [p2_void_minimum_hessian_17]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_c grain_b'
 []
 [p2_void_minimum_hessian_18]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_c grain_c'
 []
 [p2_void_minimum_hessian_19]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_c grain_d'
 []
 [p2_void_minimum_hessian_20]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_d pore_state'
 []
 [p2_void_minimum_hessian_21]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_d grain_a'
 []
 [p2_void_minimum_hessian_22]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_d grain_b'
 []
 [p2_void_minimum_hessian_23]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_d grain_c'
 []
 [p2_void_minimum_hessian_24]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_d grain_d'
 []
 [p2_solid_minimum_0]
  type = ElementAverageMaterialProperty
  mat_prop = hs_c_min
  block = 3
  execute_on = INITIAL
 []
 [p2_solid_minimum_gradient_0]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'pore_state'
 []
 [p2_solid_minimum_gradient_1]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_a'
 []
 [p2_solid_minimum_gradient_2]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_b'
 []
 [p2_solid_minimum_gradient_3]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_c'
 []
 [p2_solid_minimum_gradient_4]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_d'
 []
 [p2_solid_minimum_hessian_0]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'pore_state pore_state'
 []
 [p2_solid_minimum_hessian_1]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'pore_state grain_a'
 []
 [p2_solid_minimum_hessian_2]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'pore_state grain_b'
 []
 [p2_solid_minimum_hessian_3]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'pore_state grain_c'
 []
 [p2_solid_minimum_hessian_4]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'pore_state grain_d'
 []
 [p2_solid_minimum_hessian_5]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_a pore_state'
 []
 [p2_solid_minimum_hessian_6]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_a grain_a'
 []
 [p2_solid_minimum_hessian_7]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_a grain_b'
 []
 [p2_solid_minimum_hessian_8]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_a grain_c'
 []
 [p2_solid_minimum_hessian_9]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_a grain_d'
 []
 [p2_solid_minimum_hessian_10]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_b pore_state'
 []
 [p2_solid_minimum_hessian_11]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_b grain_a'
 []
 [p2_solid_minimum_hessian_12]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_b grain_b'
 []
 [p2_solid_minimum_hessian_13]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_b grain_c'
 []
 [p2_solid_minimum_hessian_14]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_b grain_d'
 []
 [p2_solid_minimum_hessian_15]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_c pore_state'
 []
 [p2_solid_minimum_hessian_16]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_c grain_a'
 []
 [p2_solid_minimum_hessian_17]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_c grain_b'
 []
 [p2_solid_minimum_hessian_18]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_c grain_c'
 []
 [p2_solid_minimum_hessian_19]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_c grain_d'
 []
 [p2_solid_minimum_hessian_20]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_d pore_state'
 []
 [p2_solid_minimum_hessian_21]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_d grain_a'
 []
 [p2_solid_minimum_hessian_22]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_d grain_b'
 []
 [p2_solid_minimum_hessian_23]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_d grain_c'
 []
 [p2_solid_minimum_hessian_24]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_d grain_d'
 []
 [p2_void_response_0]
  type = ElementAverageMaterialProperty
  mat_prop = hv_over_kVa
  block = 3
  execute_on = INITIAL
 []
 [p2_void_response_gradient_0]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'pore_state'
 []
 [p2_void_response_gradient_1]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_a'
 []
 [p2_void_response_gradient_2]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_b'
 []
 [p2_void_response_gradient_3]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_c'
 []
 [p2_void_response_gradient_4]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_d'
 []
 [p2_void_response_hessian_0]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'pore_state pore_state'
 []
 [p2_void_response_hessian_1]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'pore_state grain_a'
 []
 [p2_void_response_hessian_2]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'pore_state grain_b'
 []
 [p2_void_response_hessian_3]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'pore_state grain_c'
 []
 [p2_void_response_hessian_4]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'pore_state grain_d'
 []
 [p2_void_response_hessian_5]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_a pore_state'
 []
 [p2_void_response_hessian_6]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_a grain_a'
 []
 [p2_void_response_hessian_7]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_a grain_b'
 []
 [p2_void_response_hessian_8]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_a grain_c'
 []
 [p2_void_response_hessian_9]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_a grain_d'
 []
 [p2_void_response_hessian_10]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_b pore_state'
 []
 [p2_void_response_hessian_11]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_b grain_a'
 []
 [p2_void_response_hessian_12]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_b grain_b'
 []
 [p2_void_response_hessian_13]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_b grain_c'
 []
 [p2_void_response_hessian_14]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_b grain_d'
 []
 [p2_void_response_hessian_15]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_c pore_state'
 []
 [p2_void_response_hessian_16]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_c grain_a'
 []
 [p2_void_response_hessian_17]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_c grain_b'
 []
 [p2_void_response_hessian_18]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_c grain_c'
 []
 [p2_void_response_hessian_19]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_c grain_d'
 []
 [p2_void_response_hessian_20]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_d pore_state'
 []
 [p2_void_response_hessian_21]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_d grain_a'
 []
 [p2_void_response_hessian_22]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_d grain_b'
 []
 [p2_void_response_hessian_23]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_d grain_c'
 []
 [p2_void_response_hessian_24]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_d grain_d'
 []
 [p2_solid_response_0]
  type = ElementAverageMaterialProperty
  mat_prop = hs_over_kVa
  block = 3
  execute_on = INITIAL
 []
 [p2_solid_response_gradient_0]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'pore_state'
 []
 [p2_solid_response_gradient_1]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_a'
 []
 [p2_solid_response_gradient_2]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_b'
 []
 [p2_solid_response_gradient_3]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_c'
 []
 [p2_solid_response_gradient_4]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_d'
 []
 [p2_solid_response_hessian_0]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'pore_state pore_state'
 []
 [p2_solid_response_hessian_1]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'pore_state grain_a'
 []
 [p2_solid_response_hessian_2]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'pore_state grain_b'
 []
 [p2_solid_response_hessian_3]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'pore_state grain_c'
 []
 [p2_solid_response_hessian_4]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'pore_state grain_d'
 []
 [p2_solid_response_hessian_5]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_a pore_state'
 []
 [p2_solid_response_hessian_6]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_a grain_a'
 []
 [p2_solid_response_hessian_7]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_a grain_b'
 []
 [p2_solid_response_hessian_8]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_a grain_c'
 []
 [p2_solid_response_hessian_9]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_a grain_d'
 []
 [p2_solid_response_hessian_10]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_b pore_state'
 []
 [p2_solid_response_hessian_11]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_b grain_a'
 []
 [p2_solid_response_hessian_12]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_b grain_b'
 []
 [p2_solid_response_hessian_13]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_b grain_c'
 []
 [p2_solid_response_hessian_14]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_b grain_d'
 []
 [p2_solid_response_hessian_15]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_c pore_state'
 []
 [p2_solid_response_hessian_16]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_c grain_a'
 []
 [p2_solid_response_hessian_17]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_c grain_b'
 []
 [p2_solid_response_hessian_18]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_c grain_c'
 []
 [p2_solid_response_hessian_19]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_c grain_d'
 []
 [p2_solid_response_hessian_20]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_d pore_state'
 []
 [p2_solid_response_hessian_21]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_d grain_a'
 []
 [p2_solid_response_hessian_22]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_d grain_b'
 []
 [p2_solid_response_hessian_23]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_d grain_c'
 []
 [p2_solid_response_hessian_24]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 3
  execute_on = INITIAL
  derivatives = 'grain_d grain_d'
 []
 [p2_void_number_density_0]
  type = ElementAverageMaterialProperty
  mat_prop = rhov
  block = 3
  execute_on = INITIAL
 []
 [p2_solid_number_density_0]
  type = ElementAverageMaterialProperty
  mat_prop = rhos
  block = 3
  execute_on = INITIAL
 []
 [p2_void_grand_potential_0]
  type = ElementAverageMaterialProperty
  mat_prop = omegav
  block = 3
  execute_on = INITIAL
 []
 [p2_solid_grand_potential_0]
  type = ElementAverageMaterialProperty
  mat_prop = omegas
  block = 3
  execute_on = INITIAL
 []
 [p3_void_minimum_0]
  type = ElementAverageMaterialProperty
  mat_prop = hv_c_min
  block = 4
  execute_on = INITIAL
 []
 [p3_void_minimum_gradient_0]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'pore_state'
 []
 [p3_void_minimum_gradient_1]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_a'
 []
 [p3_void_minimum_gradient_2]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_b'
 []
 [p3_void_minimum_gradient_3]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_c'
 []
 [p3_void_minimum_gradient_4]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_d'
 []
 [p3_void_minimum_hessian_0]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'pore_state pore_state'
 []
 [p3_void_minimum_hessian_1]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'pore_state grain_a'
 []
 [p3_void_minimum_hessian_2]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'pore_state grain_b'
 []
 [p3_void_minimum_hessian_3]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'pore_state grain_c'
 []
 [p3_void_minimum_hessian_4]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'pore_state grain_d'
 []
 [p3_void_minimum_hessian_5]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_a pore_state'
 []
 [p3_void_minimum_hessian_6]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_a grain_a'
 []
 [p3_void_minimum_hessian_7]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_a grain_b'
 []
 [p3_void_minimum_hessian_8]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_a grain_c'
 []
 [p3_void_minimum_hessian_9]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_a grain_d'
 []
 [p3_void_minimum_hessian_10]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_b pore_state'
 []
 [p3_void_minimum_hessian_11]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_b grain_a'
 []
 [p3_void_minimum_hessian_12]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_b grain_b'
 []
 [p3_void_minimum_hessian_13]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_b grain_c'
 []
 [p3_void_minimum_hessian_14]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_b grain_d'
 []
 [p3_void_minimum_hessian_15]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_c pore_state'
 []
 [p3_void_minimum_hessian_16]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_c grain_a'
 []
 [p3_void_minimum_hessian_17]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_c grain_b'
 []
 [p3_void_minimum_hessian_18]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_c grain_c'
 []
 [p3_void_minimum_hessian_19]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_c grain_d'
 []
 [p3_void_minimum_hessian_20]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_d pore_state'
 []
 [p3_void_minimum_hessian_21]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_d grain_a'
 []
 [p3_void_minimum_hessian_22]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_d grain_b'
 []
 [p3_void_minimum_hessian_23]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_d grain_c'
 []
 [p3_void_minimum_hessian_24]
  type = RepairDerivativeAverage
  mat_prop = hv_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_d grain_d'
 []
 [p3_solid_minimum_0]
  type = ElementAverageMaterialProperty
  mat_prop = hs_c_min
  block = 4
  execute_on = INITIAL
 []
 [p3_solid_minimum_gradient_0]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'pore_state'
 []
 [p3_solid_minimum_gradient_1]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_a'
 []
 [p3_solid_minimum_gradient_2]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_b'
 []
 [p3_solid_minimum_gradient_3]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_c'
 []
 [p3_solid_minimum_gradient_4]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_d'
 []
 [p3_solid_minimum_hessian_0]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'pore_state pore_state'
 []
 [p3_solid_minimum_hessian_1]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'pore_state grain_a'
 []
 [p3_solid_minimum_hessian_2]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'pore_state grain_b'
 []
 [p3_solid_minimum_hessian_3]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'pore_state grain_c'
 []
 [p3_solid_minimum_hessian_4]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'pore_state grain_d'
 []
 [p3_solid_minimum_hessian_5]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_a pore_state'
 []
 [p3_solid_minimum_hessian_6]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_a grain_a'
 []
 [p3_solid_minimum_hessian_7]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_a grain_b'
 []
 [p3_solid_minimum_hessian_8]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_a grain_c'
 []
 [p3_solid_minimum_hessian_9]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_a grain_d'
 []
 [p3_solid_minimum_hessian_10]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_b pore_state'
 []
 [p3_solid_minimum_hessian_11]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_b grain_a'
 []
 [p3_solid_minimum_hessian_12]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_b grain_b'
 []
 [p3_solid_minimum_hessian_13]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_b grain_c'
 []
 [p3_solid_minimum_hessian_14]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_b grain_d'
 []
 [p3_solid_minimum_hessian_15]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_c pore_state'
 []
 [p3_solid_minimum_hessian_16]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_c grain_a'
 []
 [p3_solid_minimum_hessian_17]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_c grain_b'
 []
 [p3_solid_minimum_hessian_18]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_c grain_c'
 []
 [p3_solid_minimum_hessian_19]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_c grain_d'
 []
 [p3_solid_minimum_hessian_20]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_d pore_state'
 []
 [p3_solid_minimum_hessian_21]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_d grain_a'
 []
 [p3_solid_minimum_hessian_22]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_d grain_b'
 []
 [p3_solid_minimum_hessian_23]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_d grain_c'
 []
 [p3_solid_minimum_hessian_24]
  type = RepairDerivativeAverage
  mat_prop = hs_c_min
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_d grain_d'
 []
 [p3_void_response_0]
  type = ElementAverageMaterialProperty
  mat_prop = hv_over_kVa
  block = 4
  execute_on = INITIAL
 []
 [p3_void_response_gradient_0]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'pore_state'
 []
 [p3_void_response_gradient_1]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_a'
 []
 [p3_void_response_gradient_2]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_b'
 []
 [p3_void_response_gradient_3]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_c'
 []
 [p3_void_response_gradient_4]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_d'
 []
 [p3_void_response_hessian_0]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'pore_state pore_state'
 []
 [p3_void_response_hessian_1]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'pore_state grain_a'
 []
 [p3_void_response_hessian_2]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'pore_state grain_b'
 []
 [p3_void_response_hessian_3]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'pore_state grain_c'
 []
 [p3_void_response_hessian_4]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'pore_state grain_d'
 []
 [p3_void_response_hessian_5]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_a pore_state'
 []
 [p3_void_response_hessian_6]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_a grain_a'
 []
 [p3_void_response_hessian_7]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_a grain_b'
 []
 [p3_void_response_hessian_8]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_a grain_c'
 []
 [p3_void_response_hessian_9]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_a grain_d'
 []
 [p3_void_response_hessian_10]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_b pore_state'
 []
 [p3_void_response_hessian_11]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_b grain_a'
 []
 [p3_void_response_hessian_12]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_b grain_b'
 []
 [p3_void_response_hessian_13]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_b grain_c'
 []
 [p3_void_response_hessian_14]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_b grain_d'
 []
 [p3_void_response_hessian_15]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_c pore_state'
 []
 [p3_void_response_hessian_16]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_c grain_a'
 []
 [p3_void_response_hessian_17]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_c grain_b'
 []
 [p3_void_response_hessian_18]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_c grain_c'
 []
 [p3_void_response_hessian_19]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_c grain_d'
 []
 [p3_void_response_hessian_20]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_d pore_state'
 []
 [p3_void_response_hessian_21]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_d grain_a'
 []
 [p3_void_response_hessian_22]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_d grain_b'
 []
 [p3_void_response_hessian_23]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_d grain_c'
 []
 [p3_void_response_hessian_24]
  type = RepairDerivativeAverage
  mat_prop = hv_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_d grain_d'
 []
 [p3_solid_response_0]
  type = ElementAverageMaterialProperty
  mat_prop = hs_over_kVa
  block = 4
  execute_on = INITIAL
 []
 [p3_solid_response_gradient_0]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'pore_state'
 []
 [p3_solid_response_gradient_1]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_a'
 []
 [p3_solid_response_gradient_2]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_b'
 []
 [p3_solid_response_gradient_3]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_c'
 []
 [p3_solid_response_gradient_4]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_d'
 []
 [p3_solid_response_hessian_0]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'pore_state pore_state'
 []
 [p3_solid_response_hessian_1]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'pore_state grain_a'
 []
 [p3_solid_response_hessian_2]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'pore_state grain_b'
 []
 [p3_solid_response_hessian_3]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'pore_state grain_c'
 []
 [p3_solid_response_hessian_4]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'pore_state grain_d'
 []
 [p3_solid_response_hessian_5]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_a pore_state'
 []
 [p3_solid_response_hessian_6]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_a grain_a'
 []
 [p3_solid_response_hessian_7]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_a grain_b'
 []
 [p3_solid_response_hessian_8]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_a grain_c'
 []
 [p3_solid_response_hessian_9]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_a grain_d'
 []
 [p3_solid_response_hessian_10]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_b pore_state'
 []
 [p3_solid_response_hessian_11]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_b grain_a'
 []
 [p3_solid_response_hessian_12]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_b grain_b'
 []
 [p3_solid_response_hessian_13]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_b grain_c'
 []
 [p3_solid_response_hessian_14]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_b grain_d'
 []
 [p3_solid_response_hessian_15]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_c pore_state'
 []
 [p3_solid_response_hessian_16]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_c grain_a'
 []
 [p3_solid_response_hessian_17]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_c grain_b'
 []
 [p3_solid_response_hessian_18]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_c grain_c'
 []
 [p3_solid_response_hessian_19]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_c grain_d'
 []
 [p3_solid_response_hessian_20]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_d pore_state'
 []
 [p3_solid_response_hessian_21]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_d grain_a'
 []
 [p3_solid_response_hessian_22]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_d grain_b'
 []
 [p3_solid_response_hessian_23]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_d grain_c'
 []
 [p3_solid_response_hessian_24]
  type = RepairDerivativeAverage
  mat_prop = hs_over_kVa
  block = 4
  execute_on = INITIAL
  derivatives = 'grain_d grain_d'
 []
 [p3_void_number_density_0]
  type = ElementAverageMaterialProperty
  mat_prop = rhov
  block = 4
  execute_on = INITIAL
 []
 [p3_solid_number_density_0]
  type = ElementAverageMaterialProperty
  mat_prop = rhos
  block = 4
  execute_on = INITIAL
 []
 [p3_void_grand_potential_0]
  type = ElementAverageMaterialProperty
  mat_prop = omegav
  block = 4
  execute_on = INITIAL
 []
 [p3_solid_grand_potential_0]
  type = ElementAverageMaterialProperty
  mat_prop = omegas
  block = 4
  execute_on = INITIAL
 []
[]
[VectorPostprocessors]
 [dofs]
  type = RepairDofMap
  variables = 'pore_state grain_a grain_b grain_c grain_d mu_state fraction_state'
  execute_on = INITIAL
 []
[]
[Preconditioning]
 [full]
  type = SMP
  full = true
 []
[]
[Executioner]
 type = Steady
 solve_type = NEWTON
 automatic_scaling = false
[]
[Outputs]
 console = false
 file_base = result
 [csv]
  type = CSV
  precision = 17
  execute_on = INITIAL
 []
[]
